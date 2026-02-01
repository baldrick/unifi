import unittest
import talk.contact as c

class DedupTest(unittest.TestCase):
    def test(self):
        labels = ['label']
        contacts = []
        contacts.append(c.Contact(labels, 'Alice', 'Smith', '', '1', '123-456-789', '', ''))
        contacts.append(c.Contact(labels, 'Bob', 'Smith', '', '2', '123-456-789', '', ''))
        contacts.append(c.Contact(labels, 'Charlie', 'Smith', '', '3', '123-456-789', '', ''))
        all_contacts = c.Contacts(contacts)
        got = all_contacts.normalize(labels[0])
        want = [
            c.Contact(labels, 'Alice', 'Smith', '', '1', '', '', ''),
            c.Contact(labels, 'Bob', 'Smith', '', '2', '', '', ''),
            c.Contact(labels, 'Charlie', 'Smith', '', '3', '', '', ''),
            c.Contact(labels, 'Smith', 'home (Alice,Bob,Charlie)', '', '', '123-456-789', '', ''),
        ]
        got.sort(key=lambda x: x.mobile_number)
        want.sort(key=lambda x: x.mobile_number)
        self.assertEqual(got, want)

if __name__ == '__main__':
    unittest.main()
