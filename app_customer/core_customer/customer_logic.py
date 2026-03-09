from shared.database.db_manager import db
from datetime import datetime
import hashlib

class CustomerLogic:
    def __init__(self):
        pass

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def check_phone_exists(self, phone):
        result = db.fetch_one("SELECT customer_id FROM Customer WHERE phone_number = ?", (phone,))
        return result is not None

    def check_username_exists(self, username):
        result = db.fetch_one("SELECT customer_id FROM Member WHERE username = ?", (username,))
        return result is not None

    def register_member(self, full_name, phone, username, password):
        # Kiểm tra số điện thoại
        if self.check_phone_exists(phone):
            return False, "Số điện thoại đã được sử dụng.", None
        # Kiểm tra username
        if self.check_username_exists(username):
            return False, "Tên đăng nhập đã tồn tại.", None

        conn = db.get_connection()
        if not conn:
            return False, "Lỗi kết nối database.", None

        try:
            cursor = conn.cursor()
            # Thêm vào Customer
            cursor.execute(
                "INSERT INTO Customer (full_name, phone_number, created_at) VALUES (?, ?, ?)",
                (full_name, phone, datetime.now())
            )
            conn.commit()
            cursor.execute("SELECT @@IDENTITY AS id")
            customer_id = cursor.fetchone()[0]

            # Thêm vào Member
            password_hash = self.hash_password(password)
            cursor.execute(
                "INSERT INTO Member (customer_id, username, password_hash, register_date, status) VALUES (?, ?, ?, ?, ?)",
                (customer_id, username, password_hash, datetime.now(), 'Active')
            )
            conn.commit()
            return True, "Đăng ký thành công!", customer_id
        except Exception as e:
            conn.rollback()
            return False, f"Lỗi: {str(e)}", None
        finally:
            conn.close()

    def login(self, username, password):
        """Đăng nhập bằng username và mật khẩu"""
        # Tìm member theo username
        member = db.fetch_one("SELECT customer_id, password_hash FROM Member WHERE username = ?", (username,))
        if not member:
            return False, "Tên đăng nhập không tồn tại.", None, None

        # Kiểm tra mật khẩu
        password_hash = self.hash_password(password)
        if member['password_hash'] != password_hash:
            return False, "Sai mật khẩu.", None, None

        # Lấy thông tin customer
        customer = db.fetch_one("SELECT full_name FROM Customer WHERE customer_id = ?", (member['customer_id'],))
        full_name = customer['full_name'] if customer else ""

        return True, "Đăng nhập thành công!", member['customer_id'], full_name

    def get_or_create_customer(self, full_name, phone):
        existing = db.fetch_one("SELECT customer_id FROM Customer WHERE phone_number = ?", (phone,))
        if existing:
            return existing['customer_id']
        else:
            success, msg, new_id = self.add_customer(full_name, phone)
            return new_id if success else None

    def add_customer(self, full_name, phone):
        if self.check_phone_exists(phone):
            return False, "Số điện thoại đã tồn tại.", None
        success = db.execute_query(
            "INSERT INTO Customer (full_name, phone_number, created_at) VALUES (?, ?, ?)",
            (full_name, phone, datetime.now())
        )
        if success:
            new_id = db.fetch_one("SELECT @@IDENTITY AS id")['id']
            return True, "Thêm khách hàng thành công.", new_id
        else:
            return False, "Lỗi khi thêm khách hàng.", None