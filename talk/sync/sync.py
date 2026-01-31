import logging
from google_contacts.google_contacts import GoogleContacts
from talk.contact import Contact, Contacts
from talk.api import TalkAPI

logger = logging.getLogger(__name__)

# CSV header for import to Unifi Talk.
HEADER = 'first_name,last_name,company,job_title,email,mobile_number,home_number,work_number,fax_number,other_number'

def add_commands(subparsers):
    sync_parser = subparsers.add_parser('sync', help='sync contacts from Google to Unifi Talk')
    sync_parser.add_argument('--concatenate', action='store_true', help='output contacts for all labels together')
    sync_parser.add_argument('--grandstream', action='store_true', help='output contacts to XML file for Grandstream')
    sync_parser.add_argument('--unifi_csv', action='store_true', help='output contacts to CSV file for Unifi')
    sync_parser.add_argument('--unifi_talk', action='store_true', help='sync contacts with Unifi Talk')
    sync_parser.set_defaults(func=sync_contacts)


def sync_contacts(args):
    contacts = GoogleContacts().parsed_contacts

    if not args.grandstream and not args.unifi_csv and not args.unifi_talk:
        logger.error('at least one output must be specified')
        return

    write_grandstream_xml(args, contacts)
    write_unifi_csv(args, contacts)
    sync_unifi_talk(args, contacts)


def write_grandstream_xml(args, contacts):
    if not args.grandstream:
        return

    # Not sure if contacts really need to be normalized for Grandstream phones
    # but we may as well be consistent...
    for label in args.labels:
        filename = f'{label}.xml'
        with open(filename, 'w') as f:
            f.write('<AddressBook>\n')
            f.write('\n'.join([f'{c.grandstream_xml(i)}' for i, c in enumerate(contacts.normalized([label]))]))
            f.write('</AddressBook>')
        logger.info(f'wrote {filename}')


def write_unifi_csv(args, contacts):
    if not args.unifi_csv:
        return

    for label in args.labels:
        filename = f'{label}.csv'
        with open(filename, 'w') as f:
            f.write(HEADER + '\n')
            f.write('\n'.join([f'{c.unifi_csv()}' for c in contacts.normalized([label])]))
        logger.info(f'wrote {filename}')


def sync_unifi_talk(args, contacts):
    if not args.unifi_talk:
        return

    api = TalkAPI(args.server, args.username, args.password)
    ids, response = api.delete_all_contacts()
    if not response:
        logger.warning('failed to delete contacts from Unifi Talk: {response}')
        return
    
    logger.info(f'deleted all {len(ids)} contacts from Unifi Talk') if ids is not None else logger.info('no contacts to delete from Unifi Talk')
    cl_map = api.get_contact_lists()
    for label in args.labels:
        group_contacts = contacts.normalized([label])
        api.save_contacts(label, group_contacts, cl_map[label]['id'])
        logger.info(f'saved {len(group_contacts)} {label} contacts to Unifi Talk')
