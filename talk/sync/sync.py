import logging
from google_contacts.google_contacts import GoogleContacts
from talk.api import TalkAPI

logger = logging.getLogger(__name__)

# CSV header for import to Unifi Talk.
HEADER = 'first_name,last_name,company,job_title,email,mobile_number,home_number,work_number,fax_number,other_number'

def sync_contacts(ctx, grandstream, unifi_csv, unifi_talk):
    contacts = GoogleContacts().parsed_contacts

    if not (grandstream or unifi_csv or unifi_talk):
        logger.error('at least one output must be specified')
        return

    if grandstream: write_grandstream_xml(ctx, contacts)
    if unifi_csv: write_unifi_csv(ctx, contacts)
    if unifi_talk: sync_unifi_talk(ctx, contacts)


def write_grandstream_xml(ctx, contacts):
    # Not sure if contacts really need to be normalized for Grandstream phones
    # but we may as well be consistent...
    for label in ctx.obj['labels']:
        filename = f'{label}.xml'
        with open(filename, 'w') as f:
            f.write('<AddressBook>\n')
            f.write('\n'.join([f'{c.grandstream_xml(i)}' for i, c in enumerate(contacts.normalized([label]))]))
            f.write('</AddressBook>')
        logger.info(f'wrote {filename}')


def write_unifi_csv(ctx, contacts):
    for label in ctx.obj['labels']:
        filename = f'{label}.csv'
        with open(filename, 'w') as f:
            f.write(HEADER + '\n')
            f.write('\n'.join([f'{c.unifi_csv()}' for c in contacts.normalized([label])]))
        logger.info(f'wrote {filename}')


def sync_unifi_talk(ctx, contacts):
    api = TalkAPI(ctx)
    ids, response = api.delete_all_contacts()
    if not response:
        logger.warning('failed to delete contacts from Unifi Talk: {response}')
        return
    
    logger.info(f'deleted all {len(ids)} contacts from Unifi Talk') if ids is not None else logger.info('no contacts to delete from Unifi Talk')
    cl_map = api.get_contact_lists()
    for label in ctx.obj['labels']:
        group_contacts = contacts.normalized([label])
        api.save_contacts(label, group_contacts, cl_map[label]['id'])
        logger.info(f'saved {len(group_contacts)} {label} contacts to Unifi Talk')
