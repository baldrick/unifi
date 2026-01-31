import json
import logging
import requests
import urllib3
from talk.contact import Contact

logger = logging.getLogger(__name__)

class TalkAPI:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = None
        urllib3.disable_warnings()


    def login(self):
        if self.username is None:
            logger.error('username not set')
            return False
        if self.password is None:
            logger.error('password not set')
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
            logger.error(f'logging in: {response.status_code} {response.text}')
            return False
        else:
            self.xcsrf_token = response.headers.get('X-Csrf-Token')
            logger.debug(f'logged in to Unifi')
            return True


    def get(self, path: str):
        if not self.login():
            return None
        url = f'{self.base_url}{path}'
        response = self.session.get(url, verify=False)
        if response.status_code != 200:
            logger.error(f'failed to fetch {path}: {response.status_code} {response.text}')
            return None
        return response.json()


    def post(self, path: str, payload):
        if not self.login():
            return False
        url = f'{self.base_url}{path}'
        response = self.session.post(url, json=payload, verify=False, headers={'X-Csrf-Token': self.xcsrf_token})
        if response.status_code != 200:
            logger.error(f'failed to post to {path}: {response.status_code} {response.text}')
            return False
        if response.text == '':
            return True
        return response.json()


    def delete_all_contacts(self):
        contacts = self.get_contacts()
        if contacts is None:
            return None, False
        if len(contacts) == 0:
            logger.debug('no contacts to delete')
            return None, True
        ids = {
            'ids': [c['uuid'] for c in contacts]
        }
        return ids['ids'], self.post('/proxy/talk/api/contact/delete', ids)


    def get_contacts(self):
        return self.get('/proxy/talk/api/contacts')


    def save_contacts(self, contact_list_name, contacts, contact_list_id):
        logger.debug(f'saving {len(contacts)} contacts to list {contact_list_name} (#{contact_list_id}): {contacts}')
        cls = self.get_contact_lists()
        logger.debug(f'contact lists fetched: {json.dumps(cls, indent=2)}')
        cl = cls[contact_list_name]
        if cl is None:
            logger.error(f'contact list {contact_list_name} not found')
            return None

        contact_list_id = cl['id']
        if contact_list_id is None:
            logger.error(f'ID for contact list {contact_list_name} not found, contact list: {json.dumps(cl, indent=2)}')
            return None

        logger.debug(f'contact list ID {contact_list_id} for {contact_list_name}')
        payload = {
            'contacts': [self.as_unifi(c, contact_list_id) for c in contacts],
            'contactListId': contact_list_id
        }
        logger.debug(f'saving {payload}')
        return self.post('/proxy/talk/api/contacts', payload)


    def get_contact_lists(self):
        cls = self.get('/proxy/talk/api/contact_list')
        cl_map = {}
        logger.debug(f'fetched contact lists: {cls}')
        for cl in cls:
            cl_map[cl['name']] = cl
        logger.debug(f'contact list map: {cl_map}')
        return cl_map


    def as_unifi(self, contact: Contact, contact_list_id: int):
        numbers = []
        self.add_number(numbers, contact.mobile_number, 'mobile')
        self.add_number(numbers, contact.home_number, 'home')
        self.add_number(numbers, contact.work_number, 'work')
        return {
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'numbers': numbers,
            'email': contact.email,
            'contactLists': [contact_list_id],
            'invalid_field': False,
            'temporary_avatar': contact.avatar,
        }
    

    def add_number(self, numbers, number, label):
        if number != '':
            numbers.append({'did': number, 'label': label})