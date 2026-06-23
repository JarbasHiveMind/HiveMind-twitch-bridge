from unittest.mock import MagicMock


def test_version():
    from twitch_bridge.version import __version__
    assert isinstance(__version__, str)
    assert __version__[0].isdigit()


def test_import_package():
    import twitch_bridge
    from twitch_bridge import JarbasTwitchBridge, platform
    from twitch_bridge.twitch import Twitch
    assert platform.startswith("JarbasTwitchBridge")
    assert JarbasTwitchBridge is not None
    assert Twitch is not None


def test_construct_without_connecting():
    """Construct the bridge with an injected fake bus, no live Twitch/HiveMind."""
    from twitch_bridge import JarbasTwitchBridge

    fake_bus = MagicMock()
    bridge = JarbasTwitchBridge(channel="testchannel",
                                oauth="oauth:dummy",
                                tags=["@bot"],
                                bus=fake_bus)

    # the bridge registered its hivemind handlers on the injected bus
    registered = {c.args[0] for c in fake_bus.on_mycroft.call_args_list}
    assert "speak" in registered
    assert "hive.complete_intent_failure" in registered

    # the twitch client was created but never connected
    assert bridge.twitch.channel == "testchannel"
    assert bridge.twitch._connected is False
    assert bridge.twitch._running is False


def test_tagged_message_forwarded_to_hivemind():
    """A tagged chat message is emitted to the bus; an untagged one is not."""
    from twitch_bridge import JarbasTwitchBridge

    fake_bus = MagicMock()
    bridge = JarbasTwitchBridge(channel="c", oauth="oauth:dummy",
                                tags=["@bot"], bus=fake_bus)

    bridge.on_twitch_message("alice", "@bot what time is it")
    assert fake_bus.emit.called
    msg = fake_bus.emit.call_args.args[0]
    assert msg.msg_type == "recognizer_loop:utterance"
    assert msg.data["utterances"] == ["what time is it"]
    assert msg.context["user"]["twitch_username"] == "alice"

    fake_bus.emit.reset_mock()
    bridge.on_twitch_message("bob", "no tag here")
    assert not fake_bus.emit.called


def test_speak_routed_back_to_twitch():
    """A speak carrying the twitch user context is echoed back to chat."""
    from ovos_bus_client import Message
    from twitch_bridge import JarbasTwitchBridge

    fake_bus = MagicMock()
    bridge = JarbasTwitchBridge(channel="c", oauth="oauth:dummy",
                                tags=["@bot"], bus=fake_bus)
    bridge.twitch.send_message = MagicMock()

    bridge.handle_speak(Message("speak", {"utterance": "it is noon"},
                                {"user": {"twitch_username": "alice"}}))
    bridge.twitch.send_message.assert_called_once()
    sent = bridge.twitch.send_message.call_args.args[0]
    assert "alice" in sent
    assert "it is noon" in sent

    # a speak without twitch context is ignored
    bridge.twitch.send_message.reset_mock()
    bridge.handle_speak(Message("speak", {"utterance": "ignored"}, {}))
    bridge.twitch.send_message.assert_not_called()
