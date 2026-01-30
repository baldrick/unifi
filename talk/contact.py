class Contact:
    def __init__(self, first_name, last_name, email, mobile_number, home_number, work_number):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.mobile_number = mobile_number
        self.home_number = home_number
        self.work_number = work_number

    def __str__(self):
        return self.unifi_csv()

    def unifi_csv(self):
        return f'"{self.first_name}","{self.last_name}",,,"{self.email}","{self.mobile_number}","{self.home_number}","{self.work_number}",,'

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

    def grandstream_xml_number(self, account_index, label, number):
        if len(number) == 0:
            return ''
        return f'''<Phone type="{label}">
                    <phonenumber>{number}</phonenumber>
                    <accountindex>{account_index}</accountindex>
            </Phone>
            '''
