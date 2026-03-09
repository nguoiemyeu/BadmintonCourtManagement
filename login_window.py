import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtCore import Qt

from dangky_dangnhap.giaodiencsdl import Ui_MainWindow
from app_admin.core_admin.admin_logic import AdminLogic
from app_customer.core_customer.customer_logic import CustomerLogic
from app_admin.views_admin.views.main_admin_view import MainAdminView
from app_customer.views_customer.main_customer import MainCustomer

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.admin_logic = AdminLogic()
        self.customer_logic = CustomerLogic()

        # Mặc định hiển thị trang đăng nhập (page_3)
        self.ui.giaodien.setCurrentWidget(self.ui.page_3)

        # Kết nối các nút
        self.ui.pushButton_tiep_tuc_3.clicked.connect(self.handle_login)  # Nút Tiếp tục ở trang đăng nhập
        self.ui.pushButton_dk_dang_ki.clicked.connect(self.handle_register)  # Nút Đăng kí ở trang đăng ký
        self.ui.pushButton_dn.clicked.connect(self.go_to_login)  # Nút Quay lại (Đăng nhập) ở trang đăng ký
        self.ui.pushButton_back_dk.clicked.connect(lambda: self.ui.giaodien.setCurrentWidget(self.ui.page_dang_ky))

    def go_to_login(self):
        """Chuyển về trang đăng nhập"""
        self.ui.giaodien.setCurrentWidget(self.ui.page_3)

    def handle_login(self):
        username = self.ui.lineEdit_dang_nhap.text().strip()   # Thực chất là username
        password = self.ui.lineEdit_nhap_mk.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên đăng nhập và mật khẩu")
            return

        # Thử đăng nhập admin trước
        success_admin, msg_admin, admin_id, full_name, role = self.admin_logic.login_admin(username, password)
        if success_admin:
            self.open_admin_window(admin_id, full_name, role)
            return

        # Thử đăng nhập customer (member)
        success_cus, msg_cus, customer_id, customer_name = self.customer_logic.login(username, password)
        if success_cus:
            self.open_customer_window(customer_id, customer_name)
            return

        # Cả hai đều thất bại
        QMessageBox.critical(self, "Lỗi", "Sai tên đăng nhập hoặc mật khẩu")

    def handle_register(self):
        """Xử lý đăng ký thành viên"""
        full_name = self.ui.lineEdit_dk_ho_va_ten.text().strip()
        phone = self.ui.lineEdit_dk_sdt.text().strip()
        username = self.ui.lineEdit_dk_tendn.text().strip()
        password = self.ui.lineEdit_dk_pw.text().strip()

        if not full_name or not phone or not username or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin")
            return

        success, msg, customer_id = self.customer_logic.register_member(full_name, phone, username, password)
        if success:
            QMessageBox.information(self, "Thành công", msg)
            # Sau khi đăng ký, chuyển về trang đăng nhập
            self.ui.giaodien.setCurrentWidget(self.ui.page_3)
            # Có thể tự động điền username
            self.ui.lineEdit_dang_nhap.setText(username)
            self.ui.lineEdit_nhap_mk.clear()
        else:
            QMessageBox.critical(self, "Lỗi", msg)

    def open_admin_window(self, admin_id, full_name, role):
        self.admin_window = MainAdminView()
        self.admin_window.current_admin_id = admin_id
        self.admin_window.show()
        self.close()

    def open_customer_window(self, customer_id, customer_name):
        self.customer_window = MainCustomer(customer_id=customer_id, customer_name=customer_name)
        self.customer_window.show()
        self.close()

    def forgot_password(self):
        QMessageBox.information(self, "Thông báo", "Chức năng quên mật khẩu đang phát triển")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())