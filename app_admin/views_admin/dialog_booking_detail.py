from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QInputDialog
from PyQt6.QtCore import Qt
from datetime import datetime

from app_admin.core_admin.admin_logic import AdminLogic
from app_admin.core_admin.refund_logic import RefundLogic

class BookingDetailDialog(QDialog):
    def __init__(self, booking_id, admin_id, parent=None):
        super().__init__(parent)
        self.booking_id = booking_id
        self.admin_id = admin_id
        self.admin_logic = AdminLogic()
        self.refund_logic = RefundLogic()
        self.setWindowTitle(f"Chi tiết đơn #{booking_id}")
        self.setModal(True)
        self.resize(750, 550)

        layout = QVBoxLayout(self)

        # Thông tin chung (dùng QGridLayout cho đẹp)
        info_layout = QHBoxLayout()
        self.lbl_booking_id = QLabel()
        self.lbl_customer = QLabel()
        self.lbl_phone = QLabel()
        self.lbl_date = QLabel()
        info_layout.addWidget(self.lbl_booking_id)
        info_layout.addWidget(self.lbl_customer)
        info_layout.addWidget(self.lbl_phone)
        info_layout.addWidget(self.lbl_date)
        layout.addLayout(info_layout)

        # Bảng chi tiết sân
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Sân", "Bắt đầu", "Kết thúc", "Đơn giá", "Thành tiền"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Tổng cộng, giảm giá, tổng thanh toán
        total_layout = QHBoxLayout()
        self.lbl_total = QLabel("Tổng: 0")
        self.lbl_discount = QLabel("Giảm: 0")
        self.lbl_final = QLabel("Thanh toán: 0")
        total_layout.addWidget(self.lbl_total)
        total_layout.addWidget(self.lbl_discount)
        total_layout.addWidget(self.lbl_final)
        layout.addLayout(total_layout)

        # Nút thao tác
        button_layout = QHBoxLayout()
        self.btn_confirm_payment = QPushButton("Xác nhận thanh toán")
        self.btn_cancel = QPushButton("Hủy đơn")
        self.btn_print = QPushButton("In hóa đơn")
        self.btn_close = QPushButton("Đóng")
        button_layout.addWidget(self.btn_confirm_payment)
        button_layout.addWidget(self.btn_cancel)
        button_layout.addWidget(self.btn_print)
        button_layout.addWidget(self.btn_close)
        layout.addLayout(button_layout)

        # Kết nối sự kiện
        self.btn_confirm_payment.clicked.connect(self.confirm_payment)
        self.btn_cancel.clicked.connect(self.cancel_booking)
        self.btn_print.clicked.connect(self.print_invoice)
        self.btn_close.clicked.connect(self.accept)

        # Load dữ liệu
        self.load_data()

    def load_data(self):
        # Lấy thông tin booking
        booking = self.admin_logic.get_booking_by_id(self.booking_id)
        if not booking:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy thông tin đơn.")
            self.reject()
            return

        # Lấy thông tin khách hàng
        customer = self.admin_logic.get_customer_by_booking(self.booking_id)

        # Hiển thị thông tin chung
        self.lbl_booking_id.setText(f"Mã đơn: {booking['booking_id']}")
        self.lbl_customer.setText(f"Khách: {customer.get('full_name', 'N/A') if customer else 'N/A'}")
        self.lbl_phone.setText(f"SĐT: {customer.get('phone_number', 'N/A') if customer else 'N/A'}")
        date_val = booking['booking_date']
        if isinstance(date_val, datetime):
            date_str = date_val.strftime("%d/%m/%Y %H:%M")
        else:
            date_str = str(date_val)
        self.lbl_date.setText(f"Ngày đặt: {date_str}")

        # Lấy chi tiết sân
        details = self.admin_logic.get_booking_details(self.booking_id)
        self.table.setRowCount(len(details))
        for i, det in enumerate(details):
            self.table.setItem(i, 0, QTableWidgetItem(det['court_code']))
            start = det['start_time']
            if isinstance(start, datetime):
                start_str = start.strftime("%d/%m %H:%M")
            else:
                start_str = str(start)
            self.table.setItem(i, 1, QTableWidgetItem(start_str))

            end = det['end_time']
            if isinstance(end, datetime):
                end_str = end.strftime("%d/%m %H:%M")
            else:
                end_str = str(end)
            self.table.setItem(i, 2, QTableWidgetItem(end_str))

            self.table.setItem(i, 3, QTableWidgetItem(f"{det['price_per_hour']:,.0f} đ"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{det['subtotal']:,.0f} đ"))

        # Tính tổng, giảm giá, tổng thanh toán
        total_amount = booking['total_amount']
        promotion = self.admin_logic.get_promotion_by_booking(self.booking_id)
        discount = 0
        if promotion:
            if promotion['discount_type'] == 'Percentage':
                discount = total_amount * promotion['discount_value'] / 100
            else:  # Fixed
                discount = promotion['discount_value']
        final = total_amount - discount

        self.lbl_total.setText(f"Tổng: {total_amount:,.0f} đ")
        self.lbl_discount.setText(f"Giảm: {discount:,.0f} đ")
        self.lbl_final.setText(f"Thanh toán: {final:,.0f} đ")

        # Disable các nút theo trạng thái
        status = booking['status']
        if status == 'Cancelled' or status == 'Completed':
            self.btn_confirm_payment.setEnabled(False)
            self.btn_cancel.setEnabled(False)
        elif status == 'Confirmed':
            self.btn_confirm_payment.setEnabled(False)  # đã thanh toán rồi
        elif status == 'Pending':
            # Có thể confirm và hủy
            pass

    def confirm_payment(self):
        reply = QMessageBox.question(
            self, "Xác nhận",
            "Bạn có chắc đã nhận thanh toán cho đơn này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.admin_logic.confirm_payment(self.admin_id, self.booking_id)
            if success:
                QMessageBox.information(self, "Thành công", message)
                self.accept()  # Đóng dialog, parent sẽ reload
            else:
                QMessageBox.critical(self, "Lỗi", message)

    def cancel_booking(self):
        reason, ok = QInputDialog.getText(self, "Hủy đơn", "Nhập lý do hủy:")
        if not ok or not reason.strip():
            return

        booking = self.admin_logic.get_booking_by_id(self.booking_id)
        if not booking:
            return

        # Nếu đã thanh toán (Confirmed) thì hỏi hoàn tiền
        if booking['status'] == 'Confirmed':
            reply = QMessageBox.question(
                self, "Hoàn tiền",
                "Đơn đã thanh toán. Bạn có muốn hoàn tiền cho khách không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                success, message = self.refund_logic.process_refund(self.admin_id, self.booking_id, reason)
            else:
                success, message = self.admin_logic.update_booking_status(
                    self.admin_id, self.booking_id, 'Cancelled', reason
                )
        else:
            # Chưa thanh toán -> hủy trực tiếp
            success, message = self.admin_logic.update_booking_status(
                self.admin_id, self.booking_id, 'Cancelled', reason
            )

        if success:
            QMessageBox.information(self, "Thành công", message)
            # Cập nhật trạng thái court
            details = self.admin_logic.get_booking_details(self.booking_id)
            court_ids = list(set(d['court_id'] for d in details))
            from app_admin.core_admin.court_logic import CourtLogic
            court_logic = CourtLogic()
            for court_id in court_ids:
                court_logic.update_court_status_based_on_bookings(court_id)
            self.accept()
        else:
            QMessageBox.critical(self, "Lỗi", message)

    def print_invoice(self):
        QMessageBox.information(self, "Thông báo", "Chức năng in hóa đơn đang phát triển.")