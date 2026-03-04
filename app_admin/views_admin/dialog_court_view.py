from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox
from app_admin.core_admin.court_logic import CourtLogic

class CourtDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Thêm sân mới")
        self.setModal(True)
        self.resize(300, 180)

        self.court_logic = CourtLogic()
        self.current_admin_id = getattr(parent, 'current_admin_id', 1) if parent else 1
        self.court_id = None

        layout = QVBoxLayout(self)

        self.label_code = QLabel("Mã sân:")
        self.input_code = QLineEdit()
        layout.addWidget(self.label_code)
        layout.addWidget(self.input_code)

        self.label_status = QLabel("Trạng thái:")
        self.combo_status = QComboBox()
        # Thêm 3 trạng thái với giá trị DB ẩn
        self.combo_status.addItem("Trống", "Available")
        self.combo_status.addItem("Đã đặt", "Booked")
        self.combo_status.addItem("Bảo trì", "Maintenance")
        layout.addWidget(self.label_status)
        layout.addWidget(self.combo_status)

        button_layout = QHBoxLayout()
        self.btn_save = QPushButton("Lưu")
        self.btn_cancel = QPushButton("Hủy")
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_cancel)
        layout.addLayout(button_layout)

        self.btn_save.clicked.connect(self.save)
        self.btn_cancel.clicked.connect(self.reject)

    def set_data(self, court_data):
        self.court_id = court_data['court_id']
        self.input_code.setText(court_data['court_code'])

        # Ánh xạ từ tiếng Việt sang giá trị DB để chọn combobox
        status_map = {
            "Trống": "Available",
            "Đã đặt": "Booked",
            "Bảo trì": "Maintenance"
        }
        db_status = status_map.get(court_data['status'], "Available")
        index = self.combo_status.findData(db_status)
        if index >= 0:
            self.combo_status.setCurrentIndex(index)

    def save(self):
        code = self.input_code.text().strip()
        status_db = self.combo_status.currentData()  # 'Available','Booked','Maintenance'

        if not code:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập mã sân.")
            return

        if self.court_id is None:  # Thêm mới
            success, message = self.court_logic.add_court(
                admin_id=self.current_admin_id,
                court_code=code
            )
            if success:
                QMessageBox.information(self, "Thành công", message)
                self.accept()
            else:
                QMessageBox.critical(self, "Lỗi", message)
        else:  # Sửa
            court = self.court_logic.get_court_by_id(self.court_id)
            if not court:
                QMessageBox.critical(self, "Lỗi", "Không tìm thấy sân.")
                return

            changes = []
            if code != court["court_code"]:
                changes.append(('info', code))
            if status_db != court["status"]:
                changes.append(('status', status_db))

            if not changes:
                QMessageBox.information(self, "Thông báo", "Không có thay đổi nào.")
                return

            success = True
            message = ""
            for change_type, *args in changes:
                if change_type == 'info':
                    s, m = self.court_logic.update_court_info(
                        admin_id=self.current_admin_id,
                        court_id=self.court_id,
                        new_code=args[0]
                    )
                elif change_type == 'status':
                    s, m = self.court_logic.update_court_status(
                        admin_id=self.current_admin_id,
                        court_id=self.court_id,
                        new_status=args[0],
                        reason="Cập nhật qua dialog sửa"
                    )
                else:
                    s, m = False, "Loại thay đổi không hợp lệ"

                if not s:
                    success = False
                    message = m
                    break

            if success:
                QMessageBox.information(self, "Thành công", "Cập nhật sân thành công.")
                self.accept()
            else:
                QMessageBox.critical(self, "Lỗi", message)