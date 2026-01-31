import json
import logging
from google_contacts.google_contacts import GoogleContacts

logger = logging.getLogger(__name__)

def add_commands(subparsers):
    g_parser = subparsers.add_parser('google', help='Google related commands useful for Unifi Talk.')
    g_subparsers = g_parser.add_subparsers(help='google sub-command help')
    get_parser = g_subparsers.add_parser('get', help='get contacts from Google')
    get_parser.set_defaults(func=get_contacts)


def get_contacts(args):
    g = GoogleContacts()
    logger.info(f'{len(g.parsed_contacts)} contacts found: {json.dumps(g.parsed_contacts, default=lambda o: o.__dict__, sort_keys=True,indent=2)}')
    logger.info(f'{len(g.parsed_contacts)} raw contacts found: {json.dumps(g.raw_contacts, default=lambda o: o.__dict__, sort_keys=True,indent=2)}')