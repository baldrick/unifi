import logging
from google_contacts import GoogleContacts
from talk.api import TalkAPI

logger = logging.getLogger(__name__)

# CSV header for import to Unifi Talk.
HEADER = 'first_name,last_name,company,job_title,email,mobile_number,home_number,work_number,fax_number,other_number'

def sync_contacts(ctx, concatenate, grandstream, unifi_csv, unifi_talk):
    contacts = GoogleContacts().parsed_contacts

    if not (grandstream or unifi_csv or unifi_talk):
        logger.error('at least one output must be specified')
        return

    if grandstream: write_grandstream_xml(ctx, concatenate, contacts)
    if unifi_csv: write_unifi_csv(ctx, concatenate, contacts)
    if unifi_talk: sync_unifi_talk(ctx, concatenate, contacts)


def write_grandstream_xml(ctx, concatenate, contacts):
    # Not sure if contacts really need to be normalized for Grandstream phones
    # but we may as well be consistent...
    if concatenate is not None:
        contacts = contacts.filter(ctx.obj['labels']).normalize(concatenate)
        write_grandstream_xml_file(contacts, f'{concatenate}.xml')
    else:
        for label in ctx.obj['labels']:
            write_grandstream_xml_file(contacts.filter([label]).normalize(label), f'{label}.xml')


def write_grandstream_xml_file(contacts, filename):
    with open(filename, 'w') as f:
        f.write('<AddressBook>\n')
        f.write('\n'.join([f'{c.grandstream_xml(i)}' for i, c in enumerate(contacts)]))
        f.write('</AddressBook>')
    logger.info(f'wrote {len(contacts)} to {filename}')


def write_unifi_csv(ctx, concatenate, contacts):
    if concatenate is not None:
        contacts = contacts.filter(ctx.obj['labels']).normalize(concatenate)
        write_unifi_csv_file(contacts, f'{concatenate}.csv')
    else:
        for label in ctx.obj['labels']:
            write_unifi_csv_file(contacts.filter([label]).normalize(label), f'{label}.csv')


def write_unifi_csv_file(contacts, filename):
    with open(filename, 'w') as f:
        f.write(HEADER + '\n')
        f.write('\n'.join([f'{c.unifi_csv()}' for c in contacts]))
    logger.info(f'wrote {len(contacts)} to {filename}')


def sync_unifi_talk(ctx, concatenate, contacts):
    api = TalkAPI(ctx)

    # Delete all contacts to ensure no incoming contacts have overlapping
    # phone numbers.
    ids, response = api.delete_all_contacts()
    if not response:
        logger.error(f'failed to delete all contacts from Unifi Talk: {response}')
        return
    logger.info(f'deleted all {len(ids)} contacts from Unifi Talk') if ids is not None else logger.info('no contacts to delete from Unifi Talk')
    
    labels = ctx.obj['labels']
    concatenate_label = None
    if concatenate is not None:
        concatenate_label = [concatenate]

    # We've deleted all contacts.  Let's also delete all contact lists that
    # don't match the labels / concatenate label.  Don't touch the matching
    # lists though - they may be associated with phones already (presumably
    # by id) and recreating them could change their id and therefore associate
    # the wrong contacts with a phone ... maybe.
    deleted, failed = api.delete_all_contact_lists(concatenate_label or labels)
    if len(failed) > 0:
        logger.error(f'deleted {len(deleted)} but failed to delete {len(failed)} contact lists from Unifi Talk')
        return
    logger.info(f'deleted all {len(deleted)} contact lists from Unifi Talk') if len(deleted) > 0 else logger.info('no contact lists to delete from Unifi Talk')

    if not api.add_contact_lists_if_missing(concatenate_label or labels):
        logger.error(f'failed to create one or more contact lists {concatenate_label or labels}')
        return
    cl_map = api.get_contact_lists()
    if concatenate is not None:
        group_contacts = contacts.filter(labels).normalize(concatenate)
        api.save_contacts(concatenate, group_contacts, cl_map[concatenate]['id'])
        logger.info(f'saved {len(group_contacts)} {concatenate} contacts to Unifi Talk')
    else:
        for label in labels:
            group_contacts = contacts.filter([label]).normalize(label)
            api.save_contacts(label, group_contacts, cl_map[label]['id'])
            logger.info(f'saved {len(group_contacts)} {label} contacts to Unifi Talk')
