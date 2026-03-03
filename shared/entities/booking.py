class Booking:
    def __init__(self, booking_id=None, customer_id=None, promotion_id=None, booking_date=None, status=None, total_amount=None, **kwargs):
        self.booking_id = booking_id
        self.customer_id = customer_id
        self.promotion_id = promotion_id
        self.booking_date = booking_date
        self.status = status
        self.total_amount = total_amount