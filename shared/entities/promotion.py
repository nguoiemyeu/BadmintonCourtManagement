class Promotion:
    def __init__(self, promotion_id=None, promotion_name=None, discount_type=None, discount_value=None, start_date=None, end_date=None, is_active=None, **kwargs):
        self.promotion_id = promotion_id
        self.promotion_name = promotion_name
        self.discount_type = discount_type
        self.discount_value = discount_value
        self.start_date = start_date
        self.end_date = end_date
        self.is_active = is_active