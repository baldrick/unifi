import requests
import urllib3
from talk.contact import Contact
from google_contacts.google_contacts import GoogleContacts

# CSV header for import to Unifi Talk.
HEADER = 'first_name,last_name,company,job_title,email,mobile_number,home_number,work_number,fax_number,other_number'

def add_commands(subparsers):
    talk_parser = subparsers.add_parser('talk', help='Unifi Talk related commands.')
    talk_subparsers = talk_parser.add_subparsers(help='talk sub-command help')
    add_get(talk_subparsers)
    add_sync(talk_subparsers)


def add_sync(subparsers):
    sync_parser = subparsers.add_parser('sync', help='Sync contacts from Google to Unifi Talk.')
    sync_parser.add_argument('--labels', nargs='+', help='Contacts for these labels will be synced.', type=str)
    sync_parser.set_defaults(func=sync_contacts)


def sync_contacts(args):
    talk = Talk(args.server, args.username, args.password)
    raw_contacts = GoogleContacts()
    filtered_contacts = {}
    for label in args.labels:
        filtered_contacts[label] = raw_contacts.filter(label)
        write_contacts(filtered_contacts[label], label)

    deleted = talk.delete_all_contacts()
    if deleted:
        print('Deleted all contacts from Unifi Talk')
        # tcls = talk.get_contact_lists()
        talk.save_contacts(args.labels[0], [filtered_contacts[args.labels[0]][0]])
    else:
        print('Failed to delete contacts from Unifi Talk: {deleted}')


def add_get(subparsers):
    get_parser = subparsers.add_parser('get', help='Get contacts from Unifi Talk.')
    get_subparsers = get_parser.add_subparsers(help='get sub-command help')
    get_contacts_parser = get_subparsers.add_parser('contacts', help='Contacts for these labels will be retrieved.')
    get_contacts_parser.set_defaults(func=get_contacts)
    get_lists_parser = get_subparsers.add_parser('lists', help='Contact lists for these labels will be retrieved.')
    get_lists_parser.set_defaults(func=get_contact_lists)


def get_contacts(args):
    talk = Talk(args.server, args.username, args.password)
    contacts = talk.get_contacts()
    print(contacts)


def get_contact_lists(args):
    talk = Talk(args.server, args.username, args.password)
    contact_lists = talk.get_contact_lists()
    print(contact_lists)


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


def dump(deduped_by_home_number, contacts_without_home_number) -> str:
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


def write_contacts(contacts, group_id):
    print(f'{len(contacts)} {group_id} contacts found')
    deduped_by_home_number, contacts_without_home_number = dedup_by_home_number(contacts)
    deduped_by_home_number = add_cohabitants(deduped_by_home_number)
    with open(f'{group_id}.csv', 'w') as f:
        f.write(HEADER + '\n')
        f.write(dump(deduped_by_home_number, contacts_without_home_number))


class Talk:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = None
        urllib3.disable_warnings()


    def login(self):
        if self.username is None:
            print('Error: username not set')
            return False
        if self.password is None:
            print('Error: password not set')
            return False
        if self.session is not None:
            return True
        self.session = requests.Session()
        url = f'{self.base_url}/api/auth/login'
        payload = {
            'username': self.username,
            'password': self.password
        }
        response = self.session.post(url, json=payload, verify=False)
        if response.status_code != 200:
            print(f'Error logging in: {response.status_code} {response.text}')
            return False
        else:
            self.xcsrf_token = response.headers.get('X-Csrf-Token')
            print(f'Logged in to Unifi')
            return True


    def get(self, path: str):
        if not self.login():
            return None
        url = f'{self.base_url}{path}'
        response = self.session.get(url, verify=False)
        if response.status_code != 200:
            print(f'Error fetching {path}: {response.status_code} {response.text}')
            return None
        return response.json()


    def post(self, path: str, payload):
        if not self.login():
            return False
        url = f'{self.base_url}{path}'
        response = self.session.post(url, json=payload, verify=False, headers={'X-Csrf-Token': self.xcsrf_token})
        if response.status_code != 200:
            print(f'Error posting to {path}: {response.status_code} {response.text}')
            return False
        return True


    def delete_all_contacts(self):
        contacts = self.get_contacts()
        if contacts is None:
            return False
        if len(contacts) == 0:
            print('No contacts to delete')
            return True
        ids = {
            'ids': [c['uuid'] for c in contacts]
        }
        print(ids)
        return self.post('/proxy/talk/api/contact/delete', ids)


    def get_contacts(self):
        return self.get('/proxy/talk/api/contacts')


    def save_contacts(self, contact_list_name, contacts):
        cls = self.get_contact_lists()
        contact_list_id = None
        for cl in cls:
            if cl['name'] == contact_list_name:
                contact_list_id = cl['id']
                break
        if contact_list_id is None:
            print(f'Error: contact list {contact_list_name} not found')
            return None

        print(f'Using contact list ID {contact_list_id} for {contact_list_name}')
        payload = {
            'contacts': [self.as_unifi(c) for c in contacts],
            'contactListId': contact_list_id
        }
        print(f'Saving {payload}')
        return None
        return self.post('/proxy/talk/api/contacts', payload)


    def get_contact_lists(self):
        return self.get('/proxy/talk/api/contact_list')
    

    def as_unifi(self, contact: Contact):
        return {
            'id': '',
            'uuid': '',
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'numbers': [
                {'did': contact.mobile_number, 'label': 'mobile'},
                {'did': contact.home_number, 'label': 'home'},
                {'did': contact.work_number, 'label': 'work'},
            ],
            'email': contact.email,
            'invalid_field': False,
        }