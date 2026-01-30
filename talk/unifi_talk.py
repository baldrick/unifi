from talk.get.get import add_commands as add_get_commands
from talk.sync.sync import add_commands as add_sync_commands

def add_commands(subparsers):
    talk_parser = subparsers.add_parser('talk', help='Unifi Talk related commands.')
    talk_subparsers = talk_parser.add_subparsers(help='talk sub-command help')
    add_get_commands(talk_subparsers)
    add_sync_commands(talk_subparsers)
