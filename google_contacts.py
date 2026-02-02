import args
import base64
import json
import logging
import os
import requests
from talk.contact import Contact, Contacts
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


def get(ctx, raw, parsed):
    g = GoogleContacts(ctx)
    labels = args.get(ctx, args.LABELS)
    if raw:
        output_raw = g.raw_contacts
        if labels is not None:
            logger.debug(f'filtering using labels {labels}')
            output_raw = g.filter(labels)
        logger.debug(json.dumps(output_raw, default=lambda o: o.__dict__, sort_keys=True,indent=2))
        logger.debug(f'{len(output_raw)} raw filtered contacts found')
    if parsed:
        output_parsed = g.parsed_contacts
        if labels is not None:
            output_parsed = g.parsed_contacts.filter(labels)
        logger.debug({json.dumps(output_parsed, default=lambda o: o.__dict__, sort_keys=True,indent=2)})
        logger.debug(f'{len(output_parsed)} parsed filtered contacts found')        
    logger.debug(f'{len(g.raw_contacts)} raw unfiltered contacts found, parsed to {len(g.parsed_contacts)}')


class GoogleContacts:
    # If modifying these scopes, delete the token file.
    SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']
    TOKEN_FILE = '.google/token.json'
    CLIENT_SECRETS_FILE = '.google/credentials.json'

    def __init__(self, ctx):
        self.groups = Groups()
        logger.debug(f'contact groups: {json.dumps(self.groups.group_from_name, indent=2)}')

        self.raw_contacts = GoogleContacts.fetch()
        if args.get(ctx, args.FAVOURITE):
            logger.debug(f'filtering {len(self.raw_contacts)} by favourites')
            self.raw_contacts = self.filter([args.get(ctx, args.FAVOURITE_GROUP)])
            logger.debug(f'found {len(self.raw_contacts)} favourites')
        self.parsed_contacts = Contacts([p for c in self.raw_contacts if (p := self.parse(ctx, c)) is not None])

    def fetch():
        g = Service()

        # Call the People API to list connections.
        results = g.service.people().connections().list(
            resourceName='people/me',
            pageSize=1000,
            personFields='names,emailAddresses,phoneNumbers,memberships,photos,metadata'
        ).execute()
        
        return results.get('connections', [])


    def filter(self, labels):
        return [c for c in self.raw_contacts if self.is_member(c, labels)]


    def is_member(self, person, labels):
        memberships = person.get('memberships', [])
        google_group_ids = {m.get('contactGroupMembership', {}).get('contactGroupResourceName') for m in memberships}
        google_group_names = {name for name in self.groups.ids_to_group_names(google_group_ids)}
        lower_labels = {l.lower() for l in labels}
        intersection = google_group_names.intersection(lower_labels)
        return len(intersection) > 0

    def parse(self, ctx, person):
        memberships = person.get('memberships', [])
        google_group_ids = [m.get('contactGroupMembership', {}).get('contactGroupResourceName') for m in memberships]
        google_group_names = self.groups.ids_to_group_names(google_group_ids)
        passed_group = args.get(ctx, args.PASSED_GROUP)
        if passed_group is not None and passed_group.lower() in google_group_names:
            return None
        ignore_group = args.get(ctx, args.IGNORE_GROUP)
        if ignore_group is not None and ignore_group.lower() in google_group_names:
            return None

        first_name, last_name = GoogleContacts.names(person)
        if first_name is None and last_name is None:
            # Not sure when we'd ever have a contact with no names...
            return None

        mobile, home, work = GoogleContacts.phone_numbers(person)
        if mobile is None and home is None and work is None:
            # This export is going to be used for phone contacts so if there are no numbers, skip.
            return None

        labels = []
        for id in google_group_ids:
            fn = self.groups.formatted_name(id)
            if fn is None:
                continue
            labels.append(fn)
        return Contact(
            labels,
            first_name,
            last_name,
            GoogleContacts.email(person, first_name, last_name),
            mobile,
            home,
            work,
            GoogleContacts.avatar(person)
            )


    def names(person):
        names = person.get('names', [])
        if not names:
            return None, None
        return names[0].get('givenName', ''), names[0].get('familyName', '')


    def phone_numbers(person):
        phone_numbers = person.get('phoneNumbers', [])
        if not phone_numbers or len(phone_numbers) == 0:
            return None, None, None
        # Unifi doesn't like a phone number being specified if it's empty
        # (the Talk UI throws an error and you can't see any contacts).
        mobile = ''
        home = ''
        work = ''
        for number in phone_numbers:
            phone_number = number.get('canonicalForm', '') or number.get('value', '')
            match number.get('type', '').lower():
                case 'mobile':
                    mobile = phone_number
                case 'home':
                    home = phone_number
                case 'work':
                    work = phone_number
        return mobile, home, work


    def email(person, first_name, last_name):
        email_addresses = person.get('emailAddresses', [])
        email_addresses.sort(key=lambda e: e.get('value', ''))
        email = next((e.get('value', '') for e in email_addresses if e.get('type', '').lower() == 'main'), None)
        if len(email_addresses) > 1 and email is None:
            email = email_addresses[0].get('value', '')
            logger.warning(f'{len(email_addresses)} email addresses for {first_name} {last_name}, specify one as "main", defaulting to first one alphabetically ({email})')
        if email is None:
            email = ''
        return email


    def avatar(person):
        avatar = None
        photos = person.get('photos')
        for photo in photos:
            m = photo.get('metadata', {})
            if not m.get('primary', False):
                continue
            if m.get('source', {}).get('type', '') != 'PROFILE':
                continue
            url = photo.get('url', '')
            if url is not None:
                response = requests.get(url)
                if response.status_code == 200:
                    binary_content = response.content
                    avatar = base64.b64encode(binary_content).decode('utf-8')
                    break
        return avatar


class Groups:
    SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']
    TOKEN_FILE = '.google/token.json'
    CLIENT_SECRETS_FILE = '.google/credentials.json'


    def __init__(self):
        g = Service()
        self.raw_groups = g.service.contactGroups().list(pageSize=1000).execute()
        self.group_from_id = {}
        self.group_from_name = {}
        for group in self.raw_groups.get('contactGroups', {}):
            id = group.get('resourceName')
            name = group.get('name')
            if id is None or name is None:
                continue
            self.group_from_id[id] = group
            self.group_from_name[name] = group


    def ids_to_group_names(self, ids):
        group_names = []
        for id in ids:
            group = self.group_from_id.get(id)
            if group is None:
                continue
            group_names.append(group.get('name').lower())
        return group_names


    def id(self, name):
        group = self.group_from_name.get(name)
        if group is None:
            return None
        return group.get('id')
    

    def formatted_name(self, id):
        group = self.group_from_id.get(id)
        if group is None:
            return None
        return group.get('formattedName')


class Service:
    SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']
    TOKEN_FILE = '.google/token.json'
    CLIENT_SECRETS_FILE = '.google/credentials.json'

    def __init__(self):
        creds = None
        # The token file stores the user's access and refresh tokens.
        if os.path.exists(Service.TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(Service.TOKEN_FILE, Service.SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(Service.CLIENT_SECRETS_FILE, GoogleContacts.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run.
            with open(Service.TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        self.service = build('people', 'v1', credentials=creds)
