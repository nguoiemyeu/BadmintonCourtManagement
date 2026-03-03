from shared.database.db_manager import db
from app_admin.core_admin.admin_logger import AdminLogger
from datetime import datetime, timedelta


class RefundLogic:

    VALID_BOOKING_STATUS_FOR_REFUND = "PAID"

    def __init__(self):
        self.logger = AdminLogger()

    # ===============================
    # PRIVATE HELPERS
    # ===============================

    def _get_booking(self, booking_id):
        return db.fetch_one(
            "SELECT * FROM Booking WHERE booking_id = ?",
            (booking_id,)
        )

    def _get_payment(self, booking_id):
        return db.fetch_one(
            "SELECT * FROM Payment WHERE booking_id = ?",
            (booking_id,)
        )

    def _refund_exists(self, booking_id):
        result = db.fetch_one(
            "SELECT COUNT(*) AS total FROM Refund WHERE booking_id = ?",
            (booking_id,)
        )
        return result and result["total"] > 0

    def _get_earliest_start_time(self, booking_id):
        result = db.fetch_one(
            """
            SELECT MIN(start_time) AS earliest_time
            FROM Booking_Detail
            WHERE booking_id = ?
            """,
            (booking_id,)
        )
        return result["earliest_time"] if result else None

    def _parse_datetime(self, dt_value):
        """
        Chuyển datetime từ DB về datetime object an toàn
        """
        if isinstance(dt_value, datetime):
            return dt_value

        if isinstance(dt_value, str):
            try:
                # SQLite format thường là: 'YYYY-MM-DD HH:MM:SS'
                return datetime.fromisoformat(dt_value)
            except Exception:
                return None

        return None

    # ===============================
    # REFUND PROCESS (CHUẨN TÀI CHÍNH)
    # ===============================

    def process_refund(self, admin_id, booking_id, reason):

        # 1️⃣ Kiểm tra booking
        booking = self._get_booking(booking_id)
        if not booking:
            return False, "Không tìm thấy booking."

        if booking["status"] != self.VALID_BOOKING_STATUS_FOR_REFUND:
            return False, "Chỉ hoàn tiền cho booking đã thanh toán (PAID)."

        # 2️⃣ Kiểm tra payment
        payment = self._get_payment(booking_id)
        if not payment:
            return False, "Không tìm thấy thông tin thanh toán."

        if payment["status"] != "COMPLETED":
            return False, "Chỉ hoàn tiền cho giao dịch đã hoàn tất."

        # 3️⃣ Không cho refund 2 lần
        if self._refund_exists(booking_id):
            return False, "Booking này đã được hoàn tiền trước đó."

        # 4️⃣ Kiểm tra thời gian 3 giờ
        earliest_time_raw = self._get_earliest_start_time(booking_id)
        if not earliest_time_raw:
            return False, "Không tìm thấy chi tiết đặt sân."

        earliest_time = self._parse_datetime(earliest_time_raw)
        if not earliest_time:
            return False, "Lỗi định dạng thời gian đặt sân."

        now = datetime.now()

        if earliest_time - now < timedelta(hours=3):
            return False, "Chỉ được hoàn tiền nếu hủy trước giờ sử dụng ít nhất 3 giờ."

        refund_amount = booking["total_amount"]

        # ===============================
        # 5️⃣ TRANSACTION BẮT BUỘC
        # ===============================

        conn = db.get_connection()
        if not conn:
            return False, "Không thể kết nối cơ sở dữ liệu."

        try:
            cursor = conn.cursor()

            # Insert Refund record
            cursor.execute(
                """
                INSERT INTO Refund
                (booking_id, refund_amount, refund_date, reason)
                VALUES (?, ?, ?, ?)
                """,
                (booking_id, refund_amount, now, reason)
            )

            # Update Booking -> CANCELLED
            cursor.execute(
                """
                UPDATE Booking
                SET status = 'CANCELLED'
                WHERE booking_id = ?
                """,
                (booking_id,)
            )

            if cursor.rowcount == 0:
                raise Exception("Không cập nhật được Booking.")

            # Update Payment -> REFUNDED
            cursor.execute(
                """
                UPDATE Payment
                SET status = 'REFUNDED'
                WHERE booking_id = ?
                """,
                (booking_id,)
            )

            if cursor.rowcount == 0:
                raise Exception("Không cập nhật được Payment.")

            conn.commit()

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Lỗi hệ thống: {e}"

        finally:
            conn.close()

        # ===============================
        # 6️⃣ GHI LOG (KHÔNG ẢNH HƯỞNG NGHIỆP VỤ)
        # ===============================

        self.logger.log_action(
            admin_id=admin_id,
            action_type="REFUND",
            target_table="Booking",
            target_id=booking_id,
            reason=f"Hoàn tiền {refund_amount} VNĐ - {reason}"
        )

        return True, f"Hoàn tiền thành công: {refund_amount} VNĐ."