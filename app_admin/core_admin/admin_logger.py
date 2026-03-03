from shared.database.db_manager import db
from datetime import datetime


class AdminLogger:
    """
    Ghi nhận thao tác của Admin vào bảng Admin_log
    """

    VALID_ACTION_TYPES = {
        "CREATE", "UPDATE", "DELETE", "UPDATE_STATUS",
        "REFUND", "CANCEL_BOOKING", "LOGIN", "LOGOUT"
    }

    @staticmethod
    def _admin_exists(admin_id):
        """Kiểm tra Admin có tồn tại trong hệ thống không"""
        query = "SELECT COUNT(*) AS total FROM Admin WHERE admin_id = ?"
        result = db.fetch_one(query, (admin_id,))
        return result and result["total"] > 0

    def log_action(self, admin_id, action_type, target_table,
                   target_id=None, reason=None):
        """
        Ghi một bản ghi vào Admin_log
        Trả về: (success: bool, message: str)
        """

        # 1️⃣ Validate admin
        if not self._admin_exists(admin_id):
            return False, "Admin không tồn tại."

        # 2️⃣ Validate action type
        if action_type not in self.VALID_ACTION_TYPES:
            return False, f"Action type '{action_type}' không hợp lệ."

        created_at = datetime.now()
        formatted_target_id = str(target_id) if target_id is not None else None

        query = """
            INSERT INTO Admin_log
            (admin_id, action_type, target_table, target_id, reason, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        try:
            success = db.execute_query(
                query,
                (admin_id, action_type, target_table,
                 formatted_target_id, reason, created_at)
            )

            if not success:
                return False, "Không thể ghi log vào cơ sở dữ liệu."

            return True, "Ghi log thành công."

        except Exception as e:
            # Logger không nên làm crash hệ thống
            print(f"[LOGGER ERROR] {e}")
            return False, "Lỗi hệ thống khi ghi log."

    @staticmethod
    def get_logs_by_admin(admin_id):
        """Lấy lịch sử hoạt động của 1 Admin cụ thể"""
        query = """
            SELECT *
            FROM Admin_log
            WHERE admin_id = ?
            ORDER BY created_at DESC
        """
        return db.fetch_all(query, (admin_id,))

    @staticmethod
    def get_all_logs():
        """Lấy toàn bộ lịch sử hoạt động"""
        query = """
            SELECT AL.*, A.full_name
            FROM Admin_log AL
            JOIN Admin A ON AL.admin_id = A.admin_id
            ORDER BY AL.created_at DESC
        """
        return db.fetch_all(query)