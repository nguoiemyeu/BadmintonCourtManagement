# app_admin/core_admin/admin_logic.py

from shared.database.db_manager import db
from app_admin.core_admin.admin_logger import AdminLogger
from datetime import datetime

class AdminLogic:

    # Trạng thái booking hợp lệ (khớp với CSDL)
    VALID_BOOKING_STATUSES = {"Pending", "Confirmed", "Cancelled", "Completed"}

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
                       ct.court_id, 
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
    # UPDATE BOOKING STATUS
    # =====================================

    def update_booking_status(self, admin_id, booking_id, new_status, reason=None):
        # Kiểm tra trạng thái mới có hợp lệ không
        if new_status not in self.VALID_BOOKING_STATUSES:
            return False, "Trạng thái không hợp lệ."

        booking = self.get_booking_by_id(booking_id)
        if not booking:
            return False, "Không tìm thấy booking."

        current_status = booking["status"]

        if current_status == new_status:
            return False, "Booking đã ở trạng thái này."

        # Không cho thay đổi nếu đã Cancelled
        if current_status == "Cancelled":
            return False, "Booking đã bị hủy, không thể thay đổi."

        # Không cho quay ngược từ Confirmed về Pending
        if current_status == "Confirmed" and new_status == "Pending":
            return False, "Không thể quay lại trạng thái chưa thanh toán."

        # Thực hiện cập nhật
        success = db.execute_query(
            "UPDATE Booking SET status = ? WHERE booking_id = ?",
            (new_status, booking_id)
        )

        if not success:
            return False, "Lỗi khi cập nhật booking."

        # Ghi log
        self.logger.log_action(
            admin_id,
            "UPDATE",
            "Booking",
            booking_id,
            reason if reason else f"Đổi từ {current_status} sang {new_status}"
        )

        return True, "Cập nhật booking thành công."

    # =====================================
    # PAYMENT MANAGEMENT
    # =====================================

    def get_payment_by_booking(self, booking_id):
        return db.fetch_one(
            "SELECT * FROM Payment WHERE booking_id = ?",
            (booking_id,)
        )

    def confirm_payment(self, admin_id, booking_id):
        # Kiểm tra booking
        booking = self.get_booking_by_id(booking_id)
        if not booking:
            return False, "Không tìm thấy booking."

        if booking["status"] != "Pending":
            return False, "Chỉ xác nhận thanh toán cho đơn đang chờ thanh toán."

        # Kiểm tra payment
        payment = self.get_payment_by_booking(booking_id)
        if not payment:
            return False, "Chưa có giao dịch thanh toán."

        if payment["status"] == "Success":
            return False, "Thanh toán đã được xác nhận trước đó."

        conn = db.get_connection()
        if not conn:
            return False, "Không thể kết nối cơ sở dữ liệu."

        try:
            cursor = conn.cursor()

            # Cập nhật Payment -> Success
            cursor.execute(
                """
                UPDATE Payment
                SET status = 'Success',
                    payment_date = ?
                WHERE booking_id = ?
                """,
                (datetime.now(), booking_id)
            )

            if cursor.rowcount == 0:
                raise Exception("Không cập nhật được Payment.")

            # Cập nhật Booking -> Confirmed
            cursor.execute(
                """
                UPDATE Booking
                SET status = 'Confirmed'
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

        # Ghi log
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
            "SELECT SUM(total_amount) AS total_revenue FROM Booking WHERE status = 'Confirmed'"
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
        WHERE status = 'Confirmed'
          AND MONTH(booking_date) = MONTH(GETDATE())
          AND YEAR(booking_date) = YEAR(GETDATE())
        """
        result = db.fetch_one(query)
        return result["monthly_revenue"] if result and result["monthly_revenue"] else 0

    def get_booking_status_stats(self):
        return db.fetch_all(
            "SELECT status, COUNT(*) as count FROM Booking GROUP BY status"
        )

    def get_today_revenue(self):
        query = """
        SELECT SUM(total_amount) AS today_revenue
        FROM Booking
        WHERE status = 'Confirmed'
          AND CAST(booking_date AS DATE) = CAST(GETDATE() AS DATE)
        """
        result = db.fetch_one(query)
        return result["today_revenue"] if result and result["today_revenue"] else 0

    def get_today_bookings(self):
        query = "SELECT COUNT(*) AS total FROM Booking WHERE CAST(booking_date AS DATE) = CAST(GETDATE() AS DATE)"
        result = db.fetch_one(query)
        return result["total"] if result else 0

    def get_revenue_last_7_days(self):
        query = """
        SELECT CAST(booking_date AS DATE) as booking_date, SUM(total_amount) as daily_revenue
        FROM Booking
        WHERE status = 'Confirmed'
          AND booking_date >= DATEADD(day, -7, GETDATE())
        GROUP BY CAST(booking_date AS DATE)
        ORDER BY booking_date ASC
        """
        return db.fetch_all(query)

    def get_latest_bookings(self, limit=5):
        query = f"""
        SELECT TOP {limit} b.booking_id, c.full_name, b.booking_date, b.status, b.total_amount
        FROM Booking b
        JOIN Customer c ON b.customer_id = c.customer_id
        ORDER BY b.booking_date DESC
        """
        return db.fetch_all(query)

    def get_admin_info(self, admin_id):
        query = "SELECT full_name FROM Admin WHERE admin_id = ?"
        result = db.fetch_one(query, (admin_id,))
        return result["full_name"] if result else "Admin"

    # =====================================
    # SEARCH & FILTER BOOKINGS
    # =====================================

    def search_bookings(self, keyword="", from_date=None, to_date=None, status="Tất cả"):
        status_map = {
            "Chờ thanh toán": "Pending",
            "Đã thanh toán": "Confirmed",
            "Hoàn thành": "Completed",
            "Đã hủy": "Cancelled"
        }
        db_status = status_map.get(status) if status != "Tất cả" else None

        query = """
                SELECT b.booking_id, c.full_name, b.booking_date, b.total_amount, b.status
                FROM Booking b
                         JOIN Customer c ON b.customer_id = c.customer_id
                WHERE 1 = 1 \
                """
        params = []

        if keyword:
            query += " AND (CAST(b.booking_id AS VARCHAR) LIKE ? OR c.full_name LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])

        if from_date:
            query += " AND b.booking_date >= ?"
            params.append(from_date)

        if to_date:
            # Đảm bảo to_date là datetime, lấy đến cuối ngày
            to_date_end = datetime.combine(to_date.date(), datetime.max.time())
            query += " AND b.booking_date <= ?"
            params.append(to_date_end)

        if db_status:
            query += " AND b.status = ?"
            params.append(db_status)

        query += " ORDER BY b.booking_date DESC"

        # Debug: in query và params
        print(f"DEBUG SQL: {query}")
        print(f"DEBUG Params: {params}")

        return db.fetch_all(query, params)
    # =====================================
    # HELPER METHODS FOR DIALOG
    # =====================================

    def get_customer_by_booking(self, booking_id):
        """Lấy thông tin khách hàng từ booking_id"""
        query = """
        SELECT c.*
        FROM Customer c
        JOIN Booking b ON c.customer_id = b.customer_id
        WHERE b.booking_id = ?
        """
        return db.fetch_one(query, (booking_id,))

    def get_promotion_by_booking(self, booking_id):
        """Lấy thông tin khuyến mãi áp dụng cho booking"""
        query = """
        SELECT p.*
        FROM Promotion p
        JOIN Booking b ON p.promotion_id = b.promotion_id
        WHERE b.booking_id = ?
        """
        return db.fetch_one(query, (booking_id,))

    def create_booking(self, admin_id, customer_id, promotion_id, details, total_amount):
        conn = db.get_connection()
        if not conn:
            return False, "Không thể kết nối database", None

        try:
            cursor = conn.cursor()
            # Thêm booking
            cursor.execute("""
                           INSERT INTO Booking (customer_id, promotion_id, booking_date, status, total_amount)
                           VALUES (?, ?, GETDATE(), 'Pending', ?)
                           """, (customer_id, promotion_id, total_amount))
            conn.commit()
            cursor.execute("SELECT @@IDENTITY AS id")
            booking_id = cursor.fetchone()[0]

            # Thêm từng chi tiết
            for det in details:
                start = det['start'].toPyDateTime()
                end = det['end'].toPyDateTime()
                cursor.execute("""
                               INSERT INTO Booking_Detail (booking_id, court_id, start_time, end_time, price_per_hour, subtotal)
                               VALUES (?, ?, ?, ?, ?, ?)
                               """, (booking_id, det['court_id'], start, end, det['price'], det['subtotal']))

                # Cập nhật trạng thái court thành Booked nếu đang Available
                cursor.execute("""
                               UPDATE Court
                               SET status = 'Booked'
                               WHERE court_id = ?
                                 AND status = 'Available'
                               """, (det['court_id'],))

            # Tạo payment
            cursor.execute("""
                           INSERT INTO Payment (booking_id, amount, payment_method, payment_date, status)
                           VALUES (?, ?, 'Cash', GETDATE(), 'Pending')
                           """, (booking_id, total_amount))

            conn.commit()

            # Ghi log
            self.logger.log_action(admin_id, "CREATE", "Booking", booking_id, f"Tạo đơn mới cho khách {customer_id}")
            return True, "Tạo đơn thành công", booking_id

        except Exception as e:
            conn.rollback()
            return False, f"Lỗi: {str(e)}", None
        finally:
            conn.close()

    def add_customer(self, full_name, phone_number):
        """Thêm khách hàng mới"""
        # Kiểm tra phone đã tồn tại?
        existing = db.fetch_one("SELECT customer_id FROM Customer WHERE phone_number = ?", (phone_number,))
        if existing:
            return False, "Số điện thoại đã tồn tại."
        success = db.execute_query(
            "INSERT INTO Customer (full_name, phone_number) VALUES (?, ?)",
            (full_name, phone_number)
        )
        if success:
            return True, "Thêm khách hàng thành công."
        else:
            return False, "Lỗi khi thêm khách hàng."

    def get_all_customers(self):
        return db.fetch_all("SELECT customer_id, full_name, phone_number FROM Customer ORDER BY full_name")

