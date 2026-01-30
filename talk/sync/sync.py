from google_contacts.google_contacts import GoogleContacts
from talk.contact import Contact
from talk.api import TalkAPI

# CSV header for import to Unifi Talk.
HEADER = 'first_name,last_name,company,job_title,email,mobile_number,home_number,work_number,fax_number,other_number'


def add_commands(subparsers):
    sync_parser = subparsers.add_parser('sync', help='sync contacts from Google to Unifi Talk')
    sync_parser.add_argument('--labels', nargs='+', help='contacts for these labels will be synced', type=str)
    sync_parser.set_defaults(func=sync_contacts)


def sync_contacts(args):
    api = TalkAPI(args.server, args.username, args.password)
    raw_contacts = GoogleContacts()
    filtered_contacts = {}
    for label in args.labels:
        filtered_contacts[label] = raw_contacts.filter(label)
        write_csv(filtered_contacts[label], label)

    deleted = api.delete_all_contacts()
    if deleted:
        print('Deleted all contacts from Unifi Talk')
        # TODO ... why doesn't this work?!
        # tcls = talk.get_contact_lists()
        api.save_contacts(args.labels[0], [filtered_contacts[args.labels[0]][0]])
    else:
        print('Failed to delete contacts from Unifi Talk: {deleted}')


def write_csv(contacts, group_id):
    print(f'{len(contacts)} {group_id} contacts found')
    deduped_by_home_number, contacts_without_home_number = dedup_by_home_number(contacts)
    deduped_by_home_number = add_cohabitants(deduped_by_home_number)
    with open(f'{group_id}.csv', 'w') as f:
        f.write(HEADER + '\n')
        f.write(contacts_as_csv(deduped_by_home_number, contacts_without_home_number))


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
            print(f'Error: no contacts for {hn}')
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
            print(f'Error: contacts is None for {hn}')
            continue
        for contact in contacts:
            output += contact.__str__() + '\n'
    for contact in contacts_without_home_number:
        output += contact.__str__() + '\n'
    return output
