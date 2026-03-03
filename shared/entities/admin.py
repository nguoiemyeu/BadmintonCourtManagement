class Admin:
    def __init__(self, admin_id=None, full_name=None, username=None, password_hash=None, role='Staff', status='Active', **kwargs):
        self.admin_id = admin_id
        self.full_name = full_name
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.status = status