import argparse
import time

from twitch_bridge import JarbasTwitchBridge


def connect_twitch_to_hivemind(channel, oauth, tags=None,
                               access_key=None,
                               host="wss://127.0.0.1",
                               port=5678,
                               password=None,
                               crypto_key=None,
                               self_signed=False,
                               lang="en-us",
                               nickname="bot",
                               bus=None):
    """Construct the bridge, connect to HiveMind and start relaying chat."""
    bridge = JarbasTwitchBridge(channel=channel,
                                oauth=oauth,
                                tags=tags,
                                access_key=access_key,
                                host=host,
                                port=port,
                                password=password,
                                crypto_key=crypto_key,
                                self_signed=self_signed,
                                lang=lang,
                                nickname=nickname,
                                bus=bus)
    bridge.start()
    return bridge


def main():
    parser = argparse.ArgumentParser(
        description="Relay a Twitch channel's chat to a HiveMind hub")
    parser.add_argument("--channel", required=True,
                        help="Twitch channel name to join")
    parser.add_argument("--oauth", required=True,
                        help="Twitch chat OAuth token (oauth:...), "
                             "get one at https://twitchapps.com/tmi/")
    parser.add_argument("--tag", action="append", dest="tags",
                        help="trigger tag, may be repeated (default: @bot)")
    parser.add_argument("--nickname", default="bot",
                        help="Twitch bot nickname")
    parser.add_argument("--lang", default="en-us", help="utterance language")
    # hivemind connection
    parser.add_argument("--access-key", help="HiveMind access key")
    parser.add_argument("--password", default=None, help="HiveMind password")
    parser.add_argument("--crypto-key", default=None,
                        help="HiveMind payload crypto key")
    parser.add_argument("--host", default="wss://127.0.0.1",
                        help="HiveMind host (ws:// or wss://)")
    parser.add_argument("--port", type=int, default=5678,
                        help="HiveMind port (default 5678)")
    parser.add_argument("--self-signed", action="store_true",
                        help="accept self-signed ssl certificates")

    args = parser.parse_args()

    if not args.host.startswith("ws"):
        parser.error("Invalid host, please specify a protocol "
                     "(ws:// or wss://)")

    connect_twitch_to_hivemind(channel=args.channel,
                               oauth=args.oauth,
                               tags=args.tags,
                               access_key=args.access_key,
                               host=args.host,
                               port=args.port,
                               password=args.password,
                               crypto_key=args.crypto_key,
                               self_signed=args.self_signed,
                               lang=args.lang,
                               nickname=args.nickname)
    # block forever so the background relay daemon keeps running
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
