"""The bridge connects with its own identity (HIVEMIND-CRYPTO-1 §2)."""
from unittest.mock import MagicMock, patch

import twitch_bridge
from twitch_bridge import JarbasTwitchBridge


def _build(**kwargs):
    with patch.object(twitch_bridge, "Twitch"):
        JarbasTwitchBridge("channel", "oauth", access_key="k", password="p", **kwargs)


def test_the_bridge_builds_its_client_with_its_own_identity():
    identity = MagicMock()
    with patch.object(twitch_bridge, "NodeIdentity", return_value=identity) as ctor, \
         patch.object(twitch_bridge, "HiveMessageBusClient") as client:
        _build()
    ctor.assert_called_once_with(app_name="twitch-bridge")
    assert client.call_args.kwargs["identity"] is identity


def test_a_given_identity_is_used_as_is():
    identity = MagicMock()
    with patch.object(twitch_bridge, "NodeIdentity") as ctor, \
         patch.object(twitch_bridge, "HiveMessageBusClient") as client:
        _build(identity=identity)
    ctor.assert_not_called()
    assert client.call_args.kwargs["identity"] is identity
