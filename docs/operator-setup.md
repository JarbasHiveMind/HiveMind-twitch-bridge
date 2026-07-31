# Operator setup: running the Twitch bridge

This bridge logs a bot into **Twitch chat (IRC)** and relays each tagged message
to and from a HiveMind hub, so any HiveMind hub, and the OVOS skills behind it,
can answer in a Twitch channel. As an operator you need **a Twitch account for
the bot** with a **chat OAuth token**, a **channel** to join, and a HiveMind hub
to point it at.

```
Twitch user  ⇄  Twitch chat (IRC)  ⇄  hivemind-twitch-bridge  ⇄  HiveMind hub  ⇄  OVOS skills
```

Twitch is a hosted service. It is **not self-hostable**. The no-cost path is a
throwaway Twitch account used only for the bot.

## 1. Get the bot a Twitch account and chat token

1. **Create a Twitch account** for the bot at <https://twitch.tv> (a throwaway
   account is fine. Its own channel is a good channel to join).
2. **Generate a chat OAuth token** for that account. The token has the form
   `oauth:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` and needs the scopes **`chat:read`**
   and **`chat:edit`** (read and post in chat). Get one from:
   - the quick generator at <https://twitchtokengenerator.com> (or
     <https://twitchapps.com/tmi/>), logged in **as the bot account**, or
   - the [Twitch developer console](https://dev.twitch.tv/console): register an
     app and run the OAuth flow for the `chat:read chat:edit` scopes.
3. Note three values:
   - the **OAuth token** (`oauth:…`),
   - the **bot username / nick** (the account name),
   - the **channel** to join (no leading `#`. The bot account's own channel
     works).

## 2. Prerequisites

- The bot's **OAuth token**, **nick**, and target **channel** (from step 1).
- A running **HiveMind hub** (`hivemind-core`) you can reach.
- Python 3.10+. Runtime dependencies: `hivemind-bus-client`, `ovos-bus-client`,
  `ovos-utils`.

## 3. Register the bridge on the hub

On the hub, create a client credential for this bridge:

```bash
hivemind-core add-client          # prints an ACCESS KEY and a PASSWORD
```

Note the **access key**, **password**, and the hub **host** and **port**
(default WebSocket port `5678`). The bridge connects as a HiveMind *satellite*
with these values.

## 4. Install and run the bridge

```bash
pip install .          # provides the `hivemind-twitch-bridge` command

hivemind-twitch-bridge \
  --channel  your_channel \
  --oauth    "oauth:your_chat_token" \
  --nickname your_bot_nick \
  --tag @bot \
  --access-key "your-access-key" \
  --password   "your-hivemind-password" \
  --host wss://your-hub-host \
  --port 5678
```

Useful flags (verify with `hivemind-twitch-bridge --help`):

| Flag | Meaning | Default |
| --- | --- | --- |
| `--channel` | Twitch channel to join (required) | none |
| `--oauth` | chat OAuth token `oauth:…` (required) | none |
| `--nickname` | bot nickname to connect as | `bot` |
| `--tag` | trigger tag, repeatable | `@bot` |
| `--lang` | utterance language | `en-us` |
| `--access-key` / `--password` | HiveMind credentials | `None` |
| `--host` / `--port` | HiveMind hub (`ws://`/`wss://`) | `wss://127.0.0.1` / `5678` |
| `--crypto-key` | optional payload crypto key | `None` |
| `--self-signed` | accept self-signed TLS | off |

## 5. Talk to it

In the channel's chat, prefix a message with a trigger tag:

```
@bot what time is it?
```

The bridge strips the tag, forwards the message to the hub as a
`recognizer_loop:utterance`, and posts the hub's spoken reply back to the
channel as `@user , <answer>`.

## Security notes

- The **OAuth token** and the **HiveMind password** are secrets. Pass them
  through environment variables or a secrets manager, never in shell history or
  a committed file. If a token leaks, revoke it from the token generator or
  Twitch settings and issue a new one.
- Anyone in the channel who knows the trigger tag can reach the hub. Restrict
  access at the hub with client ACLs or `allowed_types`.

## Testing (live e2e)

`tests/e2e/test_twitch_live.py` opens a **real** Twitch IRC connection when you
provide credentials through environment variables. It skips cleanly when they
are absent (the mocked HiveMind-side e2e test always runs):

```bash
export TWITCH_OAUTH="oauth:your_chat_token"
export TWITCH_NICK="your_bot_nick"
export TWITCH_CHANNEL="your_channel"      # no leading '#'
# optional: trigger tag the bot answers to (default "@$TWITCH_NICK")
export TWITCH_TRIGGER="@bot"
pytest tests/e2e/test_twitch_live.py
```

---
[← Setup](setup.md) · [Home](../readme.md) · [Configuration →](configuration.md)
