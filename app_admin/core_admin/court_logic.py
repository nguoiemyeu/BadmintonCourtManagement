from shared.database.db_manager import db
from shared.entities.court import Court
from app_admin.core_admin.admin_logger import AdminLogger
from datetime import datetime


class CourtLogic:

    # Admin chỉ được phép đổi giữa 2 trạng thái này
    ADMIN_ALLOWED_STATUSES = {"AVAILABLE", "MAINTENANCE"}

    # Những booking được xem là đang chiếm slot
    ACTIVE_BOOKING_STATUSES = {"PENDING_PAYMENT", "PAID"}

    def __init__(self):
        self.logger = AdminLogger()

    # ==============================
    # LẤY DANH SÁCH SÂN
    # ==============================

    def get_all_courts(self):
        query = "SELECT * FROM Court ORDER BY court_id"
        results = db.fetch_all(query)
        return [Court(**row) for row in results]

    def get_court_by_id(self, court_id):
        result = db.fetch_one(
            "SELECT * FROM Court WHERE court_id = ?",
            (court_id,)
        )
        return Court(**result) if result else None

    # ==============================
    # THÊM SÂN MỚI
    # ==============================

    def add_court(self, admin_id, court_code):

        # Check trùng mã sân
        exists = db.fetch_one(
            "SELECT COUNT(*) as total FROM Court WHERE court_code = ?",
            (court_code,)
        )

        if exists and exists["total"] > 0:
            return False, f"Mã sân '{court_code}' đã tồn tại."

        success = db.execute_query(
            "INSERT INTO Court (court_code, status) VALUES (?, 'AVAILABLE')",
            (court_code,)
        )

        if not success:
            return False, "Lỗi khi lưu vào CSDL."

        # Lấy ID sân vừa tạo
        new_court = db.fetch_one(
            "SELECT court_id FROM Court WHERE court_code = ?",
            (court_code,)
        )

        # Ghi log (không làm fail nghiệp vụ nếu logger lỗi)
        self.logger.log_action(
            admin_id,
            "CREATE",
            "Court",
            new_court["court_id"],
            f"Thêm sân mới: {court_code}"
        )

        return True, "Thêm sân thành công."

    # ==============================
    # CẬP NHẬT TRẠNG THÁI SÂN
    # ==============================

    def update_court_status(self, admin_id, court_id, new_status, reason=None):

        # 1️⃣ Validate trạng thái
        if new_status not in self.ADMIN_ALLOWED_STATUSES:
            return False, "Trạng thái không hợp lệ cho Admin."

        court = self.get_court_by_id(court_id)
        if not court:
            return False, "Không tìm thấy sân."

        current_status = court.status

        if current_status == new_status:
            return False, "Sân đã ở trạng thái này rồi."

        # 2️⃣ Không cho bảo trì nếu có booking tương lai
        if new_status == "MAINTENANCE":
            if self.has_future_active_booking(court_id):
                return False, "Không thể bảo trì vì sân đang có lịch đặt trong tương lai."

        # 3️⃣ Update DB
        success = db.execute_query(
            "UPDATE Court SET status = ? WHERE court_id = ?",
            (new_status, court_id)
        )

        if not success:
            return False, "Lỗi hệ thống khi cập nhật trạng thái."

        # 4️⃣ Ghi log
        self.logger.log_action(
            admin_id,
            "UPDATE_STATUS",
            "Court",
            court_id,
            reason if reason else f"Đổi từ {current_status} sang {new_status}"
        )

        return True, "Cập nhật thành công."

    # ==============================
    # KIỂM TRA BOOKING TƯƠNG LAI
    # ==============================

    def has_future_active_booking(self, court_id):

        query = """
        SELECT COUNT(*) AS total
        FROM Booking_Detail bd
        JOIN Booking b ON bd.booking_id = b.booking_id
        WHERE bd.court_id = ?
          AND b.status IN ('PENDING_PAYMENT', 'PAID')
          AND bd.start_time > ?
        """

        result = db.fetch_one(query, (court_id, datetime.now()))

        return result and result["total"] > 0