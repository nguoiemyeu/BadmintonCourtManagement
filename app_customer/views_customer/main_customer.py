import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QDialog
from PyQt6.QtCore import Qt

from dangky_dangnhap.giaodiencsdl import Ui_MainWindow
from dangky_dangnhap.popup_thanh_vien import Ui_Dialog as PopupDialog
from app_customer.core_customer.customer_logic import CustomerLogic

class PopupThanhVien(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = PopupDialog()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.ui.pushButton_dong.clicked.connect(self.reject)
        self.ui.pushButton_dang_ky.clicked.connect(lambda: self.done(1))
        self.ui.pushButton_dang_nhap_nhanh.clicked.connect(lambda: self.done(2))

class MainCustomer(QMainWindow):
    def __init__(self, customer_id=None, customer_name=None):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.customer_logic = CustomerLogic()
        self.current_customer_id = customer_id
        self.current_customer_name = customer_name

        self.connect_signals()

        if not self.current_customer_id:
            self.show_popup_initial()
        else:
            self.ui.giaodien.setCurrentWidget(self.ui.page_san)

    def connect_signals(self):
        # Trang đăng ký (có thể không dùng vì đã có login riêng, nhưng vẫn giữ)
        self.ui.pushButton_dk_dang_ki.clicked.connect(self.handle_register)
        self.ui.pushButton_dn.clicked.connect(lambda: self.ui.giaodien.setCurrentWidget(self.ui.page_ban_da_la_thanh_vien))

        # Trang đặt sân nhanh
        self.ui.pushButton_tiep_tuc.clicked.connect(self.handle_fast_booking)
        self.ui.pushButton_quay_lai_2.clicked.connect(lambda: self.ui.giaodien.setCurrentWidget(self.ui.page_ban_da_la_thanh_vien))

        # Trang đăng nhập (có thể không dùng)
        self.ui.pushButton_tiep_tuc_3.clicked.connect(self.handle_login)
        self.ui.pushButton_quen_mk.clicked.connect(self.handle_forgot_password)

        # Trang "Bạn đã là thành viên chưa?"
        self.ui.pushButton_da_la_thanh_vien.clicked.connect(lambda: self.ui.giaodien.setCurrentWidget(self.ui.page_3))
        self.ui.pushButton_chua_co_tai_khoan.clicked.connect(lambda: self.ui.giaodien.setCurrentWidget(self.ui.page_dang_ky))
        self.ui.pushButton_quay_lai.clicked.connect(self.close)

        self.ui.pushButton_quay_lai_4.clicked.connect(lambda: self.ui.giaodien.setCurrentWidget(self.ui.page_san))

    def show_popup_initial(self):
        popup = PopupThanhVien(self)
        result = popup.exec()
        if result == 1:
            self.ui.giaodien.setCurrentWidget(self.ui.page_dang_ky)
        elif result == 2:
            self.ui.giaodien.setCurrentWidget(self.ui.page_dat_san_nhanh)
        else:
            self.close()

    def handle_register(self):
        full_name = self.ui.lineEdit_dk_ho_va_ten.text().strip()
        phone = self.ui.lineEdit_dk_sdt.text().strip()
        username = self.ui.lineEdit_dk_tendn.text().strip()
        password = self.ui.lineEdit_dk_pw.text().strip()

        if not full_name or not phone or not username or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin.")
            return

        success, message, customer_id = self.customer_logic.register_member(full_name, phone, username, password)
        if success:
            QMessageBox.information(self, "Thành công", message)
            self.current_customer_id = customer_id
            self.current_customer_name = full_name
            self.ui.giaodien.setCurrentWidget(self.ui.page_san)
        else:
            QMessageBox.critical(self, "Lỗi", message)

    def handle_fast_booking(self):
        full_name = self.ui.lineEdit_nhap_ho_va_ten.text().strip()
        phone = self.ui.lineEdit_nhap_sdt.text().strip()

        if not full_name or not phone:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập họ tên và số điện thoại.")
            return

        customer_id = self.customer_logic.get_or_create_customer(full_name, phone)
        if customer_id:
            self.current_customer_id = customer_id
            self.current_customer_name = full_name
            self.ui.giaodien.setCurrentWidget(self.ui.page_san)
        else:
            QMessageBox.critical(self, "Lỗi", "Không thể tạo khách hàng.")

    def handle_login(self):
        username = self.ui.lineEdit_dang_nhap.text().strip()
        password = self.ui.lineEdit_nhap_mk.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập thông tin")
            return
        success, msg, cid, name = self.customer_logic.login(username, password)
        if success:
            self.current_customer_id = cid
            self.current_customer_name = name
            self.ui.giaodien.setCurrentWidget(self.ui.page_san)
        else:
            QMessageBox.critical(self, "Lỗi", msg)

    def handle_forgot_password(self):
        QMessageBox.information(self, "Thông báo", "Chức năng đang phát triển.")