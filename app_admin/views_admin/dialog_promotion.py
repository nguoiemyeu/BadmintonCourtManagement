from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QDoubleSpinBox, QDateEdit, QCheckBox, QPushButton, QMessageBox
from PyQt6.QtCore import QDate, Qt

from app_admin.core_admin.admin_logic import AdminLogic
from datetime import datetime, time

class PromotionDialog(QDialog):
    def __init__(self, admin_id, promotion=None, parent=None):
        super().__init__(parent)
        self.admin_id = admin_id
        self.promotion = promotion  # None nếu thêm mới
        self.admin_logic = AdminLogic()
        self.setWindowTitle("Thêm khuyến mãi" if promotion is None else "Sửa khuyến mãi")
        self.setModal(True)
        self.resize(400, 350)

        layout = QVBoxLayout(self)

        # Tên khuyến mãi
        layout.addWidget(QLabel("Tên chương trình:"))
        self.edit_name = QLineEdit()
        if promotion:
            self.edit_name.setText(promotion['promotion_name'])
        layout.addWidget(self.edit_name)

        # Loại giảm giá
        layout.addWidget(QLabel("Loại giảm giá:"))
        self.combo_type = QComboBox()
        self.combo_type.addItem("Phần trăm (%)", "Percentage")
        self.combo_type.addItem("Số tiền cố định (VNĐ)", "Fixed")
        if promotion:
            index = self.combo_type.findData(promotion['discount_type'])
            if index >= 0:
                self.combo_type.setCurrentIndex(index)
        layout.addWidget(self.combo_type)

        # Giá trị giảm
        layout.addWidget(QLabel("Giá trị giảm:"))
        self.spin_value = QDoubleSpinBox()
        self.spin_value.setRange(0, 1000000)
        self.spin_value.setSingleStep(1000)
        self.spin_value.setSuffix(" VNĐ" if self.combo_type.currentData() == "Fixed" else " %")
        if promotion:
            self.spin_value.setValue(float(promotion['discount_value']))
        self.combo_type.currentIndexChanged.connect(self.update_spin_suffix)
        layout.addWidget(self.spin_value)

        # Ngày bắt đầu
        layout.addWidget(QLabel("Ngày bắt đầu:"))
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate())
        if promotion and promotion['start_date']:
            if isinstance(promotion['start_date'], str):
                from datetime import datetime
                d = datetime.strptime(promotion['start_date'], "%Y-%m-%d %H:%M:%S")
                self.date_start.setDate(QDate(d.year, d.month, d.day))
            else:
                self.date_start.setDate(QDate(promotion['start_date'].year, promotion['start_date'].month, promotion['start_date'].day))
        layout.addWidget(self.date_start)

        # Ngày kết thúc
        layout.addWidget(QLabel("Ngày kết thúc:"))
        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(QDate.currentDate().addDays(30))
        if promotion and promotion['end_date']:
            if isinstance(promotion['end_date'], str):
                from datetime import datetime
                d = datetime.strptime(promotion['end_date'], "%Y-%m-%d %H:%M:%S")
                self.date_end.setDate(QDate(d.year, d.month, d.day))
            else:
                self.date_end.setDate(QDate(promotion['end_date'].year, promotion['end_date'].month, promotion['end_date'].day))
        layout.addWidget(self.date_end)

        # Kích hoạt ngay
        self.check_active = QCheckBox("Kích hoạt ngay")
        if promotion:
            self.check_active.setChecked(promotion['is_active'] == 1 or promotion['is_active'] is True)
        else:
            self.check_active.setChecked(True)
        layout.addWidget(self.check_active)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Lưu")
        self.btn_cancel = QPushButton("Hủy")
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.btn_save.clicked.connect(self.save)
        self.btn_cancel.clicked.connect(self.reject)

    def update_spin_suffix(self):
        if self.combo_type.currentData() == "Fixed":
            self.spin_value.setSuffix(" VNĐ")
            self.spin_value.setRange(0, 1000000)
            self.spin_value.setSingleStep(1000)
        else:
            self.spin_value.setSuffix(" %")
            self.spin_value.setRange(0, 100)
            self.spin_value.setSingleStep(1)

    def save(self):
        name = self.edit_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên chương trình")
            return

        discount_type = self.combo_type.currentData()
        value = self.spin_value.value()
        if value <= 0:
            QMessageBox.warning(self, "Lỗi", "Giá trị giảm phải lớn hơn 0")
            return

        from datetime import datetime, time
        start_date = datetime.combine(self.date_start.date().toPyDate(), time.min)
        end_date = datetime.combine(self.date_end.date().toPyDate(), time.max)

        if start_date >= end_date:
            QMessageBox.warning(self, "Lỗi", "Ngày kết thúc phải sau ngày bắt đầu")
            return

        is_active = 1 if self.check_active.isChecked() else 0

        if self.promotion is None:
            success, message, new_id = self.admin_logic.add_promotion(
                self.admin_id, name, discount_type, value, start_date, end_date, is_active
            )
            if success:
                QMessageBox.information(self, "Thành công", message)
                self.accept()
            else:
                QMessageBox.critical(self, "Lỗi", message)
        else:
            success, message = self.admin_logic.update_promotion(
                self.admin_id, self.promotion['promotion_id'], name, discount_type, value, start_date, end_date,
                is_active
            )
            if success:
                QMessageBox.information(self, "Thành công", message)
                self.accept()
            else:
                QMessageBox.critical(self, "Lỗi", message)