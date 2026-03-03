class Member:
    def __init__(self, customer_id=None, username=None, password_hash=None, register_date=None, status='Active', **kwargs):
        self.customer_id = customer_id
        self.username = username
        self.password_hash = password_hash
        self.register_date = register_date
        self.status = status