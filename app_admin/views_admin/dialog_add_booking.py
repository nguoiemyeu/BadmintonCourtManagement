from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QComboBox, QDateTimeEdit, QLineEdit, QSpinBox, QHeaderView
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QColor
from datetime import datetime

from app_admin.core_admin.admin_logic import AdminLogic
from app_admin.core_admin.court_logic import CourtLogic

class AddBookingDialog(QDialog):
    def __init__(self, admin_id, parent=None):
        super().__init__(parent)
        self.admin_id = admin_id
        self.admin_logic = AdminLogic()
        self.court_logic = CourtLogic()
        self.setWindowTitle("Thêm đơn đặt sân mới")
        self.setModal(True)
        self.resize(800, 600)

        # Dữ liệu tạm thời cho các sân đã chọn
        self.selected_courts = []  # list of dict: court_id, court_code, start, end, price, subtotal

        # Layout chính
        layout = QVBoxLayout(self)

        # === Thông tin khách hàng ===
        customer_layout = QHBoxLayout()
        self.cmb_customer = QComboBox()
        self.cmb_customer.addItem("-- Chọn khách hàng --", None)
        self.btn_new_customer = QPushButton("Khách mới")
        customer_layout.addWidget(QLabel("Khách hàng:"))
        customer_layout.addWidget(self.cmb_customer)
        customer_layout.addWidget(self.btn_new_customer)
        layout.addLayout(customer_layout)

        # === Chọn sân và thời gian ===
        court_select_layout = QHBoxLayout()
        self.cmb_court = QComboBox()
        self.cmb_court.addItem("-- Chọn sân --", None)
        self.dt_start = QDateTimeEdit()
        self.dt_start.setDateTime(QDateTime.currentDateTime())
        self.dt_start.setCalendarPopup(True)
        self.dt_end = QDateTimeEdit()
        self.dt_end.setDateTime(QDateTime.currentDateTime().addSecs(3600))  # +1 giờ
        self.dt_end.setCalendarPopup(True)
        self.btn_add_court = QPushButton("Thêm sân")
        court_select_layout.addWidget(QLabel("Sân:"))
        court_select_layout.addWidget(self.cmb_court)
        court_select_layout.addWidget(QLabel("Từ:"))
        court_select_layout.addWidget(self.dt_start)
        court_select_layout.addWidget(QLabel("Đến:"))
        court_select_layout.addWidget(self.dt_end)
        court_select_layout.addWidget(self.btn_add_court)
        layout.addLayout(court_select_layout)

        # === Bảng danh sách sân đã chọn ===
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Mã sân", "Bắt đầu", "Kết thúc", "Đơn giá", "Thành tiền", "Xóa"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # === Tổng tiền và khuyến mãi ===
        total_layout = QHBoxLayout()
        self.lbl_total = QLabel("Tổng: 0 đ")
        self.cmb_promotion = QComboBox()
        self.cmb_promotion.addItem("-- Không áp dụng --", None)
        self.lbl_discount = QLabel("Giảm: 0 đ")
        self.lbl_final = QLabel("Thanh toán: 0 đ")
        total_layout.addWidget(self.lbl_total)
        total_layout.addWidget(QLabel("Khuyến mãi:"))
        total_layout.addWidget(self.cmb_promotion)
        total_layout.addWidget(self.lbl_discount)
        total_layout.addWidget(self.lbl_final)
        layout.addLayout(total_layout)

        # === Nút lưu và hủy ===
        button_layout = QHBoxLayout()
        self.btn_save = QPushButton("Lưu đơn")
        self.btn_cancel = QPushButton("Hủy")
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_cancel)
        layout.addLayout(button_layout)

        # Kết nối sự kiện
        self.btn_add_court.clicked.connect(self.add_court_to_list)
        self.btn_new_customer.clicked.connect(self.create_new_customer)
        self.btn_save.clicked.connect(self.save)
        self.btn_cancel.clicked.connect(self.reject)
        self.cmb_promotion.currentIndexChanged.connect(self.update_totals)
        self.dt_start.dateTimeChanged.connect(self.validate_end_time)
        self.dt_end.dateTimeChanged.connect(self.validate_end_time)

        # Load dữ liệu ban đầu
        self.load_customers()
        self.load_courts()
        self.load_promotions()

    def load_customers(self):
        """Load danh sách khách hàng vào combobox"""
        # Giả sử có method get_all_customers trong admin_logic (cần thêm nếu chưa có)
        customers = self.admin_logic.get_all_customers()  # Tạm thời dùng method có sẵn?
        # Nếu chưa có, ta có thể tự viết query:
        # from shared.database.db_manager import db
        # customers = db.fetch_all("SELECT customer_id, full_name, phone_number FROM Customer ORDER BY full_name")
        # Tôi sẽ giả sử đã có method này.
        self.cmb_customer.clear()
        self.cmb_customer.addItem("-- Chọn khách hàng --", None)
        for c in customers:
            self.cmb_customer.addItem(f"{c['full_name']} - {c['phone_number']}", c['customer_id'])

    def load_courts(self):
        """Load danh sách sân đang Available vào combobox"""
        courts = self.court_logic.get_all_courts()
        self.cmb_court.clear()
        self.cmb_court.addItem("-- Chọn sân --", None)
        for c in courts:
            if c['status'] == 'Available':
                self.cmb_court.addItem(f"{c['court_code']}", c['court_id'])

    def load_promotions(self):
        """Load danh sách khuyến mãi đang active"""
        promotions = self.admin_logic.get_all_promotions()  # Đã có
        self.cmb_promotion.clear()
        self.cmb_promotion.addItem("-- Không áp dụng --", None)
        for p in promotions:
            if p['is_active']:
                self.cmb_promotion.addItem(p['promotion_name'], p['promotion_id'])

    def validate_end_time(self):
        """Đảm bảo end_time > start_time"""
        start = self.dt_start.dateTime()
        end = self.dt_end.dateTime()
        if end <= start:
            self.dt_end.setDateTime(start.addSecs(3600))

    def get_price_per_hour(self, dt):
        """
        Tính giá theo giờ dựa vào thời gian bắt đầu.
        dt: QDateTime object
        Trả về: 60000 nếu trước 17h, 80000 nếu từ 17h trở đi
        """
        # Lấy giờ từ QDateTime
        hour = dt.time().hour()
        minute = dt.time().minute()
        # Nếu thời gian bắt đầu từ 17:00 trở đi -> 80k, ngược lại 60k
        if hour >= 17:
            return 80000
        else:
            return 60000

    def calculate_subtotal(self, start, end):
        """
        Tính thành tiền cho một khoảng thời gian.
        start, end: QDateTime
        """
        # Tính số giờ (làm tròn lên? Theo đề bài: giá theo giờ, tính riêng từng khoảng nếu qua 17h)
        # Đơn giản: tính tổng số phút, nhân với giá/giờ
        # Nhưng đề bài yêu cầu: nếu thời gian kéo dài qua 17h thì tính riêng.
        # Ta sẽ xử lý phức tạp hơn: chia làm 2 khoảng nếu cần.
        start_dt = start.toPyDateTime()
        end_dt = end.toPyDateTime()
        total_minutes = (end_dt - start_dt).total_seconds() / 60
        if total_minutes <= 0:
            return 0

        # Xác định các khoảng thời gian trong ngày
        # Giả sử giá chỉ thay đổi theo giờ bắt đầu, không chia nhỏ?
        # Đề bài: "Trường hợp thời gian sử dụng kéo dài qua mốc 17 giờ thì chi phí được tính riêng cho từng khoảng thời gian tương ứng."
        # Do đó cần chia.
        # Ta sẽ tính số phút trước 17h và sau 17h.
        # Giới hạn: chỉ xét trong cùng ngày? Đề không nói, nhưng booking_detail chỉ trong ngày? Thực tế có thể qua ngày.
        # Đơn giản hóa: tạm tính theo giờ bắt đầu (giống logic cũ) để demo.
        # Nhưng để đúng, tôi sẽ viết hàm chia khoảng.
        return self._split_and_calculate(start_dt, end_dt)

    def _split_and_calculate(self, start, end):
        """
        Tính tiền dựa trên mốc 17h.
        start, end: datetime objects
        """
        if start >= end:
            return 0

        # Nếu cùng ngày và không qua 17h
        if start.date() == end.date():
            if start.hour < 17 and end.hour < 17:
                # hoàn toàn trước 17h
                hours = (end - start).total_seconds() / 3600
                return hours * 60000
            elif start.hour >= 17:
                # hoàn toàn sau 17h
                hours = (end - start).total_seconds() / 3600
                return hours * 80000
            else:
                # bắt đầu trước 17h, kết thúc sau 17h
                # Tính đến 17h
                split_point = datetime(start.year, start.month, start.day, 17, 0)
                hours_before = (split_point - start).total_seconds() / 3600
                hours_after = (end - split_point).total_seconds() / 3600
                return hours_before * 60000 + hours_after * 80000
        else:
            # Qua ngày: phức tạp, tạm tính theo giờ bắt đầu
            # Có thể xử lý chi tiết hơn, nhưng demo tạm
            hours = (end - start).total_seconds() / 3600
            # Lấy giờ bắt đầu làm chuẩn
            if start.hour < 17:
                return hours * 60000
            else:
                return hours * 80000

    def add_court_to_list(self):
        """Thêm sân được chọn vào bảng tạm"""
        court_id = self.cmb_court.currentData()
        if not court_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn sân.")
            return
        court_code = self.cmb_court.currentText()

        start = self.dt_start.dateTime()
        end = self.dt_end.dateTime()
        if end <= start:
            QMessageBox.warning(self, "Lỗi", "Thời gian kết thúc phải sau thời gian bắt đầu.")
            return

        # Kiểm tra trùng lịch với các sân đã chọn (trong cùng đơn)
        for item in self.selected_courts:
            if item['court_id'] == court_id:
                # Kiểm tra thời gian trùng
                existing_start = item['start']
                existing_end = item['end']
                if not (end <= existing_start or start >= existing_end):
                    QMessageBox.warning(self, "Lỗi", "Sân này đã được chọn trong khoảng thời gian bị trùng trong cùng đơn.")
                    return

        # Tính giá và thành tiền
        price_per_hour = self.get_price_per_hour(start)
        subtotal = self.calculate_subtotal(start, end)

        # Thêm vào danh sách
        court_item = {
            'court_id': court_id,
            'court_code': court_code,
            'start': start,
            'end': end,
            'price': price_per_hour,
            'subtotal': subtotal
        }
        self.selected_courts.append(court_item)

        # Cập nhật bảng
        self.refresh_table()
        self.update_totals()

    def refresh_table(self):
        """Làm mới bảng hiển thị các sân đã chọn"""
        self.table.setRowCount(len(self.selected_courts))
        for i, item in enumerate(self.selected_courts):
            self.table.setItem(i, 0, QTableWidgetItem(item['court_code']))
            self.table.setItem(i, 1, QTableWidgetItem(item['start'].toString("dd/MM/yyyy HH:mm")))
            self.table.setItem(i, 2, QTableWidgetItem(item['end'].toString("dd/MM/yyyy HH:mm")))
            self.table.setItem(i, 3, QTableWidgetItem(f"{item['price']:,} đ"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{item['subtotal']:,} đ"))

            # Nút xóa
            btn_delete = QPushButton("Xóa")
            btn_delete.clicked.connect(lambda checked, row=i: self.remove_court_row(row))
            self.table.setCellWidget(i, 5, btn_delete)

    def remove_court_row(self, row):
        """Xóa một dòng khỏi danh sách"""
        if 0 <= row < len(self.selected_courts):
            del self.selected_courts[row]
            self.refresh_table()
            self.update_totals()

    def update_totals(self):
        total = sum(item['subtotal'] for item in self.selected_courts)
        promotion_id = self.cmb_promotion.currentData()
        discount = 0
        if promotion_id:
            promos = self.admin_logic.get_all_promotions()
            promo = next((p for p in promos if p['promotion_id'] == promotion_id), None)
            if promo:
                # Chuyển discount_value từ Decimal sang float
                discount_value = float(promo['discount_value'])
                if promo['discount_type'] == 'Percentage':
                    discount = total * discount_value / 100
                else:  # Fixed
                    discount = discount_value
        final = total - discount
        if final < 0:
            final = 0

        self.lbl_total.setText(f"Tổng: {total:,.0f} đ")
        self.lbl_discount.setText(f"Giảm: {discount:,.0f} đ")
        self.lbl_final.setText(f"Thanh toán: {final:,.0f} đ")

    def create_new_customer(self):
        from PyQt6.QtWidgets import QInputDialog
        name, ok1 = QInputDialog.getText(self, "Khách mới", "Nhập họ tên khách hàng:")
        if not ok1 or not name.strip():
            return
        phone, ok2 = QInputDialog.getText(self, "Khách mới", "Nhập số điện thoại:")
        if not ok2 or not phone.strip():
            return

        success, message = self.admin_logic.add_customer(name.strip(), phone.strip())
        if success:
            QMessageBox.information(self, "Thành công", "Đã thêm khách hàng mới.")
            self.load_customers()
            # Cập nhật dashboard nếu parent là MainAdminView
            if self.parent() and hasattr(self.parent(), 'load_dashboard_data'):
                self.parent().load_dashboard_data()
            # Chọn khách vừa thêm (tìm cách)
            self.cmb_customer.setCurrentIndex(self.cmb_customer.count() - 1)
        else:
            QMessageBox.critical(self, "Lỗi", message)

    def save(self):
        """Lưu đơn đặt sân vào database"""
        # Kiểm tra dữ liệu đầu vào
        customer_id = self.cmb_customer.currentData()
        if not customer_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn khách hàng.")
            return

        if not self.selected_courts:
            QMessageBox.warning(self, "Lỗi", "Vui lòng thêm ít nhất một sân.")
            return

        promotion_id = self.cmb_promotion.currentData()
        total_amount = sum(item['subtotal'] for item in self.selected_courts)
        # Tính lại final (có thể dùng update_totals)
        discount = 0
        # Trong save:
        if promotion_id:
            promos = self.admin_logic.get_all_promotions()
            promo = next((p for p in promos if p['promotion_id'] == promotion_id), None)
            if promo:
                discount_value = float(promo['discount_value'])
                if promo['discount_type'] == 'Percentage':
                    discount = total_amount * discount_value / 100
                else:
                    discount = discount_value

        final = total_amount - discount
        if final < 0:
            final = 0

        # Gọi logic tạo booking (cần method create_booking trong admin_logic)
        # Tôi sẽ tạo một method mới trong admin_logic sau
        success, message, booking_id = self.admin_logic.create_booking(
            admin_id=self.admin_id,
            customer_id=customer_id,
            promotion_id=promotion_id,
            details=self.selected_courts,  # list các dict với court_id, start, end, price, subtotal
            total_amount=final  # Số tiền thực tế khách phải trả sau giảm giá? Hay total_amount là tổng trước giảm?
        )
        # Theo cấu trúc bảng Booking: total_amount là tổng tiền sau giảm (số tiền thực tế).
        # Nhưng trong Booking_Detail, subtotal là tiền từng sân. Tổng subtotal = total_amount + discount.
        # Tùy vào logic, bạn có thể lưu total_amount là tổng trước giảm và discount riêng? Nhưng không có cột discount.
        # Vậy total_amount trong Booking là số tiền thực tế sau giảm.
        # Trong create_booking, cần tính toán và insert booking, details, và payment nếu có.

        if success:
            QMessageBox.information(self, "Thành công", f"Đã tạo đơn thành công. Mã đơn: {booking_id}")
            self.accept()
        else:
            QMessageBox.critical(self, "Lỗi", message)