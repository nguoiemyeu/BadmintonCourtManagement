class Refund:
    def __init__(self, refund_id=None, booking_id=None, refund_amount=None, refund_date=None, reason=None, **kwargs):
        self.refund_id = refund_id
        self.booking_id = booking_id
        self.refund_amount = refund_amount
        self.refund_date = refund_date
        self.reason = reason