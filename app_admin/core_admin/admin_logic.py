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
        if new_status not in self.VALID_BOOKING_STATUSES:
            return False, "Trạng thái không hợp lệ."

        booking = self.get_booking_by_id(booking_id)
        if not booking:
            return False, "Không tìm thấy booking."

        current_status = booking["status"]

        if current_status == new_status:
            return False, "Booking đã ở trạng thái này."

        if current_status == "Cancelled":
            return False, "Booking đã bị hủy, không thể thay đổi."

        if current_status == "Confirmed" and new_status == "Pending":
            return False, "Không thể quay lại trạng thái chưa thanh toán."

        success = db.execute_query(
            "UPDATE Booking SET status = ? WHERE booking_id = ?",
            (new_status, booking_id)
        )

        if not success:
            return False, "Lỗi khi cập nhật booking."

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
        booking = self.get_booking_by_id(booking_id)
        if not booking:
            return False, "Không tìm thấy booking."

        if booking["status"] != "Pending":
            return False, "Chỉ xác nhận thanh toán cho đơn đang chờ thanh toán."

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
        WHERE 1 = 1
        """
        params = []

        if keyword:
            query += " AND (CAST(b.booking_id AS VARCHAR) LIKE ? OR c.full_name LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])

        if from_date:
            query += " AND b.booking_date >= ?"
            params.append(from_date)

        if to_date:
            to_date_end = datetime.combine(to_date.date(), datetime.max.time())
            query += " AND b.booking_date <= ?"
            params.append(to_date_end)

        if db_status:
            query += " AND b.status = ?"
            params.append(db_status)

        query += " ORDER BY b.booking_date DESC"
        return db.fetch_all(query, params)

    # =====================================
    # HELPER METHODS FOR DIALOGS
    # =====================================

    def get_customer_by_booking(self, booking_id):
        query = """
        SELECT c.*
        FROM Customer c
        JOIN Booking b ON c.customer_id = b.customer_id
        WHERE b.booking_id = ?
        """
        return db.fetch_one(query, (booking_id,))

    def get_promotion_by_booking(self, booking_id):
        query = """
        SELECT p.*
        FROM Promotion p
        JOIN Booking b ON p.promotion_id = b.promotion_id
        WHERE b.booking_id = ?
        """
        return db.fetch_one(query, (booking_id,))

    # =====================================
    # CREATE BOOKING (with court status update)
    # =====================================

    def create_booking(self, admin_id, customer_id, promotion_id, details, total_amount):
        conn = db.get_connection()
        if not conn:
            return False, "Không thể kết nối database", None

        try:
            cursor = conn.cursor()
            # Insert booking
            cursor.execute("""
                INSERT INTO Booking (customer_id, promotion_id, booking_date, status, total_amount)
                VALUES (?, ?, GETDATE(), 'Pending', ?)
            """, (customer_id, promotion_id, total_amount))
            conn.commit()
            cursor.execute("SELECT @@IDENTITY AS id")
            booking_id = cursor.fetchone()[0]

            # Insert booking details and update court status
            for det in details:
                start = det['start'].toPyDateTime()
                end = det['end'].toPyDateTime()
                cursor.execute("""
                    INSERT INTO Booking_Detail (booking_id, court_id, start_time, end_time, price_per_hour, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (booking_id, det['court_id'], start, end, det['price'], det['subtotal']))

                # Update court to Booked if it was Available
                cursor.execute("""
                    UPDATE Court
                    SET status = 'Booked'
                    WHERE court_id = ? AND status = 'Available'
                """, (det['court_id'],))

            # Create payment record (pending)
            cursor.execute("""
                INSERT INTO Payment (booking_id, amount, payment_method, payment_date, status)
                VALUES (?, ?, 'Cash', GETDATE(), 'Pending')
            """, (booking_id, total_amount))

            conn.commit()

            self.logger.log_action(admin_id, "CREATE", "Booking", booking_id,
                                   f"Tạo đơn mới cho khách {customer_id}")
            return True, "Tạo đơn thành công", booking_id

        except Exception as e:
            conn.rollback()
            return False, f"Lỗi: {str(e)}", None
        finally:
            conn.close()

    def update_completed_bookings(self):
        """
        Cập nhật các đơn đã thanh toán (Confirmed) đã qua thời gian kết thúc thành Completed,
        và chuyển trạng thái sân tương ứng về Available nếu không còn booking nào khác.
        """
        conn = db.get_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            now = datetime.now()
            # Tìm các booking Confirmed có thời gian kết thúc lớn nhất < hiện tại
            cursor.execute("""
                           SELECT b.booking_id
                           FROM Booking b
                           WHERE b.status = 'Confirmed'
                             AND (SELECT MAX(bd.end_time) FROM Booking_Detail bd WHERE bd.booking_id = b.booking_id) < ?
                           """, (now,))
            rows = cursor.fetchall()
            booking_ids = [row[0] for row in rows]
            if not booking_ids:
                return True

            # Cập nhật các booking đó thành Completed
            placeholders = ','.join('?' for _ in booking_ids)
            cursor.execute(f"""
                UPDATE Booking SET status = 'Completed'
                WHERE booking_id IN ({placeholders})
            """, booking_ids)

            # Lấy tất cả court_id từ các booking_detail của các booking này
            cursor.execute(f"""
                SELECT DISTINCT court_id
                FROM Booking_Detail
                WHERE booking_id IN ({placeholders})
            """, booking_ids)
            court_rows = cursor.fetchall()
            court_ids = [row[0] for row in court_rows]

            # Với mỗi court, kiểm tra nếu không còn booking nào đang hoạt động (Pending hoặc Confirmed)
            # có thời gian kết thúc > hiện tại (tức là còn hiệu lực) thì chuyển thành Available
            for court_id in court_ids:
                cursor.execute("""
                               SELECT COUNT(*) as cnt
                               FROM Booking_Detail bd
                                        JOIN Booking b ON bd.booking_id = b.booking_id
                               WHERE bd.court_id = ?
                                 AND b.status IN ('Pending', 'Confirmed')
                                 AND bd.end_time > ?
                               """, (court_id, now))
                result = cursor.fetchone()
                if result[0] == 0:
                    cursor.execute("UPDATE Court SET status = 'Available' WHERE court_id = ?", (court_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"❌ Lỗi cập nhật đơn hoàn thành: {e}")
            return False
        finally:
            conn.close()
    # =====================================
    # CUSTOMER MANAGEMENT
    # =====================================

    def get_all_customers(self):
        """Lấy tất cả khách hàng kèm loại (thành viên hay không)"""
        query = """
        SELECT c.customer_id, c.full_name, c.phone_number, c.created_at,
               CASE WHEN m.customer_id IS NOT NULL THEN N'Thành viên' ELSE N'Khách nhanh' END AS customer_type
        FROM Customer c
        LEFT JOIN Member m ON c.customer_id = m.customer_id
        ORDER BY c.full_name
        """
        return db.fetch_all(query)

    def get_customer_by_id(self, customer_id):
        """Lấy thông tin chi tiết một khách hàng"""
        query = """
        SELECT c.*,
               CASE WHEN m.customer_id IS NOT NULL THEN 1 ELSE 0 END AS is_member,
               m.username, m.register_date, m.status AS member_status
        FROM Customer c
        LEFT JOIN Member m ON c.customer_id = m.customer_id
        WHERE c.customer_id = ?
        """
        return db.fetch_one(query, (customer_id,))

    def add_customer(self, full_name, phone_number):
        """
        Thêm khách hàng mới, trả về (success, message, customer_id)
        """
        conn = db.get_connection()
        if not conn:
            return False, "Không thể kết nối database", None

        try:
            cursor = conn.cursor()
            # Kiểm tra phone đã tồn tại chưa
            cursor.execute("SELECT customer_id FROM Customer WHERE phone_number = ?", (phone_number,))
            if cursor.fetchone():
                return False, "Số điện thoại đã tồn tại.", None

            # Thêm khách hàng
            cursor.execute(
                "INSERT INTO Customer (full_name, phone_number) VALUES (?, ?)",
                (full_name, phone_number)
            )
            conn.commit()

            # Lấy ID vừa tạo (dùng @@IDENTITY để tương thích)
            cursor.execute("SELECT @@IDENTITY AS id")
            row = cursor.fetchone()
            if row and row[0] is not None:
                new_id = int(row[0])
                return True, "Thêm khách hàng thành công.", new_id
            else:
                return False, "Không thể lấy ID khách hàng mới.", None

        except Exception as e:
            conn.rollback()
            return False, f"Lỗi: {str(e)}", None
        finally:
            conn.close()

    def update_customer(self, customer_id, full_name, phone_number):
        existing = db.fetch_one(
            "SELECT customer_id FROM Customer WHERE phone_number = ? AND customer_id != ?",
            (phone_number, customer_id)
        )
        if existing:
            return False, "Số điện thoại đã tồn tại ở khách hàng khác."
        success = db.execute_query(
            "UPDATE Customer SET full_name = ?, phone_number = ? WHERE customer_id = ?",
            (full_name, phone_number, customer_id)
        )
        if success:
            return True, "Cập nhật thành công."
        else:
            return False, "Lỗi khi cập nhật."

    def update_customer(self, customer_id, full_name, phone_number):
        """Cập nhật thông tin khách hàng"""
        # Kiểm tra số điện thoại mới có bị trùng với khách khác không
        existing = db.fetch_one(
            "SELECT customer_id FROM Customer WHERE phone_number = ? AND customer_id != ?",
            (phone_number, customer_id)
        )
        if existing:
            return False, "Số điện thoại đã tồn tại ở khách hàng khác."

        success = db.execute_query(
            "UPDATE Customer SET full_name = ?, phone_number = ? WHERE customer_id = ?",
            (full_name, phone_number, customer_id)
        )
        if success:
            return True, "Cập nhật thông tin thành công."
        else:
            return False, "Lỗi khi cập nhật."

    def delete_customer(self, admin_id, customer_id):
        """
        Xóa khách hàng. Nếu là thành viên, tự động xóa member trước.
        Chỉ cho phép xóa nếu chưa có booking nào.
        """
        conn = db.get_connection()
        if not conn:
            return False, "Không thể kết nối database"

        try:
            cursor = conn.cursor()
            # Kiểm tra booking
            cursor.execute("SELECT COUNT(*) FROM Booking WHERE customer_id = ?", (customer_id,))
            if cursor.fetchone()[0] > 0:
                return False, "Không thể xóa vì khách hàng đã có lịch sử đặt sân."

            # Xóa member trước nếu có
            cursor.execute("DELETE FROM Member WHERE customer_id = ?", (customer_id,))

            # Xóa customer
            cursor.execute("DELETE FROM Customer WHERE customer_id = ?", (customer_id,))
            conn.commit()

            self.logger.log_action(admin_id, "DELETE", "Customer", customer_id, "Xóa khách hàng")
            return True, "Xóa khách hàng thành công."

        except Exception as e:
            conn.rollback()
            return False, f"Lỗi: {str(e)}"
        finally:
            conn.close()

    def search_customers(self, keyword="", customer_type="Tất cả"):
        """
        Tìm kiếm khách hàng theo tên hoặc số điện thoại, và lọc theo loại.
        Trả về danh sách các dict có keys: customer_id, full_name, phone_number, created_at, customer_type, total_bookings
        """
        query = """
                SELECT c.customer_id, \
                       c.full_name, \
                       c.phone_number, \
                       c.created_at,
                       CASE WHEN m.customer_id IS NOT NULL THEN N'Thành viên' ELSE N'Khách nhanh' END AS customer_type,
                       (SELECT COUNT(*) FROM Booking WHERE customer_id = c.customer_id)               AS total_bookings
                FROM Customer c
                         LEFT JOIN Member m ON c.customer_id = m.customer_id
                WHERE 1 = 1 \
                """
        params = []
        if keyword:
            query += " AND (c.full_name LIKE ? OR c.phone_number LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if customer_type == "Thành viên":
            query += " AND m.customer_id IS NOT NULL"
        elif customer_type == "Khách nhanh":
            query += " AND m.customer_id IS NULL"
        query += " ORDER BY c.full_name"
        return db.fetch_all(query, params)

    def get_customer_booking_history(self, customer_id):
        """Lấy lịch sử đặt sân của một khách hàng"""
        query = """
        SELECT b.booking_id, b.booking_date, b.status, b.total_amount,
               COUNT(bd.booking_detail_id) AS total_courts
        FROM Booking b
        LEFT JOIN Booking_Detail bd ON b.booking_id = bd.booking_id
        WHERE b.customer_id = ?
        GROUP BY b.booking_id, b.booking_date, b.status, b.total_amount
        ORDER BY b.booking_date DESC
        """
        return db.fetch_all(query, (customer_id,))

    def get_customer_booking_details(self, booking_id):
        """Lấy chi tiết các sân trong một booking (dùng cho lịch sử)"""
        return self.get_booking_details(booking_id)

    def add_member(self, admin_id, customer_id, username, password_hash, status='Active'):
        existing = db.fetch_one("SELECT customer_id FROM Member WHERE username = ?", (username,))
        if existing:
            return False, "Tên đăng nhập đã tồn tại.", None

        success = db.execute_query("""
                                   INSERT INTO Member (customer_id, username, password_hash, register_date, status)
                                   VALUES (?, ?, ?, GETDATE(), ?)
                                   """, (customer_id, username, password_hash, status))

        if success:
            self.logger.log_action(admin_id, "CREATE", "Member", customer_id,
                                   f"Tạo tài khoản thành viên cho khách {customer_id}")
            return True, "Thêm thành viên thành công.", customer_id
        else:
            return False, "Lỗi khi thêm thành viên.", None

    def get_customer_bookings(self, customer_id):
        pass

    def get_promotion_by_id(self, promotion_id):
        return db.fetch_one("SELECT * FROM Promotion WHERE promotion_id = ?", (promotion_id,))

    def add_promotion(self, admin_id, name, discount_type, discount_value, start_date, end_date, is_active):
        # Kiểm tra tên trùng? Có thể không cần, nhưng có thể thêm.
        query = """
                INSERT INTO Promotion (promotion_name, discount_type, discount_value, start_date, end_date, is_active)
                VALUES (?, ?, ?, ?, ?, ?) \
                """
        success = db.execute_query(query, (name, discount_type, discount_value, start_date, end_date, is_active))
        if success:
            # Lấy id vừa tạo
            new_id = db.fetch_one("SELECT @@IDENTITY AS id")['id']
            self.logger.log_action(admin_id, "CREATE", "Promotion", new_id, f"Tạo khuyến mãi: {name}")
            return True, "Thêm khuyến mãi thành công", new_id
        else:
            return False, "Lỗi khi thêm khuyến mãi", None

    def update_promotion(self, admin_id, promotion_id, name, discount_type, discount_value, start_date, end_date,
                         is_active):
        query = """
                UPDATE Promotion
                SET promotion_name = ?, \
                    discount_type  = ?, \
                    discount_value = ?, \
                    start_date     = ?, \
                    end_date       = ?, \
                    is_active      = ?
                WHERE promotion_id = ? \
                """
        success = db.execute_query(query,
                                   (name, discount_type, discount_value, start_date, end_date, is_active, promotion_id))
        if success:
            self.logger.log_action(admin_id, "UPDATE", "Promotion", promotion_id, f"Cập nhật khuyến mãi: {name}")
            return True, "Cập nhật thành công"
        else:
            return False, "Lỗi khi cập nhật"

    def delete_promotion(self, admin_id, promotion_id):
        # Kiểm tra xem có booking nào dùng không? Nếu có, không cho xóa (hoặc set is_active = 0)
        result = db.fetch_one("SELECT COUNT(*) as total FROM Booking WHERE promotion_id = ?", (promotion_id,))
        if result and result['total'] > 0:
            return False, "Không thể xóa vì đã có đơn đặt sử dụng khuyến mãi này."
        success = db.execute_query("DELETE FROM Promotion WHERE promotion_id = ?", (promotion_id,))
        if success:
            self.logger.log_action(admin_id, "DELETE", "Promotion", promotion_id, f"Xóa khuyến mãi")
            return True, "Xóa thành công"
        else:
            return False, "Lỗi khi xóa"

    def toggle_promotion_status(self, admin_id, promotion_id, is_active):
        # Hàm này có thể dùng để bật/tắt nhanh
        success = db.execute_query("UPDATE Promotion SET is_active = ? WHERE promotion_id = ?",
                                   (is_active, promotion_id))
        if success:
            action = "BẬT" if is_active else "TẮT"
            self.logger.log_action(admin_id, "UPDATE_STATUS", "Promotion", promotion_id, f"{action} khuyến mãi")
            return True, f"Đã {action} khuyến mãi"
        else:
            return False, "Lỗi cập nhật trạng thái"

# =====================================
    # PAYMENT & REFUND MANAGEMENT
    # =====================================

    def get_pending_payments(self):
        """
        Lấy danh sách các booking đang chờ thanh toán (status='Pending')
        Kèm thông tin khách hàng, tổng tiền, và trạng thái payment (nếu có)
        """
        query = """
        SELECT b.booking_id, c.full_name, c.phone_number, b.booking_date, b.total_amount,
               p.payment_id, p.status as payment_status, p.payment_method
        FROM Booking b
        JOIN Customer c ON b.customer_id = c.customer_id
        LEFT JOIN Payment p ON b.booking_id = p.booking_id
        WHERE b.status = 'Pending'
        ORDER BY b.booking_date DESC
        """
        return db.fetch_all(query)

    def get_completed_payments(self):
        """
        Lấy danh sách các booking đã thanh toán (status='Confirmed', payment='Success')
        """
        query = """
        SELECT b.booking_id, c.full_name, c.phone_number, b.booking_date, b.total_amount,
               p.payment_id, p.payment_method, p.payment_date
        FROM Booking b
        JOIN Customer c ON b.customer_id = c.customer_id
        JOIN Payment p ON b.booking_id = p.booking_id
        WHERE b.status = 'Confirmed' AND p.status = 'Success'
        ORDER BY p.payment_date DESC
        """
        return db.fetch_all(query)

    def get_cancelled_bookings_for_refund(self):
        """
        Lấy danh sách các booking đã hủy (status='Cancelled') chưa có refund,
        kèm thông tin payment nếu có.
        """
        query = """
        SELECT b.booking_id, c.full_name, c.phone_number, b.booking_date, b.total_amount,
               p.payment_id, p.status as payment_status, p.payment_method,
               CASE WHEN r.refund_id IS NOT NULL THEN 1 ELSE 0 END as has_refund
        FROM Booking b
        JOIN Customer c ON b.customer_id = c.customer_id
        LEFT JOIN Payment p ON b.booking_id = p.booking_id
        LEFT JOIN Refund r ON b.booking_id = r.booking_id
        WHERE b.status = 'Cancelled' AND r.refund_id IS NULL
        ORDER BY b.booking_date DESC
        """
        return db.fetch_all(query)

    def get_refund_history(self):
        """
        Lấy lịch sử hoàn tiền (dùng cho tab 3 nếu muốn hiển thị các refund đã tạo)
        """
        query = """
        SELECT r.refund_id, b.booking_id, c.full_name, r.refund_amount, r.refund_date, r.reason
        FROM Refund r
        JOIN Booking b ON r.booking_id = b.booking_id
        JOIN Customer c ON b.customer_id = c.customer_id
        ORDER BY r.refund_date DESC
        """
        return db.fetch_all(query)

    def get_cancelled_bookings_for_refund(self):
        query = """
                SELECT b.booking_id, \
                       c.full_name, \
                       c.phone_number, \
                       b.booking_date, \
                       b.total_amount,
                       p.payment_id, \
                       p.status                                            as payment_status, \
                       p.payment_method,
                       CASE WHEN r.refund_id IS NOT NULL THEN 1 ELSE 0 END as has_refund
                FROM Booking b
                         JOIN Customer c ON b.customer_id = c.customer_id
                         LEFT JOIN Payment p ON b.booking_id = p.booking_id
                         LEFT JOIN Refund r ON b.booking_id = r.booking_id
                WHERE b.status = 'Cancelled'
                ORDER BY b.booking_date DESC \
                """
        return db.fetch_all(query)

    def get_all_admins(self):
        """Lấy danh sách admin (ID và tên)"""
        return db.fetch_all("SELECT admin_id, full_name FROM Admin ORDER BY full_name")

    def get_admin_by_id(self, admin_id):
        """Lấy thông tin chi tiết của admin theo ID"""
        query = "SELECT admin_id, full_name, username, role FROM Admin WHERE admin_id = ?"
        return db.fetch_one(query, (admin_id,))

    def login_admin(self, username, password):
        """
        Đăng nhập cho admin.
        Trả về: (success, message, admin_id, full_name, role)
        """
        admin = db.fetch_one("SELECT * FROM Admin WHERE username = ?", (username,))
        if not admin:
            return False, "Tên đăng nhập không tồn tại.", None, None, None
        # So sánh mật khẩu (trong demo dùng plain text, thực tế nên hash)
        if admin['password_hash'] != password:
            return False, "Sai mật khẩu.", None, None, None
        if admin['status'] != 'Active':
            return False, "Tài khoản đã bị khóa.", None, None, None
        return True, "Đăng nhập thành công.", admin['admin_id'], admin['full_name'], admin['role']