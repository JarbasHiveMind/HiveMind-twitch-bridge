# HiveMind Twitch Bridge

This bridge relays a [Twitch](https://twitch.tv) channel's chat to a [HiveMind](https://github.com/JarbasHiveMind/HiveMind-core) hub.

The bridge is a HiveMind **satellite**. Its input and output are Twitch IRC chat instead of a microphone. A chat message that carries a trigger tag becomes an utterance sent to the hub. The hub's spoken reply is echoed back into the channel, addressed to the user. Any HiveMind hub, and the OVOS skills behind it, becomes a Twitch chat bot.

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

This installs the `hivemind-twitch-bridge` console entry point. Runtime dependencies: `hivemind-bus-client`, `ovos-bus-client`, `ovos-utils`.

## Quickstart

**1. Register the bridge on the hub** (where `hivemind-core` is installed):

```bash
hivemind-core add-client --name twitch-bridge \
  --access-key "your-access-key" --password "your-password"
```

**2. Run it.** The bridge connects to the hub as a satellite and joins the Twitch channel:

```bash
hivemind-twitch-bridge \
  --channel your_channel \
  --oauth oauth:your_chat_token \
  --tag @bot --tag @jarbas \
  --host wss://127.0.0.1 --port 5678 \
  --access-key your-access-key --password your-password
```

You can also call `connect_twitch_to_hivemind(...)` from `twitch_bridge.__main__` directly in Python.

**3. Send a message.** In the channel's chat, include a trigger tag:

```
@bot what time is it?
```

The bridge strips the tag, forwards the message to the hub, and posts the reply back to the channel as `@user , <answer>`.

## Configuration

`hivemind-twitch-bridge` / `connect_twitch_to_hivemind(...)` options:

| Option | Description | Default |
| --- | --- | --- |
| `--channel` | Twitch channel name to join | none |
| `--oauth` | Twitch chat OAuth token (`oauth:...`) | none |
| `--tag` | Trigger tag (repeatable). A chat message containing one is forwarded | `@bot` |
| `--nickname` | Twitch bot nickname | `bot` |
| `--lang` | Utterance language | `en-us` |
| `--host` | HiveMind hub host (`wss://` / `ws://`) | `wss://127.0.0.1` |
| `--port` | HiveMind hub port | `5678` |
| `--access-key` | HiveMind access key | `None` |
| `--password` | HiveMind password | `None` |
| `--crypto-key` | Optional HiveMind payload crypto key | `None` |
| `--self-signed` | Accept self-signed SSL certificates | off |

See [docs/configuration.md](docs/configuration.md) for the full parameter reference.

## Troubleshooting

- **Bot never answers**: confirm the chat message contains a trigger tag. Tags are matched case-insensitively and stripped before forwarding.
- **Cannot connect to Twitch**: verify the OAuth token is current (regenerate at <https://twitchapps.com/tmi/>) and the channel name is spelled correctly.
- **No reply posted**: confirm the hub is reachable and the access key is registered (`hivemind-core list-clients`), and that the hub produces a `speak` for the answer. The single most common cause is a missing `allow-msg` whitelist — a freshly added client is denied every message type by default; see [operator-setup.md](docs/operator-setup.md#whitelist-the-messages-the-bridge-sends).
- **"invalid api key" on connect**: the bridge's `hivemind-bus-client` is too old for the hub's protocol version. Update it (`pip install -U hivemind-bus-client`).
- **Hub rejects the connection after it was reinstalled or its identity changed**: the client pins the hub's Noise public key on first connect and refuses a hub presenting a different one. Run `hivemind-client reset-noise-pin` and reconnect.

## Documentation

- **[Setup walkthrough](docs/setup.md)**: from nothing to a working bot, step by step.
- **[Operator setup](docs/operator-setup.md)**: getting the bot's Twitch account and chat OAuth token, registering the bridge on a HiveMind hub, the run command, security notes, and live-test environment variables.
- **[Configuration reference](docs/configuration.md)**: every credential and parameter the bridge accepts.
- **[Examples](docs/examples.md)**: a worked conversation and a standalone Twitch echo bot for testing credentials.

## Related projects

- [HiveMind-core](https://github.com/JarbasHiveMind/HiveMind-core): the HiveMind hub this bridge connects to.
- [hivemind-websocket-client](https://github.com/JarbasHiveMind/hivemind-websocket-client): the client library the bridge uses to talk to the hub.

## License

See [LICENSE](LICENSE).
