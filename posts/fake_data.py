from faker import Faker


class FakeData:

    def __init__(self):
        self.fake = Faker()
        self.fake_password = self.fake.password(length=40, special_chars=True)
        self.fake_username = self.fake.simple_profile()['username']
        self.fake_email = self.fake.simple_profile()['mail']
        self.fake_text = self.fake.text()
        self.fake_slug = self.fake.slug()