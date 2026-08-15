# Configuration and Credentials Reference

The bridge needs Twitch chat credentials and a HiveMind access key. Both are
passed as arguments to `connect_twitch_to_hivemind(...)` in
`twitch_bridge/__main__.py`.

## Twitch credentials

| Parameter | Meaning |
| --- | --- |
| `channel` | The Twitch channel name whose chat the bot joins. |
| `oauth` | A Twitch chat OAuth token (`oauth:...`), generated at <https://twitchapps.com/tmi/>. |
| `tags` | List of trigger tags. A chat message that contains any tag (matched case-insensitively) is forwarded. The tag is stripped first. Default `["@bot"]`. |

The bot connects to Twitch IRC at `irc.twitch.tv:6667` and authenticates with
the token.

## HiveMind credentials

| Parameter | Meaning | Default |
| --- | --- | --- |
| `host` | HiveMind hub host (`wss://` or `ws://`). | `wss://127.0.0.1` |
| `port` | HiveMind hub port. | `5678` |
| `key` | HiveMind access key from `hivemind-core add-client`. | `dummy_key` |
| `crypto_key` | Optional pre-shared payload crypto key. | `None` |
| `name` | Terminal name reported to the hub. | `JarbasTwitchBridge` |

## Reply routing

When the bridge forwards a message it tags the HiveMind context with
`user.twitch_username`. The hub echoes it on the `speak` reply, and the bridge
posts the answer to the channel prefixed with `@username`.

The bridge also handles `hive.complete_intent_failure` from the hub, replying
with a fixed "I don't know how to answer that" message.

## Trigger and dispatch flow

1. A chat line arrives over IRC.
2. The message is lowercased. If it contains a trigger tag, the bridge removes
   the tag and forwards the remainder.
3. The bridge ignores messages without a trigger tag.

---
[← Operator setup](operator-setup.md) · [Home](../readme.md) · [Examples →](examples.md)
