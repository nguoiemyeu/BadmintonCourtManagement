class BookingDetail:
    def __init__(self, booking_detail_id=None, booking_id=None, court_id=None, start_time=None, end_time=None, price_per_hour=None, subtotal=None, **kwargs):
        self.booking_detail_id = booking_detail_id
        self.booking_id = booking_id
        self.court_id = court_id
        self.start_time = start_time
        self.end_time = end_time
        self.price_per_hour = price_per_hour
        self.subtotal = subtotal