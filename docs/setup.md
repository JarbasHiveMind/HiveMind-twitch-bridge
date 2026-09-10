# Setup Walkthrough

This page takes you from nothing to a working Twitch chat bot backed by a HiveMind hub.

## How the bridge fits together

The bridge is a HiveMind satellite with two connections:

- **To Twitch**: it joins the channel's IRC chat with a bot account and OAuth token and listens for messages.
- **To the HiveMind hub**: it connects as a HiveMind terminal using an access key.

A chat message that contains a trigger tag becomes a `recognizer_loop:utterance` sent to the hub. The sender's username travels in the message context, so the hub's `speak` reply is echoed back to the channel, addressed to that user.

```
Twitch chat (IRC)  ⇄  bridge  ⇄  HiveMind hub  ⇄  OVOS pipeline / skills
```

## Step 1: Stand up a HiveMind hub

Install and run [hivemind-core](https://github.com/JarbasHiveMind/HiveMind-core):

```bash
pip install hivemind-core
hivemind-core listen
```

The hub listens on port `5678` by default.

## Step 2: Register the bridge as a client

On the hub machine:

```bash
hivemind-core add-client --name twitch-bridge \
  --access-key "your-access-key" --password "your-password"
```

Keep the access key. List clients with `hivemind-core list-clients`.

## Step 3: Get a Twitch chat token

1. Create or pick a Twitch account for the bot.
2. Generate a chat OAuth token at <https://twitchapps.com/tmi/> while logged in as that account. It looks like `oauth:abcd1234...`.
3. Note the channel name whose chat the bot should join.

## Step 4: Install the bridge

```bash
git clone https://github.com/JarbasHiveMind/HiveMind-twitch-bridge
cd HiveMind-twitch-bridge
pip install -r requirements.txt
```

## Step 5: Configure and run

Edit the call to `connect_twitch_to_hivemind(...)` at the bottom of `twitch_bridge/__main__.py` with your `channel`, `oauth`, trigger `tags`, and HiveMind `host`/`port`/`key`. Then run:

```bash
python -m twitch_bridge
```

## Step 6: Talk to it

In the channel's chat, include a trigger tag:

```
@bot what is the weather?
```

The bridge strips the tag, forwards the message to the hub, and posts the spoken answer back as `@user , <answer>`.

---
[Home](../readme.md) · [Operator setup →](operator-setup.md)
