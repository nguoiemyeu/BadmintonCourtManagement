from shared.database.db_manager import db
from app_admin.core_admin.admin_logger import AdminLogger
from datetime import datetime

class CourtLogic:
    # Trạng thái sân mà admin được phép chuyển (có thể chuyển thủ công)
    ADMIN_ALLOWED_STATUSES = {"Available", "Booked", "Maintenance"}

    # Trạng thái booking được coi là đang hoạt động (có hiệu lực)
    ACTIVE_BOOKING_STATUSES = {"Pending", "Confirmed"}

    def __init__(self):
        self.logger = AdminLogger()

    def get_all_courts(self):
        query = "SELECT court_id, court_code, status FROM Court ORDER BY court_id"
        return db.fetch_all(query)

    def get_court_by_id(self, court_id):
        return db.fetch_one(
            "SELECT court_id, court_code, status FROM Court WHERE court_id = ?",
            (court_id,)
        )

    def get_filtered_courts(self, search_text="", status_filter="Tất cả"):
        query = "SELECT court_id, court_code, status FROM Court WHERE 1=1"
        params = []

        if search_text:
            query += " AND court_code LIKE ?"
            params.append(f"%{search_text}%")

        if status_filter != "Tất cả":
            # Ánh xạ từ tiếng Việt sang giá trị DB
            status_map = {
                "Trống": "Available",
                "Đã đặt": "Booked",
                "Bảo trì": "Maintenance"
            }
            db_status = status_map.get(status_filter)
            if db_status:
                query += " AND status = ?"
                params.append(db_status)

        return db.fetch_all(query, tuple(params))

    def get_available_courts_count(self):
        result = db.fetch_one("SELECT COUNT(*) AS total FROM Court WHERE status = 'Available'")
        return result["total"] if result else 0

    def add_court(self, admin_id, court_code):
        # Kiểm tra trùng mã
        exists = db.fetch_one(
            "SELECT COUNT(*) as total FROM Court WHERE court_code = ?",
            (court_code,)
        )
        if exists and exists["total"] > 0:
            return False, f"Mã sân '{court_code}' đã tồn tại."

        success = db.execute_query(
            "INSERT INTO Court (court_code, status) VALUES (?, 'Available')",
            (court_code,)
        )
        if not success:
            return False, "Lỗi khi lưu vào cơ sở dữ liệu."

        new_court = db.fetch_one(
            "SELECT court_id FROM Court WHERE court_code = ?",
            (court_code,)
        )
        if new_court:
            self.logger.log_action(
                admin_id,
                "CREATE",
                "Court",
                new_court["court_id"],
                f"Thêm sân mới: {court_code}"
            )
        return True, "Thêm sân thành công."

    def update_court_info(self, admin_id, court_id, new_code):
        court = self.get_court_by_id(court_id)
        if not court:
            return False, "Không tìm thấy sân."

        if new_code != court["court_code"]:
            exists = db.fetch_one(
                "SELECT COUNT(*) as total FROM Court WHERE court_code = ? AND court_id != ?",
                (new_code, court_id)
            )
            if exists and exists["total"] > 0:
                return False, f"Mã sân '{new_code}' đã tồn tại ở sân khác."

        success = db.execute_query(
            "UPDATE Court SET court_code = ? WHERE court_id = ?",
            (new_code, court_id)
        )
        if not success:
            return False, "Lỗi hệ thống khi cập nhật thông tin sân."

        self.logger.log_action(
            admin_id,
            "UPDATE",
            "Court",
            court_id,
            f"Cập nhật mã sân: {court['court_code']} → {new_code}"
        )
        return True, "Cập nhật mã sân thành công."

    def update_court_status(self, admin_id, court_id, new_status, reason=None):
        if new_status not in self.ADMIN_ALLOWED_STATUSES:
            return False, "Trạng thái không hợp lệ cho Admin."

        court = self.get_court_by_id(court_id)
        if not court:
            return False, "Không tìm thấy sân."
        if court["status"] == new_status:
            return False, "Sân đã ở trạng thái này rồi."

        # Kiểm tra nếu chuyển sang Maintenance: không được có booking đang hoạt động (Pending, Confirmed)
        if new_status == "Maintenance":
            if self._has_active_or_future_booking(court_id):
                return False, "Không thể bảo trì vì sân đang có lịch đặt (hiện tại hoặc tương lai)."

        success = db.execute_query(
            "UPDATE Court SET status = ? WHERE court_id = ?",
            (new_status, court_id)
        )
        if not success:
            return False, "Lỗi hệ thống khi cập nhật trạng thái."

        log_reason = reason if reason else f"Đổi từ {court['status']} sang {new_status}"
        self.logger.log_action(admin_id, "UPDATE_STATUS", "Court", court_id, log_reason)
        return True, "Cập nhật trạng thái thành công."

    def delete_court(self, admin_id, court_id):
        court = self.get_court_by_id(court_id)
        if not court:
            return False, "Không tìm thấy sân."

        # Kiểm tra xem có bất kỳ booking_detail nào tham chiếu đến sân này không
        # (kể cả booking cũ đã hủy hoặc hoàn thành) vì ràng buộc khóa ngoại
        result = db.fetch_one(
            "SELECT COUNT(*) AS total FROM Booking_Detail WHERE court_id = ?",
            (court_id,)
        )
        if result and result["total"] > 0:
            return False, "Không thể xóa sân vì đã có lịch đặt liên quan (kể cả trong quá khứ)."

        # Thực hiện xóa
        success = db.execute_query("DELETE FROM Court WHERE court_id = ?", (court_id,))
        if not success:
            # In lỗi chi tiết ra console để debug
            print(f"LỖI: Không thể xóa sân ID {court_id} từ database.")
            return False, "Lỗi hệ thống khi xóa sân. Vui lòng kiểm tra log."

        # Ghi log thành công
        self.logger.log_action(
            admin_id,
            "DELETE",
            "Court",
            court_id,
            f"Xóa sân: {court['court_code']}"
        )
        return True, "Xóa sân thành công."

    def _has_active_or_future_booking(self, court_id):
        now = datetime.now()
        query = """
        SELECT COUNT(*) AS total
        FROM Booking_Detail bd
        JOIN Booking b ON bd.booking_id = b.booking_id
        WHERE bd.court_id = ?
          AND b.status IN ({})
          AND (
              bd.start_time > ?
              OR (bd.start_time <= ? AND bd.end_time > ?)
          )
        """.format(','.join('?' for _ in self.ACTIVE_BOOKING_STATUSES))
        params = [court_id] + list(self.ACTIVE_BOOKING_STATUSES) + [now, now, now]
        result = db.fetch_one(query, tuple(params))
        return result and result["total"] > 0

    def update_court_status_based_on_bookings(self, court_id):
        """
        Cập nhật trạng thái court dựa trên các booking_detail hiện tại.
        Nếu có ít nhất một booking_detail với booking có status 'Pending' hoặc 'Confirmed'
        thì court ở trạng thái 'Booked', ngược lại là 'Available'.
        (Không tự động chuyển từ Maintenance)
        """
        # Lấy trạng thái hiện tại
        court = self.get_court_by_id(court_id)
        if not court:
            return False, "Không tìm thấy sân"

        # Nếu đang Maintenance thì không tự động thay đổi
        if court['status'] == 'Maintenance':
            return True, "Sân đang bảo trì, giữ nguyên"

        # Kiểm tra booking đang hoạt động
        query = """
                SELECT COUNT(*) as total
                FROM Booking_Detail bd
                         JOIN Booking b ON bd.booking_id = b.booking_id
                WHERE bd.court_id = ? \
                  AND b.status IN ('Pending', 'Confirmed') \
                """
        result = db.fetch_one(query, (court_id,))
        has_active = result and result['total'] > 0

        new_status = 'Booked' if has_active else 'Available'
        if new_status != court['status']:
            success = db.execute_query(
                "UPDATE Court SET status = ? WHERE court_id = ?",
                (new_status, court_id)
            )
            if success:
                return True, f"Cập nhật trạng thái sân thành {new_status}"
            else:
                return False, "Lỗi cập nhật"
        return True, "Không thay đổi"