import requests
import urllib3
from talk.contact import Contact

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