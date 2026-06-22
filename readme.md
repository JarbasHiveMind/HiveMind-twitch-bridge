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

Install from a checkout:

```bash
git clone https://github.com/JarbasHiveMind/HiveMind-twitch-bridge
cd HiveMind-twitch-bridge
pip install .
```

This installs the `hivemind-twitch-bridge` console entry point. Runtime
dependencies: `hivemind-bus-client`, `ovos-bus-client`, `ovos-utils`.

## Quickstart

**1. Register the bridge on the hub** (where `hivemind-core` is installed):

```bash
hivemind-core add-client --name twitch-bridge \
  --access-key "your-access-key" --password "your-password"
```

**2. Run it.** The bridge connects to the hub as a satellite and joins the
Twitch channel:

```bash
hivemind-twitch-bridge \
  --channel your_channel \
  --oauth oauth:your_chat_token \
  --tag @bot --tag @jarbas \
  --host wss://127.0.0.1 --port 5678 \
  --access-key your-access-key --password your-password
```

You can also call `connect_twitch_to_hivemind(...)` from
`twitch_bridge.__main__` directly in Python.

**3. Send a message.** In the channel's chat, include a trigger tag:

```
@bot what time is it?
```

The bridge strips the tag, forwards the message to the hub, and posts the reply back to the channel as `@user , <answer>`.

## Configuration

`hivemind-twitch-bridge` / `connect_twitch_to_hivemind(...)` options:

| Option | Description | Default |
| --- | --- | --- |
| `--channel` | Twitch channel name to join | — |
| `--oauth` | Twitch chat OAuth token (`oauth:...`) | — |
| `--tag` | Trigger tag (repeatable); a chat message containing one is forwarded | `@bot` |
| `--nickname` | Twitch bot nickname | `bot` |
| `--lang` | Utterance language | `en-us` |
| `--host` | HiveMind hub host (`wss://` / `ws://`) | `wss://127.0.0.1` |
| `--port` | HiveMind hub port | `5678` |
| `--access-key` | HiveMind access key | `None` |
| `--password` | HiveMind password | `None` |
| `--crypto-key` | Optional HiveMind payload crypto key | `None` |
| `--self-signed` | Accept self-signed SSL certificates | off |

## Troubleshooting

- **Bot never answers** — confirm the chat message contains a trigger tag; tags are matched case-insensitively and stripped before forwarding.
- **Cannot connect to Twitch** — verify the OAuth token is current (regenerate at <https://twitchapps.com/tmi/>) and the channel name is spelled correctly.
- **No reply posted** — confirm the hub is reachable and the access key is registered (`hivemind-core list-clients`), and that the hub produces a `speak` for the answer.

## Documentation

See [`docs/`](docs/) for a full setup walkthrough, a configuration reference, and worked examples.
