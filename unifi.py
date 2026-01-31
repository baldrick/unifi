#!/usr/bin/env python

import logging
import argparse
import talk.unifi_talk
import google_contacts.commands


if __name__ == "__main__":
    parser = argparse.ArgumentParser('unifi')
    parser.add_argument('--server', help='Unifi server address', type=str, required=True)
    parser.add_argument('--username', help='username for Unifi', type=str, required=True)
    parser.add_argument('--password', help='password for Unifi', type=str, required=True)
    parser.add_argument('--log-level', help='set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)', type=str, default='INFO')
    subparsers = parser.add_subparsers(help='sub-command help')
    talk.unifi_talk.add_commands(subparsers)
    google_contacts.commands.add_commands(subparsers)
    args = parser.parse_args()
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(name)s %(message)s', datefmt='%H:%M:%S', level=getattr(logging, args.log_level.upper(), None))
    args.func(args)
