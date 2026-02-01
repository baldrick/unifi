from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class Contact:
    labels: str # Array of labels
    first_name: str
    last_name: str
    email: str
    mobile_number: str
    home_number: str
    work_number: str
    avatar:str # base64 encoded


    def grandstream_xml(self, id):
        # Should use a library to generate this but it's not obvious which one...
        # ... and our requirements are simple so this hack will do for now!
        return f'''<Contact>
            <id>{id}</id>
            <FirstName>{self.first_name}</FirstName>
            <LastName>{self.last_name}</LastName>
            <RingtoneUrl>default ringtone</RingtoneUrl>
            <Frequent>0</Frequent>
            {self.grandstream_xml_number(1, "Home", self.home_number)}
            {self.grandstream_xml_number(1, "Cell", self.mobile_number)}
            {self.grandstream_xml_number(1, "Work", self.work_number)}
            <Primary>0</Primary>
        </Contact>'''


    def grandstream_xml_number(self, account_index, phone_label, number):
        if len(number) == 0:
            return ''
        return f'''<Phone type="{phone_label}">
                    <phonenumber>{number}</phonenumber>
                    <accountindex>{account_index}</accountindex>
            </Phone>
            '''


    def unifi_csv(self):
        return f'"{self.first_name}","{self.last_name}",,,"{self.email}","{self.mobile_number}","{self.home_number}","{self.work_number}",,'


class Contacts:
    contacts = []


    def __init__(self, contacts):
        self.contacts = contacts


    def __len__(self):
        return len(self.contacts)
    

    def filter(self, labels):
        # Get the contacts with any label matching the given labels.
        lower_labels = [l.lower() for l in labels]
        return Contacts([c for c in self.contacts if any(l.lower() in lower_labels for l in c.labels)])


    def normalize(self, label):
        # Go through contacts finding those sharing a home number
        # For those, create a "surname home (first names)" contact
        # and remove the home number from the original contact.
        self.contacts.extend(self.shared_home(self.contacts, label))
        return self.contacts


    def shared_home(self, contacts, label):
        # Gather contacts by home number.
        home_contacts = {}
        for c in contacts:
            if c.home_number is None or len(c.home_number) == 0:
                continue
            hn = f'{c.home_number}'
            if hn in home_contacts:
                home_contacts[hn].append(c)
            else:
                home_contacts[hn] = [c]

        # Create separate array of "surname home (first1, first2...)" contacts
        # for contacts who share a home number.  Clear the home number for the
        # sharing contacts.
        logger.debug(f'contacts by home number: {home_contacts}')
        results = []
        for hn, cs in home_contacts.items():
            if len(cs) > 1:
                fn = [c.first_name for c in cs]
                fn.sort()
                first_names = ','.join(fn)
                results.append(Contact([label], cs[0].last_name, f'home ({first_names})', '', '', hn, '', ''))
                logger.debug(f'first names: {first_names}, results:{results}')
                for c in cs:
                    c.home_number = ''
        logger.debug(f'shared_home results:{results}')
        return results

    