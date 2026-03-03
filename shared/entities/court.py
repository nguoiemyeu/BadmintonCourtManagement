class Court:
    def __init__(self, court_id=None, court_code=None, status=None, **kwargs):
        self.court_id = court_id
        self.court_code = court_code
        self.status = status