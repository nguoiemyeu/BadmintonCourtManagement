from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt6.QtCore import Qt

class RefundDialog(QDialog):
    def __init__(self, booking_id, total_amount, parent=None):
        super().__init__(parent)
        self.booking_id = booking_id
        self.total_amount = total_amount
        self.setWindowTitle("Tạo hoàn tiền")
        self.setModal(True)
        self.resize(400, 200)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"Đơn #{booking_id} - Số tiền: {total_amount:,.0f} VNĐ"))
        layout.addWidget(QLabel("Lý do hoàn tiền:"))

        self.edit_reason = QLineEdit()
        layout.addWidget(self.edit_reason)

        btn_layout = QHBoxLayout()
        self.btn_confirm = QPushButton("Xác nhận hoàn tiền")
        self.btn_cancel = QPushButton("Hủy")
        btn_layout.addWidget(self.btn_confirm)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.btn_confirm.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def get_reason(self):
        return self.edit_reason.text().strip()