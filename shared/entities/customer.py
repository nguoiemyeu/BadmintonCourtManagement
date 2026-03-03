class Customer:
    def __init__(self, customer_id=None, full_name=None, phone_number=None, created_at=None, **kwargs):
        self.customer_id = customer_id
        self.full_name = full_name
        self.phone_number = phone_number
        self.created_at = created_at