# app_admin/core_admin/admin_logic.py

from shared.database.db_manager import db
from app_admin.core_admin.admin_logger import AdminLogger
from datetime import datetime


class AdminLogic:

    VALID_BOOKING_STATUSES = {"PENDING_PAYMENT", "PAID", "CANCELLED"}

    def __init__(self):
        self.logger = AdminLogger()

    # =====================================
    # BOOKING MANAGEMENT
    # =====================================

    def get_all_bookings(self):
        query = """
        SELECT b.booking_id, c.full_name, b.booking_date, b.status, b.total_amount,
               (SELECT COUNT(*) FROM Booking_Detail WHERE booking_id = b.booking_id) as total_courts
        FROM Booking b
        JOIN Customer c ON b.customer_id = c.customer_id
        ORDER BY b.booking_date DESC
        """
        return db.fetch_all(query)

    def get_booking_details(self, booking_id):
        query = """
        SELECT bd.booking_detail_id,
               ct.court_code,
               bd.start_time,
               bd.end_time,
               bd.price_per_hour,
               bd.subtotal
        FROM Booking_Detail bd
        JOIN Court ct ON bd.court_id = ct.court_id
        WHERE bd.booking_id = ?
        """
        return db.fetch_all(query, (booking_id,))

    def get_booking_by_id(self, booking_id):
        return db.fetch_one(
            "SELECT * FROM Booking WHERE booking_id = ?",
            (booking_id,)
        )

    # =====================================
    # UPDATE BOOKING STATUS (SIẾT CHẶT LUỒNG)
    # =====================================

    def update_booking_status(self, admin_id, booking_id, new_status, reason=None):

        if new_status not in self.VALID_BOOKING_STATUSES:
            return False, "Trạng thái không hợp lệ."

        booking = self.get_booking_by_id(booking_id)
        if not booking:
            return False, "Không tìm thấy booking."

        current_status = booking["status"]

        if current_status == new_status:
            return False, "Booking đã ở trạng thái này."

        # Không cho thay đổi nếu đã CANCELLED
        if current_status == "CANCELLED":
            return False, "Booking đã bị hủy, không thể thay đổi."

        # Không cho quay ngược trạng thái
        if current_status == "PAID" and new_status == "PENDING_PAYMENT":
            return False, "Không thể quay lại trạng thái chưa thanh toán."

        # Update DB
        success = db.execute_query(
            "UPDATE Booking SET status = ? WHERE booking_id = ?",
            (new_status, booking_id)
        )

        if not success:
            return False, "Lỗi khi cập nhật booking."

        # Log (không làm fail nghiệp vụ nếu logger lỗi)
        self.logger.log_action(
            admin_id,
            "UPDATE",
            "Booking",
            booking_id,
            reason if reason else f"Đổi từ {current_status} sang {new_status}"
        )

        return True, "Cập nhật booking thành công."

    # =====================================
    # PAYMENT MANAGEMENT (TRANSACTION CHUẨN)
    # =====================================

    def get_payment_by_booking(self, booking_id):
        return db.fetch_one(
            "SELECT * FROM Payment WHERE booking_id = ?",
            (booking_id,)
        )

    def confirm_payment(self, admin_id, booking_id):

        # 1️⃣ Kiểm tra booking
        booking = self.get_booking_by_id(booking_id)
        if not booking:
            return False, "Không tìm thấy booking."

        if booking["status"] != "PENDING_PAYMENT":
            return False, "Chỉ xác nhận thanh toán cho booking chưa thanh toán."

        # 2️⃣ Kiểm tra payment
        payment = self.get_payment_by_booking(booking_id)
        if not payment:
            return False, "Chưa có giao dịch thanh toán."

        if payment["status"] == "COMPLETED":
            return False, "Thanh toán đã được xác nhận trước đó."

        conn = db.get_connection()
        if not conn:
            return False, "Không thể kết nối cơ sở dữ liệu."

        try:
            cursor = conn.cursor()

            # Update Payment
            cursor.execute(
                """
                UPDATE Payment
                SET status = 'COMPLETED',
                    payment_date = ?
                WHERE booking_id = ?
                """,
                (datetime.now(), booking_id)
            )

            if cursor.rowcount == 0:
                raise Exception("Không cập nhật được Payment.")

            # Update Booking
            cursor.execute(
                """
                UPDATE Booking
                SET status = 'PAID'
                WHERE booking_id = ?
                """,
                (booking_id,)
            )

            if cursor.rowcount == 0:
                raise Exception("Không cập nhật được Booking.")

            conn.commit()

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi hệ thống: {e}"

        finally:
            conn.close()

        # Log sau commit thành công
        self.logger.log_action(
            admin_id,
            "UPDATE",
            "Payment",
            payment["payment_id"],
            "Xác nhận thanh toán"
        )

        return True, "Xác nhận thanh toán thành công."

    # =====================================
    # PROMOTION MANAGEMENT
    # =====================================

    def get_all_promotions(self):
        return db.fetch_all(
            "SELECT * FROM Promotion ORDER BY start_date DESC"
        )

    def deactivate_promotion(self, admin_id, promotion_id):

        success = db.execute_query(
            "UPDATE Promotion SET is_active = 0 WHERE promotion_id = ?",
            (promotion_id,)
        )

        if not success:
            return False, "Không thể cập nhật khuyến mãi."

        self.logger.log_action(
            admin_id,
            "UPDATE_STATUS",
            "Promotion",
            promotion_id,
            "Tắt khuyến mãi"
        )

        return True, "Đã tắt khuyến mãi."

    # =====================================
    # DASHBOARD STATS
    # =====================================

    def get_total_revenue(self):
        result = db.fetch_one(
            "SELECT SUM(total_amount) AS total_revenue FROM Booking WHERE status = 'PAID'"
        )
        return result["total_revenue"] if result and result["total_revenue"] else 0

    def get_total_bookings(self):
        result = db.fetch_one("SELECT COUNT(*) AS total FROM Booking")
        return result["total"] if result else 0

    def get_total_customers(self):
        result = db.fetch_one("SELECT COUNT(*) AS total FROM Customer")
        return result["total"] if result else 0

    def get_monthly_revenue(self):
        query = """
        SELECT SUM(total_amount) AS monthly_revenue
        FROM Booking
        WHERE status = 'PAID'
          AND MONTH(booking_date) = MONTH(GETDATE())
          AND YEAR(booking_date) = YEAR(GETDATE())
        """
        result = db.fetch_one(query)
        return result["monthly_revenue"] if result and result["monthly_revenue"] else 0

    def get_booking_status_stats(self):
        return db.fetch_all(
            "SELECT status, COUNT(*) as count FROM Booking GROUP BY status"
        )