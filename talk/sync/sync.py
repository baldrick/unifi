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
    sync_parser.add_argument('--csv', action='store_const', const=True, help='output contacts to CSV files')
    sync_parser.add_argument('--unifi', action='store_const', const=True, help='sync contacts with Unifi Talk')
    sync_parser.set_defaults(func=sync_contacts)


def sync_contacts(args):
    if args.labels is None or len(args.labels) == 0:
        logger.error('at least one label must be specified for sync')
        return

    # Get contacts from Google, create map of contacts for given labels.
    raw_contacts = GoogleContacts()
    filtered_contacts = {}
    for label in args.labels:
        filtered_contacts[label] = raw_contacts.filter(label)

    if not args.csv and not args.unifi:
        logger.error('at least one of --csv or --unifi must be specified')
        return

    # Output CSV files if requested.
    if args.csv:
        for label in args.labels:
            filename = write_csv(filtered_contacts[label], label)
            logger.info(f'wrote {filename}')

    # Sync with Unifi Talk if requested.
    if args.unifi:
        api = TalkAPI(args.server, args.username, args.password)
        ids, response = api.delete_all_contacts()
        if response is not False:
            logger.info(f'deleted all {len(ids)} contacts from Unifi Talk') if ids is not None else logger.info('no contacts to delete from Unifi Talk')
            cl_map = api.get_contact_lists()
            for label in args.labels:
                api.save_contacts(label, filtered_contacts[label], cl_map[label]['id'])
                logger.info(f'saved {len(filtered_contacts[label])} {label} contacts to Unifi Talk')
        else:
            logger.warning('failed to delete contacts from Unifi Talk: {deleted}')


def write_csv(contacts, group_id):
    logger.debug(f'{len(contacts)} {group_id} raw contacts found')
    deduped_by_home_number, contacts_without_home_number = dedup_by_home_number(contacts)
    deduped_by_home_number = add_cohabitants(deduped_by_home_number)
    logger.debug(f'{len(deduped_by_home_number) + len(contacts_without_home_number)} normalized {group_id} contacts found')
    filename = f'{group_id}.csv'
    with open(filename, 'w') as f:
        f.write(HEADER + '\n')
        f.write(contacts_as_csv(deduped_by_home_number, contacts_without_home_number))
    return filename


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


def contacts_as_csv(deduped_by_home_number, contacts_without_home_number) -> str:
    output = ''
    for hn, contacts in deduped_by_home_number.items():
        if contacts is None:
            logger.warning(f'contacts is None for {hn}')
            continue
        for contact in contacts:
            output += contact.__str__() + '\n'
    for contact in contacts_without_home_number:
        output += contact.__str__() + '\n'
    return output
