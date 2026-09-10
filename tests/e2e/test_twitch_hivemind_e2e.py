"""
REAL end-to-end test: Twitch bridge <-> a live hivemind-core hub.

This exercises the bridge's *production* HiveMind code path against a *real*
hivemind-core hub (booted in-process by hivescope over a real localhost
WebSocket via ``add_master(..., use_loopback=True)``). Only the Twitch IRC side
is mocked — the bridge's ``twitch_bridge.twitch.Twitch`` wraps a stdlib socket
IRC client, so we replace its socket with a fake to (a) inject an inbound chat
line and (b) capture the bridge's outbound IRC ``PRIVMSG``.

Round-trip proven:

    inbound Twitch chat ("@bot what is the weather")
      -> bridge.on_twitch_message
      -> recognizer_loop:utterance (REAL HiveMessageBusClient -> hub)
      -> hub agent bus handler emits `speak` (destination = originating peer,
         echoing the twitch_username context)
      -> hivemind-core reverse-routes the speak BUS message to the satellite
      -> bridge.handle_speak (on_mycroft("speak"))
      -> bridge.twitch.send_message -> outbound IRC PRIVMSG to #channel,
         addressed to the asking user.

The bridge's REAL HiveMind path is the bus client + handshake + ACL admission +
reverse routing. Nothing on the HiveMind side is mocked.

References:
  - hivemind-test-harness/tests/test_hivemind_bus_client_e2e.py
    (loopback hub + HiveMessageBusClient + register_satellite/allowed_types)
  - hivemind-test-harness/tests/test_cascade.py
    (agent responder on master.agent_protocol.bus)
"""
import threading
import time

import pytest
from ovos_bus_client.message import Message

from hivemind_bus_client.client import HiveMessageBusClient
from hivemind_bus_client.identity import NodeIdentity
from hivescope.topology import TopologyBuilder

from twitch_bridge import JarbasTwitchBridge


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _extract_host_port(url: str):
    """Extract (host, port) from ``ws://127.0.0.1:PORT/``."""
    parts = url.replace("ws://", "").replace("wss://", "").rstrip("/").split(":")
    return parts[0], int(parts[1])


def _make_client(url: str, key: str, password: str,
                 name: str = "twitch-bridge") -> HiveMessageBusClient:
    """A REAL HiveMessageBusClient pointed at the loopback hub.

    Mirrors hivemind-test-harness's e2e helper: this is the exact client the
    bridge uses in production (``twitch_bridge.JarbasTwitchBridge`` builds the
    same class internally); here we build it explicitly so we can aim it at the
    ephemeral loopback port and inject it via ``bus=``.
    """
    host, port = _extract_host_port(url)
    identity = NodeIdentity()
    identity.access_key = key
    identity.password = password
    identity.default_master = f"ws://{host}"
    identity.default_port = port
    identity.name = name
    identity.site_id = f"{name}-site"
    return HiveMessageBusClient(
        key=key,
        password=password,
        host=f"ws://{host}",
        port=port,
        useragent=name,
        self_signed=False,
        identity=identity,
    )


class _FakeIRCSocket:
    """Stand-in for the stdlib socket inside ``twitch_bridge.twitch.Twitch``.

    Captures every ``.send()`` (so we can read back the outbound IRC PRIVMSG)
    and no-ops connect/close. We never let the bridge's real IRC ``listen()``
    loop run — instead the test drives inbound chat by calling the bridge's
    ``on_twitch_message`` directly, which is exactly what ``Twitch.listen()``
    does for each parsed line. This keeps the mock explicit (no importorskip).
    """

    def __init__(self):
        self.sent = []

    def connect(self, *a, **k):
        return None

    def send(self, data):
        self.sent.append(data)
        return len(data)

    def close(self, *a, **k):
        return None

    def recv(self, *a, **k):
        # never used: the test injects inbound chat via on_twitch_message
        return b""


def _setup_twitch_responder_agent(master, answer: str = "it is sunny"):
    """Register a handler on the hub's REAL agent bus that answers utterances.

    The injected utterance arrives on the agent bus with
    ``context["peer"]``/``context["source"]`` == the originating satellite peer
    (set by hivemind-core ``handle_inject_agent_msg``) and the bridge's
    ``context["user"]`` (twitch_username) preserved. To get the reply routed
    back to *that* satellite, we emit ``speak`` with
    ``context["destination"] = [peer]`` and echo the ``user`` context — which is
    what makes the bridge able to address the right Twitch user. hivescope's
    ``TestAgentProtocol.handle_internal_mycroft`` then reverse-routes it (exact
    port of ovos-bus-client ``OVOSProtocol``).
    """
    bus = master.agent_protocol.bus

    def _responder(msg: Message):
        peer = msg.context.get("peer") or msg.context.get("source")
        user = msg.context.get("user")
        bus.emit(Message(
            "speak",
            {"utterance": answer},
            {"destination": [peer], "user": user, "source": "skills"},
        ))

    bus.on("recognizer_loop:utterance", _responder)


# --------------------------------------------------------------------------- #
# the e2e test
# --------------------------------------------------------------------------- #
def test_twitch_roundtrip_through_real_hivemind_hub():
    """Full inbound-chat -> hub -> outbound-chat round-trip over a real hub."""
    key, password = "twitch-e2e-key", "twitch-e2e-pwd"
    channel, asking_user = "mychannel", "alice"

    b = TopologyBuilder()
    m = b.add_master("M0", use_loopback=True)
    # whitelist-only ACL: the bridge only ever injects this type.
    m.register_satellite(key, password=password,
                         allowed_types=["recognizer_loop:utterance"])
    b.start_all()

    bridge = None
    client = None
    try:
        # --- REAL bus client -> the live hub -------------------------------
        client = _make_client(m.network_protocol.url, key, password)
        client.connect(site_id="twitch-e2e-site")
        client.wait_for_handshake(timeout=10)
        assert client.handshake_event.is_set(), "handshake did not complete"

        # ensure the encrypted HELLO registered the peer on the hub
        deadline = time.time() + 5
        while not m.connected_peers() and time.time() < deadline:
            time.sleep(0.1)
        assert len(m.connected_peers()) == 1, \
            f"bridge did not register on hub: {m.connected_peers()}"

        # --- REAL bridge, MOCKED Twitch IRC side ---------------------------
        bridge = JarbasTwitchBridge(channel=channel, oauth="oauth:dummy",
                                    tags=["@bot"], bus=client)
        fake_irc = _FakeIRCSocket()
        bridge.twitch._socket = fake_irc
        bridge.twitch._connected = True  # pretend IRC is already joined

        # capture the bridge's outbound PRIVMSG the moment it fires
        outbound = []
        ev = threading.Event()
        _orig_send = bridge.twitch.send_message

        def _capturing_send(text):
            outbound.append(text)
            ev.set()
            return _orig_send(text)

        bridge.twitch.send_message = _capturing_send

        # --- hub-side responder on the REAL agent bus ----------------------
        _setup_twitch_responder_agent(m, answer="it is sunny")

        # --- drive the round-trip: simulate one inbound Twitch chat line ---
        # This is exactly the callback Twitch.listen() invokes per parsed line.
        bridge.on_twitch_message(asking_user, "@bot what is the weather")

        # --- assert the reply came all the way back out to Twitch ----------
        assert ev.wait(timeout=10), \
            "bridge never produced an outbound Twitch message"
        time.sleep(0.2)  # let any duplicate settle

        assert len(outbound) >= 1, "expected an outbound Twitch PRIVMSG"
        reply = outbound[0]
        assert "it is sunny" in reply, f"reply text missing: {reply!r}"
        assert asking_user in reply, \
            f"reply not addressed to asking user: {reply!r}"

        # and that it actually hit the (mocked) IRC socket as a real PRIVMSG,
        # routed to the right channel
        raw = b"".join(fake_irc.sent)
        assert b"PRIVMSG #" + channel.encode() in raw, \
            f"no PRIVMSG to #{channel} on the wire: {raw!r}"
        assert b"it is sunny" in raw, f"reply not on the wire: {raw!r}"
        assert asking_user.encode() in raw, \
            f"asking user not on the wire: {raw!r}"

        # and that the hub actually saw the utterance (REAL inject path)
        m.agent_protocol.assert_injected("recognizer_loop:utterance", count=1)
    finally:
        if bridge is not None:
            try:
                bridge.stop()
            except Exception:
                pass
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
        b.stop_all()


def test_untagged_chat_does_not_reach_hub():
    """A chat line without the trigger tag must NOT be forwarded to the hub."""
    key, password = "twitch-e2e-key2", "twitch-e2e-pwd2"

    b = TopologyBuilder()
    m = b.add_master("M0", use_loopback=True)
    m.register_satellite(key, password=password,
                         allowed_types=["recognizer_loop:utterance"])
    b.start_all()

    bridge = None
    client = None
    try:
        client = _make_client(m.network_protocol.url, key, password)
        client.connect(site_id="twitch-e2e-site2")
        client.wait_for_handshake(timeout=10)

        bridge = JarbasTwitchBridge(channel="c", oauth="oauth:dummy",
                                    tags=["@bot"], bus=client)
        bridge.twitch._socket = _FakeIRCSocket()
        bridge.twitch._connected = True

        bridge.on_twitch_message("bob", "just chatting, no tag")
        time.sleep(1)

        m.agent_protocol.assert_injected("recognizer_loop:utterance", count=0)
    finally:
        if bridge is not None:
            try:
                bridge.stop()
            except Exception:
                pass
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
        b.stop_all()
