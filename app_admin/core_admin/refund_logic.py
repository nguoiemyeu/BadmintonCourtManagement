from shared.database.db_manager import db
from app_admin.core_admin.admin_logger import AdminLogger
from datetime import datetime, timedelta


class RefundLogic:

    # Trạng thái booking cho phép hoàn tiền: đã thanh toán (Confirmed)
    VALID_BOOKING_STATUS_FOR_REFUND = "Confirmed"

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
        if isinstance(dt_value, datetime):
            return dt_value
        if isinstance(dt_value, str):
            try:
                return datetime.fromisoformat(dt_value)
            except Exception:
                return None
        return None

    # ===============================
    # REFUND PROCESS
    # ===============================

    def process_refund(self, admin_id, booking_id, reason):

        # 1️⃣ Kiểm tra booking
        booking = self._get_booking(booking_id)
        if not booking:
            return False, "Không tìm thấy booking."

        if booking["status"] != self.VALID_BOOKING_STATUS_FOR_REFUND:
            return False, "Chỉ hoàn tiền cho booking đã thanh toán (Confirmed)."

        # 2️⃣ Kiểm tra payment
        payment = self._get_payment(booking_id)
        if not payment:
            return False, "Không tìm thấy thông tin thanh toán."

        if payment["status"] != "Success":  # Trạng thái payment thành công
            return False, "Chỉ hoàn tiền cho giao dịch đã hoàn tất."

        # 3️⃣ Không cho refund 2 lần
        if self._refund_exists(booking_id):
            return False, "Booking này đã được hoàn tiền trước đó."

        # 4️⃣ Kiểm tra thời gian 3 giờ (nếu cần)
        earliest_time_raw = self._get_earliest_start_time(booking_id)
        if earliest_time_raw:
            earliest_time = self._parse_datetime(earliest_time_raw)
            if earliest_time:
                now = datetime.now()
                if earliest_time - now < timedelta(hours=3):
                    return False, "Chỉ được hoàn tiền nếu hủy trước giờ sử dụng ít nhất 3 giờ."

        refund_amount = booking["total_amount"]

        # 5. Transaction
        conn = db.get_connection()
        if not conn:
            return False, "Không thể kết nối cơ sở dữ liệu."

        try:
            cursor = conn.cursor()

            # Insert Refund record
            cursor.execute(
                """
                INSERT INTO Refund (booking_id, refund_amount, refund_date, reason)
                VALUES (?, ?, ?, ?)
                """,
                (booking_id, refund_amount, datetime.now(), reason)
            )

            # Update Booking -> Cancelled
            cursor.execute(
                "UPDATE Booking SET status = 'Cancelled' WHERE booking_id = ?",
                (booking_id,)
            )
            if cursor.rowcount == 0:
                raise Exception("Không cập nhật được Booking.")

            # Update Payment -> Refunded (có thể thêm trạng thái mới, nếu chưa có thì tạo)
            # Trong CSDL, Payment status có thể là 'Pending', 'Success', 'Failed'
            # Ta có thể thêm 'Refunded' vào check constraint, hoặc tạm thời dùng 'Failed'
            # Tốt nhất nên thêm 'Refunded' vào ràng buộc. Ở đây giả sử đã có 'Refunded'.
            cursor.execute(
                "UPDATE Payment SET status = 'Refunded' WHERE booking_id = ?",
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

        # Ghi log
        self.logger.log_action(
            admin_id=admin_id,
            action_type="REFUND",
            target_table="Booking",
            target_id=booking_id,
            reason=f"Hoàn tiền {refund_amount} VNĐ - {reason}"
        )

        return True, f"Hoàn tiền thành công: {refund_amount} VNĐ."