from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, \
    QMessageBox, QLineEdit, QComboBox
from PyQt6.QtCore import Qt
from datetime import datetime

from app_admin.core_admin.admin_logic import AdminLogic
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class CustomerDetailDialog(QDialog):
    def __init__(self, customer_id, admin_id, parent=None):
        super().__init__(parent)
        self.customer_id = customer_id
        self.admin_id = admin_id
        self.admin_logic = AdminLogic()
        self.setWindowTitle(f"Chi tiết khách hàng #{customer_id}")
        self.setModal(True)
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        # Thông tin khách hàng
        info_layout = QHBoxLayout()
        self.lbl_id = QLabel()
        self.lbl_name = QLabel()
        self.lbl_phone = QLabel()
        self.lbl_type = QLabel()
        self.lbl_join_date = QLabel()
        info_layout.addWidget(self.lbl_id)
        info_layout.addWidget(self.lbl_name)
        info_layout.addWidget(self.lbl_phone)
        info_layout.addWidget(self.lbl_type)
        info_layout.addWidget(self.lbl_join_date)
        layout.addLayout(info_layout)

        # Bảng lịch sử đặt sân
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Mã đơn", "Ngày đặt", "Trạng thái", "Tổng tiền", "Số sân"])
        layout.addWidget(self.table)

        # Nút đóng
        self.btn_close = QPushButton("Đóng")
        self.btn_close.clicked.connect(self.accept)
        layout.addWidget(self.btn_close)

        self.load_data()

    def load_data(self):
        customer = self.admin_logic.get_customer_by_id(self.customer_id)
        if not customer:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy khách hàng")
            self.reject()
            return

        self.lbl_id.setText(f"Mã: {customer['customer_id']}")
        self.lbl_name.setText(f"Họ tên: {customer['full_name']}")
        self.lbl_phone.setText(f"SĐT: {customer['phone_number']}")
        loai = "Thành viên" if customer.get('is_member', False) else "Khách nhanh"
        self.lbl_type.setText(f"Loại: {loai}")
        if customer.get('created_at'):
            if isinstance(customer['created_at'], datetime):
                date_str = customer['created_at'].strftime("%d/%m/%Y")
            else:
                date_str = str(customer['created_at'])
        else:
            date_str = ""
        self.lbl_join_date.setText(f"Ngày tạo: {date_str}")

        # Lịch sử booking
        bookings = self.admin_logic.get_customer_booking_history(self.customer_id)
        self.table.setRowCount(len(bookings))
        for i, b in enumerate(bookings):
            self.table.setItem(i, 0, QTableWidgetItem(str(b['booking_id'])))
            if isinstance(b['booking_date'], datetime):
                date_str = b['booking_date'].strftime("%d/%m/%Y %H:%M")
            else:
                date_str = str(b['booking_date'])
            self.table.setItem(i, 1, QTableWidgetItem(date_str))
            status_map = {
                "Pending": "Chờ thanh toán",
                "Confirmed": "Đã thanh toán",
                "Cancelled": "Đã hủy",
                "Completed": "Hoàn thành"
            }
            self.table.setItem(i, 2, QTableWidgetItem(status_map.get(b['status'], b['status'])))
            self.table.setItem(i, 3, QTableWidgetItem(f"{b['total_amount']:,.0f} đ"))
            self.table.setItem(i, 4, QTableWidgetItem(str(b['total_courts'])))


class CustomerEditDialog(QDialog):
    def __init__(self, admin_id, customer=None, parent=None):
        super().__init__(parent)
        self.admin_id = admin_id
        self.customer = customer  # None nếu thêm mới, có dữ liệu nếu sửa
        self.admin_logic = AdminLogic()
        self.setWindowTitle("Thêm khách hàng" if customer is None else "Sửa khách hàng")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        # Loại khách hàng (chỉ hiển thị khi thêm mới, vì sửa không cho đổi loại)
        if customer is None:
            self.label_type = QLabel("Loại khách:")
            self.combo_type = QComboBox()
            self.combo_type.addItem("Khách nhanh", "normal")
            self.combo_type.addItem("Thành viên", "member")
            self.combo_type.currentIndexChanged.connect(self.on_type_changed)
            layout.addWidget(self.label_type)
            layout.addWidget(self.combo_type)

        # Họ tên
        self.label_name = QLabel("Họ tên:")
        self.edit_name = QLineEdit()
        if customer:
            self.edit_name.setText(customer['full_name'])
        layout.addWidget(self.label_name)
        layout.addWidget(self.edit_name)

        # Số điện thoại
        self.label_phone = QLabel("Số điện thoại:")
        self.edit_phone = QLineEdit()
        if customer:
            self.edit_phone.setText(customer['phone_number'])
        layout.addWidget(self.label_phone)
        layout.addWidget(self.edit_phone)

        # Các trường dành cho thành viên (ẩn ban đầu nếu thêm mới)
        self.member_widgets = []
        if customer is None:
            self.label_username = QLabel("Tên đăng nhập:")
            self.edit_username = QLineEdit()
            self.label_password = QLabel("Mật khẩu:")
            self.edit_password = QLineEdit()
            self.edit_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.label_confirm = QLabel("Xác nhận mật khẩu:")
            self.edit_confirm = QLineEdit()
            self.edit_confirm.setEchoMode(QLineEdit.EchoMode.Password)

            # Ẩn ban đầu
            for w in [self.label_username, self.edit_username,
                      self.label_password, self.edit_password,
                      self.label_confirm, self.edit_confirm]:
                w.setVisible(False)
                self.member_widgets.append(w)
                layout.addWidget(w)
        else:
            # Khi sửa, không cho thay đổi loại, có thể hiển thị thông tin thêm nếu là member?
            # Ở đây ta chỉ cho sửa tên và SĐT, không sửa username/password.
            pass

        # Nút lưu và hủy
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Lưu")
        self.btn_cancel = QPushButton("Hủy")
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.btn_save.clicked.connect(self.save)
        self.btn_cancel.clicked.connect(self.reject)

    def on_type_changed(self, index):
        """Hiển thị/ẩn các trường thành viên"""
        is_member = (self.combo_type.currentData() == "member")
        for w in self.member_widgets:
            w.setVisible(is_member)
        # Điều chỉnh kích thước dialog
        if is_member:
            self.resize(400, 350)
        else:
            self.resize(400, 250)

    def save(self):
        name = self.edit_name.text().strip()
        phone = self.edit_phone.text().strip()
        if not name or not phone:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ họ tên và số điện thoại")
            return

        if self.customer is None:  # Thêm mới
            customer_type = self.combo_type.currentData()
            # Tạo customer trước
            success, message, new_customer_id = self.admin_logic.add_customer(name, phone)
            print(f"DEBUG: add_customer -> success={success}, message={message}, new_id={new_customer_id}")

            if not success:
                QMessageBox.critical(self, "Lỗi", message)
                return
            if new_customer_id is None:
                QMessageBox.critical(self, "Lỗi", "Không lấy được ID khách hàng mới")
                return
            if customer_type == "member":
                username = self.edit_username.text().strip()
                password = self.edit_password.text().strip()
                confirm = self.edit_confirm.text().strip()
                if not username or not password:
                    QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên đăng nhập và mật khẩu")
                    return
                if password != confirm:
                    QMessageBox.warning(self, "Lỗi", "Mật khẩu xác nhận không khớp")
                    return
                password_hash = hash_password(password)
                success_mem, message_mem, _ = self.admin_logic.add_member(
                    self.admin_id, new_customer_id, username, password_hash, 'Active'
                )
                print(f"DEBUG: add_member -> success={success_mem}, message={message_mem}")
                # ... xử lý kết quả
                if success_mem:
                    QMessageBox.information(self, "Thành công", "Thêm khách hàng thành công (thành viên)")
                    self.accept()
                else:
                    QMessageBox.critical(self, "Lỗi", message_mem)
                    # Có thể xóa customer? Tạm thời bỏ qua
            else:  # Khách nhanh
                QMessageBox.information(self, "Thành công", message)
                self.accept()
        else:  # Sửa thông tin
            success, message = self.admin_logic.update_customer(
                self.customer['customer_id'], name, phone
            )
            if success:
                QMessageBox.information(self, "Thành công", message)
                self.accept()
            else:
                QMessageBox.critical(self, "Lỗi", message)