class Payment:
    def __init__(self, payment_id=None, booking_id=None, amount=None, payment_method=None, payment_date=None, status=None, **kwargs):
        self.payment_id = payment_id
        self.booking_id = booking_id
        self.amount = amount
        self.payment_method = payment_method
        self.payment_date = payment_date
        self.status = status