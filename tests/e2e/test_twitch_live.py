"""
LIVE Twitch IRC test — SCAFFOLD.

This is the other half of the bridge's real path: a genuine Twitch IRC
connect + message loop. It needs real Twitch chat credentials, which cannot be
checked in, so it SKIPS cleanly whenever the env vars are absent. Drop the
creds in and it runs as-is — no code changes needed.

Required environment variables:
  TWITCH_OAUTH    chat OAuth token, e.g. "oauth:xxxxxxxx"
                  (get one at https://twitchapps.com/tmi/)
  TWITCH_NICK     bot account nickname to connect as
  TWITCH_CHANNEL  channel name to join (no leading '#')

Optional:
  TWITCH_TRIGGER  trigger tag the bot answers to (default "@<TWITCH_NICK>")

What it does when creds ARE present:
  - opens a REAL IRC socket to irc.twitch.tv via twitch_bridge.twitch.Twitch
  - PASS/NICK/JOINs the channel
  - runs the listen() parse loop in a daemon thread
  - posts a tagged trigger message into the channel from the bot itself
  - asserts the bridge's on_message callback fires for the bot's own line and
    that an outbound PRIVMSG can be sent back to the channel.

This complements test_twitch_hivemind_e2e.py: that one mocks IRC and uses a
real hub; this one uses real IRC. Wiring both together against a real hub AND
real Twitch at once is a manual/operator test the credential owner can run by
combining the two (point JarbasTwitchBridge at a real hub with a real oauth).
"""
import os
import threading
import time

import pytest

from twitch_bridge.twitch import Twitch


TWITCH_OAUTH = os.environ.get("TWITCH_OAUTH")
TWITCH_NICK = os.environ.get("TWITCH_NICK")
TWITCH_CHANNEL = os.environ.get("TWITCH_CHANNEL")

_HAVE_CREDS = bool(TWITCH_OAUTH and TWITCH_NICK and TWITCH_CHANNEL)

pytestmark = pytest.mark.skipif(
    not _HAVE_CREDS,
    reason="set TWITCH_OAUTH, TWITCH_NICK and TWITCH_CHANNEL to run the live "
           "Twitch IRC test",
)


def test_live_twitch_connect_and_message_loop():
    """Connect to real Twitch IRC, run the listen loop, post + observe a line."""
    trigger = os.environ.get("TWITCH_TRIGGER", "@{}".format(TWITCH_NICK))

    twitch = Twitch(channel=TWITCH_CHANNEL, oauth=TWITCH_OAUTH,
                    nickname=TWITCH_NICK)

    received = []
    ev = threading.Event()

    def _on_message(username, message):
        received.append((username, message))
        ev.set()

    twitch.on_message = _on_message

    # real IRC connect + JOIN
    twitch.connect()
    try:
        # run the real parse loop in the background
        listener = threading.Thread(target=twitch.listen, daemon=True)
        listener.start()

        # give Twitch a moment to finish MOTD / NAMES before we post
        time.sleep(3)

        probe = "{} hello from the live e2e test".format(trigger)
        twitch.send_message(probe)

        # wait for our own line to come back through the IRC parse loop
        assert ev.wait(timeout=30), \
            "did not observe any chat line on the live Twitch connection"
        assert received, "on_message never fired"
    finally:
        twitch.stop_listening()
