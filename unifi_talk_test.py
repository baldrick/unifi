import unittest
import get_contacts as c

class DedupTest(unittest.TestCase):
    def test(self):
        contacts = []
        contacts.append(c.Contact('Alice', 'Smith', '', '', '123-456-789', ''))
        contacts.append(c.Contact('Bob', 'Smith', '', '', '123-456-789', ''))
        contacts.append(c.Contact('Charlie', 'Smith', '', '', '123-456-789', ''))   
        deduped, contacts_without_home_number = c.dedup_by_home_number(contacts)
        want_deduped = {}
        want_deduped['123-456-789'] = [
            c.Contact('Smith', 'home', '', '', '123-456-789', ''),
            c.Contact('Alice', 'Smith', '', '', '', ''),
            c.Contact('Bob', 'Smith', '', '', '', ''),
            c.Contact('Charlie', 'Smith', '', '', '', ''),
        ]
        got = c.dump(deduped, contacts_without_home_number)
        want = c.dump(want_deduped, contacts_without_home_number)
        self.assertEqual(got, want)

if __name__ == '__main__':
    unittest.main()