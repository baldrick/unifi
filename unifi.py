#!/usr/bin/env python

import argparse
import talk.unifi_talk


if __name__ == "__main__":
    parser = argparse.ArgumentParser('unifi')
    parser.add_argument('--server', help='Unifi server address', type=str, required=True)
    parser.add_argument('--username', help='username for Unifi', type=str, required=True)
    parser.add_argument('--password', help='password for Unifi', type=str, required=True)
    subparsers = parser.add_subparsers(help='sub-command help')
    talk.unifi_talk.add_commands(subparsers)
    args = parser.parse_args()
    args.func(args)
