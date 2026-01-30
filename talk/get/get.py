from talk.api import TalkAPI

def add_commands(subparsers):
    get_parser = subparsers.add_parser('get', help='get contacts from Unifi Talk')
    get_subparsers = get_parser.add_subparsers(help='get sub-command help')
    get_contacts_parser = get_subparsers.add_parser('contacts', help='all contacts will be retrieved')
    get_contacts_parser.set_defaults(func=get_contacts)
    get_lists_parser = get_subparsers.add_parser('lists', help='contact lists for these labels will be retrieved')
    get_lists_parser.set_defaults(func=get_contact_lists)


def get_contacts(args):
    api = TalkAPI(args.server, args.username, args.password)
    contacts = api.get_contacts()
    print(f'{len(contacts)} contacts found: {contacts}')


def get_contact_lists(args):
    api = TalkAPI(args.server, args.username, args.password)
    contact_lists = api.get_contact_lists()
    print(f'{len(contact_lists)} contact lists found: {contact_lists}')
