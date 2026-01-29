import argparse
import unifi_talk


if __name__ == "__main__":
    parser = argparse.ArgumentParser('unifi')
    parser.add_argument('--server', help='Unifi server address.', type=str, default='')
    parser.add_argument('--username', help='Username for Unifi.', type=str, default='')
    parser.add_argument('--password', help='Password for Unifi.', type=str, required=True)
    subparsers = parser.add_subparsers(help='Sub-command help')
    unifi_talk.add_commands(subparsers)
    args = parser.parse_args()
    args.func(args)
