import logging
import os
from talk.contact import Contact
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

class GoogleContacts:
    # If modifying these scopes, delete the token.json file.
    SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']

    def __init__(self):
        self.raw_contacts = GoogleContacts.fetch()

    def fetch():
        creds = None
        # token.json stores the user's access and refresh tokens
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', GoogleContacts.SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', GoogleContacts.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        service = build('people', 'v1', credentials=creds)

        # Call the People API to list connections
        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=1000,
            personFields='names,emailAddresses,phoneNumbers,memberships'
        ).execute()
        
        return results.get('connections', [])


    def filter(self, group_id):
        all_contacts = []
        for person in self.raw_contacts:
            parsed_contact = GoogleContacts.parse(person, group_id)
            if parsed_contact is not None:
                all_contacts.append(parsed_contact)
        return all_contacts
        

    def parse(person, group_id):
        memberships = person.get('memberships', [])
        include = False
        for membership in memberships:
            group = membership.get('contactGroupMembership', {}).get('contactGroupResourceName')
            if group == f'contactGroups/{group_id.lower()}':
                include = True
            if group == 'contactGroups/5815031b8d533454': # Passed :-(
                include = False
                break
        if not include:
            return None

        names = person.get('names', [])
        if not names:
            return None
        first_name = names[0].get('givenName', '')
        last_name = names[0].get('familyName', '')

        phone_numbers = person.get('phoneNumbers', [])
        if not phone_numbers or len(phone_numbers) == 0:
            # This export is going to be used for phone contacts so if there are no numbers, skip.
            return None
        mobile_number = ''
        home_number = ''
        work_number = ''
        for number in phone_numbers:
            type_ = number.get('type', '').lower()
            phone_number = number.get('canonicalForm', '')
            raw = number.get('value', '')
            if not phone_number:
                phone_number = raw
            if type_ == 'mobile':
                mobile_number = phone_number
            elif type_ == 'home':
                home_number = phone_number
            elif type_ == 'work':
                work_number = phone_number

        email = ''
        email_addresses = person.get('emailAddresses', [])
        for address in email_addresses:
            match address.get('type', '').lower():
                case 'main':
                    email = address.get('value', '')
                    break
        if len(email_addresses) > 1 and email == '':
            logger.warning(f'{len(email_addresses)} email addresses for {first_name} {last_name}')

        return Contact(first_name, last_name, email, mobile_number, home_number, work_number)
