class AdminLog:
    def __init__(self, log_id=None, admin_id=None, action_type=None, target_table=None, target_id=None, reason=None, created_at=None, **kwargs):
        self.log_id = log_id
        self.admin_id = admin_id
        self.action_type = action_type
        self.target_table = target_table
        self.target_id = target_id
        self.reason = reason
        self.created_at = created_at