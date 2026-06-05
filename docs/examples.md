# Examples

## Run the bridge

Configure the call at the bottom of `twitch_bridge/__main__.py`:

```python
from twitch_bridge.__main__ import connect_twitch_to_hivemind

connect_twitch_to_hivemind(
    channel="your_channel",
    oauth="oauth:your_chat_token",
    tags=["@bot", "@jarbas"],
    host="wss://127.0.0.1",
    port=5678,
    key="your-access-key",
)
```

Then start it:

```bash
python -m twitch_bridge
```

## A conversation

In the channel's chat:

```
alice> @bot what time is it?
bot>   @alice , It is half past three.

alice> @bot set a timer for five minutes
bot>   @alice , Timer set for five minutes.
```

Chat lines without a trigger tag are ignored.

## Standalone Twitch echo bot

The `Twitch` IRC client can be used on its own, without HiveMind, to verify the channel and OAuth token. See `examples/echobot.py`:

```python
from twitch_bridge.twitch import Twitch

class EchoBot(Twitch):
    def on_message(self, username, message):
        self.send_message(message)

    def on_connect(self):
        self.send_message("I am EchoBot")

twitch = EchoBot("your_channel", "oauth:your_chat_token")
twitch.listen()
```

If the echo bot mirrors chat back, the Twitch half of the configuration is correct and you can move on to wiring the HiveMind half.
