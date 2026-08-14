from hivemind_bus_client import HiveMessageBusClient
from ovos_bus_client import Message
from ovos_utils import create_daemon
from ovos_utils.log import LOG

from twitch_bridge.twitch import Twitch

platform = "JarbasTwitchBridgeV0.3"

DEFAULT_HANDSHAKE_MAX_RETRIES = 10


class JarbasTwitchBridge:
    """Relay a Twitch channel's chat to/from a HiveMind hub.

    The bridge connects to a HiveMind hub as a satellite using
    ``HiveMessageBusClient``. Twitch chat messages containing a trigger tag are
    forwarded to the hub as ``recognizer_loop:utterance`` and the hub's spoken
    reply is echoed back into the channel, addressed to the user that asked.
    """

    def __init__(self, channel, oauth, tags=None,
                 access_key=None,
                 host="wss://127.0.0.1",
                 port=5678,
                 password=None,
                 crypto_key=None,
                 self_signed=False,
                 lang="en-us",
                 nickname="bot",
                 bus=None,
                 handshake_max_retries=DEFAULT_HANDSHAKE_MAX_RETRIES):
        self.channel = channel
        self.oauth = oauth
        self.tags = tags or ["@bot"]
        self.lang = lang
        self.handshake_max_retries = handshake_max_retries

        self.twitch = Twitch(self.channel, self.oauth, nickname=nickname)
        self.twitch.on_message = self.on_twitch_message

        if bus:
            # got a connection already
            self.bus = bus
        else:
            # connect to hivemind
            self.bus = HiveMessageBusClient(access_key,
                                            host=host,
                                            port=port,
                                            password=password,
                                            crypto_key=crypto_key,
                                            self_signed=self_signed,
                                            useragent=platform)
            self.bus.connect(handshake_max_retries=self.handshake_max_retries)

        self.bus.on_mycroft("speak", self.handle_speak)
        self.bus.on_mycroft("hive.complete_intent_failure",
                            self.handle_complete_intent_failure)

    def start(self):
        """Start listening to the Twitch channel in a background daemon."""
        LOG.info("Twitch Channel: {0}".format(self.channel))
        create_daemon(self.twitch.listen)

    def stop(self):
        """Stop listening to the Twitch channel."""
        self.twitch.stop_listening()

    # twitch -> hivemind
    def on_twitch_message(self, username, message):
        utterance = message.lower().strip()
        should_answer = False
        for tag in self.tags:
            if tag.lower() in utterance:
                should_answer = True
                utterance = utterance.replace(tag.lower(), "")
        if should_answer:
            utterance = utterance.strip()
            LOG.debug("Twitch utterance from {0}: {1}".format(username,
                                                              utterance))
            self.bus.emit(Message("recognizer_loop:utterance",
                                  {"utterances": [utterance],
                                   "lang": self.lang},
                                  {"destination": "HiveMind",
                                   "platform": platform,
                                   "user": {"twitch_username": username}}))

    # hivemind -> twitch
    def speak(self, utterance, user_data):
        user = user_data["twitch_username"]
        utterance = "@{} , ".format(user) + utterance
        LOG.debug("Message: " + utterance)
        self.twitch.send_message(utterance)

    def handle_speak(self, message):
        user_data = message.context.get("user")
        if user_data and "twitch_username" in user_data:
            utterance = message.data["utterance"]
            self.speak(utterance, user_data)

    def handle_complete_intent_failure(self, message):
        user_data = message.context.get("user")
        if user_data and "twitch_username" in user_data:
            LOG.error("complete intent failure")
            self.speak("I don't know how to answer that", user_data)
