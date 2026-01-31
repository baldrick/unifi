from talk.get.get import add_commands as add_get_commands
from talk.sync.sync import add_commands as add_sync_commands

def add_commands(subparsers):
    u_parser = subparsers.add_parser('unifi', help='Unifi commands.')
    u_subparsers = u_parser.add_subparsers(help='unifi sub-command help')
    u_parser.add_argument('--server', help='Unifi server address', type=str, required=True)
    u_parser.add_argument('--username', help='username for Unifi', type=str, required=True)
    u_parser.add_argument('--password', help='password for Unifi', type=str, required=True)
    talk_parser = u_subparsers.add_parser('talk', help='Unifi Talk related commands.')
    talk_subparsers = talk_parser.add_subparsers(help='talk sub-command help')
    add_get_commands(talk_subparsers)
    add_sync_commands(talk_subparsers)
