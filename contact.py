class Contact:
    def __init__(self, first_name, last_name, email, mobile_number, home_number, work_number):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.mobile_number = mobile_number
        self.home_number = home_number
        self.work_number = work_number

    def __str__(self):
        return f'"{self.first_name}","{self.last_name}",,,"{self.email}","{self.mobile_number}","{self.home_number}","{self.work_number}",,'
