import logging
from google_contacts.google_contacts import GoogleContacts
from talk.contact import Contact
from talk.api import TalkAPI

logger = logging.getLogger(__name__)

# CSV header for import to Unifi Talk.
HEADER = 'first_name,last_name,company,job_title,email,mobile_number,home_number,work_number,fax_number,other_number'

def add_commands(subparsers):
    sync_parser = subparsers.add_parser('sync', help='sync contacts from Google to Unifi Talk')
    sync_parser.add_argument('--labels', nargs='+', help='contacts for these labels will be synced', type=str)
    sync_parser.add_argument('--unifi_csv', action='store_const', const=True, help='output contacts to CSV file for Unifi')
    sync_parser.add_argument('--grandstream', action='store_const', const=True, help='output contacts to XML file for Grandstream')
    sync_parser.add_argument('--unifi', action='store_const', const=True, help='sync contacts with Unifi Talk')
    sync_parser.set_defaults(func=sync_contacts)


def sync_contacts(args):
    if args.labels is None or len(args.labels) == 0:
        logger.error('at least one label must be specified for sync')
        return

    # Get contacts from Google, create map of contacts for given labels.
    # Normalize those contacts by collating ones with the same home number.
    raw_contacts = GoogleContacts()
    normalized_contacts = {label: normalize(raw_contacts.filter(label), label) for label in args.labels}
    #for label in args.labels:
    #    normalized_contacts[label] = normalize(raw_contacts.filter(label), label)

    if not args.unifi_csv and not args.grandstream and not args.unifi:
        logger.error('at least one of --csv, --grandstream or --unifi must be specified')
        return

    write_unifi_csv(args, normalized_contacts)
    write_grandstream_xml(args, normalized_contacts)
    write_unifi(args, normalized_contacts)


def normalize(contacts, group_id):
    group_contacts = contacts[group_id]
    logger.debug(f'{len(group_contacts)} {group_id} raw contacts found')
    deduped_by_home_number, contacts_without_home_number = dedup_by_home_number(group_contacts)
    deduped_by_home_number = add_cohabitants(deduped_by_home_number)
    logger.debug(f'{len(deduped_by_home_number) + len(contacts_without_home_number)} normalized {group_id} contacts found')
    normalized_contacts = [c for c in dedup_by_home_number.items()]
    normalized_contacts.extend(contacts_without_home_number)
    return normalized_contacts


def dedup_by_home_number(contacts):
    contacts_by_home_number = {}
    contacts_without_home_number = []
    for c in contacts:
        if c.last_name == 'home':
            continue
        hn = c.home_number
        if hn == '':
            contacts_without_home_number.append(c)
            continue
        ec = contacts_by_home_number.get(hn)
        if ec is None:
            contacts_by_home_number[hn] = [c]
        else:
            if ec[0].last_name == 'home':
                c.home_number = ''
                contacts_by_home_number[hn].append(c)
            else:
                hc = [Contact(c.last_name, 'home', '', '', hn, '')]
                c.home_number = ''
                ec[0].home_number = ''
                ec.append(c)
                hc.extend(ec)
                contacts_by_home_number[hn] = hc
    return contacts_by_home_number, contacts_without_home_number


def add_cohabitants(deduped_by_home_number):
    for hn, contacts in deduped_by_home_number.items():
        if contacts is None or len(contacts) == 0:
            logger.warning(f'no contacts for {hn}')
            continue
        if contacts[0].last_name != 'home':
            continue
        cohabitants = contacts[1:]
        cohabitant_names = [f'{c.first_name}' for c in cohabitants]
        cohabitant_names.sort()
        contacts[0].last_name = 'home (' + ', '.join(cohabitant_names) + ')'
    return deduped_by_home_number


def write_unifi_csv(args, contacts):
    if not args.unifi_csv:
        return

    for label in args.labels:
        filename = f'{label}.csv'
        with open(filename, 'w') as f:
            f.write(HEADER + '\n')
            f.write('\n'.join([f'{c.unifi_csv()}' for c in contacts]))
        logger.info(f'wrote {filename}')


def write_grandstream_xml(args, contacts):
    if not args.grandstream:
        return

    for label in args.labels:
        filename = f'{label}.csv'
        with open(filename, 'w') as f:
            f.write('<AddressBook>\n')
            f.write('\n'.join([f'{c.grandstream_xml(i)}' for i, c in enumerate(contacts)]))
            f.write('</AddressBook>')
        logger.info(f'wrote {filename}')


def write_unifi(args, contacts):
    if not args.unifi:
        return

    api = TalkAPI(args.server, args.username, args.password)
    ids, response = api.delete_all_contacts()
    if response is not False:
        logger.info(f'deleted all {len(ids)} contacts from Unifi Talk') if ids is not None else logger.info('no contacts to delete from Unifi Talk')
        cl_map = api.get_contact_lists()
        for label in args.labels:
            api.save_contacts(label, contacts[label], cl_map[label]['id'])
            logger.info(f'saved {len(contacts[label])} {label} contacts to Unifi Talk')
    else:
        logger.warning('failed to delete contacts from Unifi Talk: {deleted}')


# def contacts_as_csv(contacts) -> str:
#     return 
    # for hn, contacts in deduped_by_home_number.items():
    #     if contacts is None:
    #         logger.warning(f'contacts is None for {hn}')
    #         continue
    #     for contact in contacts:
    #         output += contact.__str__() + '\n'
    # for contact in contacts_without_home_number:
    #     output += contact.__str__() + '\n'
    # return output
