from talk.talk import TalkAPI

def add_commands(subparsers):
    get_parser = subparsers.add_parser('get', help='get contacts from Unifi Talk')
    get_subparsers = get_parser.add_subparsers(help='get sub-command help')
    get_contacts_parser = get_subparsers.add_parser('contacts', help='all contacts will be retrieved')
    get_contacts_parser.set_defaults(func=get_contacts)
    get_lists_parser = get_subparsers.add_parser('lists', help='contact lists for these labels will be retrieved')
    get_lists_parser.set_defaults(func=get_contact_lists)


def get_contacts(args):
    talk = TalkAPI(args.server, args.username, args.password)
    contacts = talk.get_contacts()
    print(contacts)


def get_contact_lists(args):
    talk = TalkAPI(args.server, args.username, args.password)
    contact_lists = talk.get_contact_lists()
    print(contact_lists)
