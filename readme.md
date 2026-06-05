# HiveMind Twitch Bridge

Relay a [Twitch](https://twitch.tv) channel's chat to a [HiveMind](https://github.com/JarbasHiveMind/HiveMind-core) hub.

The bridge is a HiveMind **satellite** whose input and output are Twitch IRC chat instead of a microphone. Chat messages that carry a trigger tag become utterances sent to the hub; the hub's spoken reply is echoed back into the channel, addressed to the user. Any HiveMind hub (and the OVOS skills behind it) becomes a Twitch chat bot.

```
Twitch chat (IRC)  ⇄  HiveMind-twitch-bridge  ⇄  HiveMind hub  ⇄  OVOS skills
```

![](./twitch.png)
![](./bridge.png)

## Prerequisites

- A running **HiveMind hub** ([hivemind-core](https://github.com/JarbasHiveMind/HiveMind-core)) reachable over the network, and a **HiveMind access key** for this bridge (`hivemind-core add-client`).
- A **Twitch account** for the bot and a chat **OAuth token** for it. Generate one at <https://twitchapps.com/tmi/> (the token has the form `oauth:...`).
- The **channel name** whose chat the bot should join.

## Install

This repo has no published package. Install the runtime dependency and run from a checkout:

```bash
git clone https://github.com/JarbasHiveMind/HiveMind-twitch-bridge
cd HiveMind-twitch-bridge
pip install -r requirements.txt
```

Dependency: `jarbas_hive_mind>=0.8.0` (pulls in `ovos_utils`).

## Quickstart

**1. Register the bridge on the hub** (where `hivemind-core` is installed):

```bash
hivemind-core add-client --name twitch-bridge \
  --access-key "your-access-key" --password "your-password"
```

**2. Configure the bridge.** The entry point is `connect_twitch_to_hivemind(...)` in `twitch_bridge/__main__.py`. Edit the call at the bottom of that file:

```python
from twitch_bridge.__main__ import connect_twitch_to_hivemind

connect_twitch_to_hivemind(
    channel="your_channel",                  # Twitch channel to join
    oauth="oauth:your_chat_token",           # Twitch chat OAuth token
    tags=["@bot", "@jarbas"],                # trigger tags
    host="wss://127.0.0.1",                  # HiveMind hub host
    port=5678,                               # HiveMind hub port
    key="your-access-key",                   # HiveMind access key
)
```

**3. Run it:**

```bash
python -m twitch_bridge
```

**4. Send a message.** In the channel's chat, include a trigger tag:

```
@bot what time is it?
```

The bridge strips the tag, forwards the message to the hub, and posts the reply back to the channel as `@user , <answer>`.

## Configuration

`connect_twitch_to_hivemind(...)` parameters:

| Parameter | Description | Default |
| --- | --- | --- |
| `channel` | Twitch channel name to join | — |
| `oauth` | Twitch chat OAuth token (`oauth:...`) | — |
| `tags` | Trigger tags; a chat message containing one is forwarded | `["@bot"]` |
| `host` | HiveMind hub host (`wss://` / `ws://`) | `wss://127.0.0.1` |
| `port` | HiveMind hub port | `5678` |
| `key` | HiveMind access key | `dummy_key` |
| `crypto_key` | Optional HiveMind payload crypto key | `None` |

## Troubleshooting

- **Bot never answers** — confirm the chat message contains a trigger tag; tags are matched case-insensitively and stripped before forwarding.
- **Cannot connect to Twitch** — verify the OAuth token is current (regenerate at <https://twitchapps.com/tmi/>) and the channel name is spelled correctly.
- **No reply posted** — confirm the hub is reachable and the access key is registered (`hivemind-core list-clients`), and that the hub produces a `speak` for the answer.

## Documentation

See [`docs/`](docs/) for a full setup walkthrough, a configuration reference, and worked examples.
