import pyodbc


class DBManager:
    def __init__(self):
        """
        Khởi tạo chuỗi kết nối đến SQL Server với thông tin đã được gắn cứng.
        Sử dụng Trusted_Connection=yes (Quyền xác thực của Windows).
        """
        # Đã điền sẵn thông tin Server và Database của bạn vào đây
        self.conn_str = (
            "DRIVER={SQL Server};"
            r"SERVER=.\SQLEXPRESS;"
            "DATABASE=BadmintonCourtManagement;"
            "Trusted_Connection=yes;"
        )

    def get_connection(self):
        """Tạo và trả về đối tượng kết nối"""
        try:
            conn = pyodbc.connect(self.conn_str)
            return conn
        except Exception as e:
            print(f"LỖI KẾT NỐI CSDL: {e}")
            return None

    def execute_query(self, query, params=None):
        """
        Dùng cho các lệnh không trả về dữ liệu: INSERT, UPDATE, DELETE
        """
        conn = self.get_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()  # Xác nhận thay đổi vào CSDL
            return True
        except Exception as e:
            print(f"LỖI THỰC THI (INSERT/UPDATE/DELETE): {e}")
            return False
        finally:
            conn.close()

    def fetch_all(self, query, params=None):
        """
        Dùng cho lệnh SELECT trả về nhiều dòng (Ví dụ: Lấy danh sách sân)
        Trả về một list các dict để dễ dàng truy xuất dữ liệu theo tên cột.
        """
        conn = self.get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Lấy tên các cột
            columns = [column[0] for column in cursor.description]

            # Lấy toàn bộ dữ liệu và map với tên cột
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
        except Exception as e:
            print(f"LỖI TRUY VẤN (SELECT ALL): {e}")
            return []
        finally:
            conn.close()

    def fetch_one(self, query, params=None):
        """
        Dùng cho lệnh SELECT trả về 1 dòng (Ví dụ: Tìm user theo ID hoặc số điện thoại)
        """
        conn = self.get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            row = cursor.fetchone()
            if row:
                columns = [column[0] for column in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            print(f"LỖI TRUY VẤN (SELECT ONE): {e}")
            return None
        finally:
            conn.close()


# Khởi tạo sẵn một đối tượng db dùng chung cho toàn bộ dự án
db = DBManager()