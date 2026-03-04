from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem, QVBoxLayout, QDialog, QInputDialog
from app_admin.views_admin.ui_generated.giao_dien_admin import Ui_MainWindow
from app_admin.views_admin.dialog_booking_detail import BookingDetailDialog

from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QGraphicsScene

from datetime import datetime

# Thư viện vẽ biểu đồ cho PyQt6
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from PyQt6 import QtCore, QtGui
import pyqtgraph as pg

# Import các file Logic Nghiệp vụ
from app_admin.core_admin.admin_logic import AdminLogic
from app_admin.core_admin.court_logic import CourtLogic
from app_admin.core_admin.refund_logic import RefundLogic
from app_admin.core_admin.admin_logger import AdminLogger

from app_admin.views_admin.dialog_court_view import CourtDialog
class MainAdminView(QMainWindow):
    def __init__(self):
        super().__init__()

        # 1. Khởi tạo Giao diện
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 2. Khởi tạo các class Logic
        self.admin_logic = AdminLogic()
        self.court_logic = CourtLogic()
        self.refund_logic = RefundLogic()
        self.logger = AdminLogger()

        # Giả lập Admin ID đang đăng nhập (Thực tế sẽ truyền từ màn hình Login sang)
        self.current_admin_id = 1

        # 3. Kết nối sự kiện (Nút bấm -> Hàm xử lý)
        self.setup_signals()

        # 4. Cài đặt mặc định khi vừa mở App lên
        # Mở trang chủ (Index 0)
        self.switch_page(0)

        # ==================================================

    # KHU VỰC 1: KẾT NỐI SỰ KIỆN (SIGNALS & SLOTS)
    # ==================================================
    def setup_signals(self):
        """Kết nối toàn bộ nút bấm trên giao diện với các hàm xử lý"""

        # --- 1.1. MENU ĐIỀU HƯỚNG BÊN TRÁI (Chuyển trang) ---
        # Dùng lambda để truyền tham số index của trang vào hàm switch_page
        #Nút bấm trang chủ
        self.ui.pushButton_trangchu.clicked.connect(lambda: self.switch_page(0))
        self.ui.pushButton_quanlysan.clicked.connect(lambda: self.switch_page(1))
        self.ui.pushButton_qldon.clicked.connect(lambda: self.switch_page(2))
        self.ui.pushButton_qlkhachhang.clicked.connect(lambda: self.switch_page(3))
        self.ui.pushButton_qlkhmai.clicked.connect(lambda: self.switch_page(4))
        self.ui.pushButton_ttht.clicked.connect(lambda: self.switch_page(5))
        self.ui.pushButton_adminlog.clicked.connect(lambda: self.switch_page(6))
        self.ui.pushButton_taikhoan.clicked.connect(lambda: self.switch_page(7))


        #Nút bấm trang quản lý court
        self.ui.pushButton_trangchu_2.clicked.connect(lambda: self.switch_page(0))
        self.ui.pushButton_quanlysan_2.clicked.connect(lambda: self.switch_page(1))
        self.ui.pushButton_qldon_2.clicked.connect(lambda: self.switch_page(2))
        self.ui.pushButton_qlkhachhang_2.clicked.connect(lambda: self.switch_page(3))
        self.ui.pushButton_qlkhmai_2.clicked.connect(lambda: self.switch_page(4))
        self.ui.pushButton_ttht_2.clicked.connect(lambda: self.switch_page(5))
        self.ui.pushButton_adminlog_2.clicked.connect(lambda: self.switch_page(6))
        self.ui.pushButton_taikhoan_2.clicked.connect(lambda: self.switch_page(7))

        # Kết nối các nút bấm Trang 1: Quản lý sân
        self.ui.pushButton_kiem.clicked.connect(self.load_court_data)  # Nút Tìm kiếm
        self.ui.pushButton_loc.clicked.connect(self.load_court_data)  # Nút Lọc
        self.ui.pushButton_lammoi.clicked.connect(self.refresh_court_tab)  # Nút Làm mới
        self.ui.pushButton_thems.clicked.connect(self.handle_add_court)  # Nút Thêm sân
        self.ui.pushButton_xoa.clicked.connect(self.handle_sidebar_delete)  # Nút Xóa sân
        self.ui.pushButton_sua.clicked.connect(self.handle_sidebar_edit)  # Nút Sửa sân

        #Nút bấm trang quản lý đơn đặt
        self.ui.pushButton_trangchu_3.clicked.connect(lambda: self.switch_page(0))
        self.ui.pushButton_quanlysan_3.clicked.connect(lambda: self.switch_page(1))
        self.ui.pushButton_qldon_3.clicked.connect(lambda: self.switch_page(2))
        self.ui.pushButton_qlkhachhang_3.clicked.connect(lambda: self.switch_page(3))
        self.ui.pushButton_qlkhmai_3.clicked.connect(lambda: self.switch_page(4))
        self.ui.pushButton_ttht_3.clicked.connect(lambda: self.switch_page(5))
        self.ui.pushButton_adminlog_3.clicked.connect(lambda: self.switch_page(6))
        self.ui.pushButton_taikhoan_3.clicked.connect(lambda: self.switch_page(7))

        # Trang quản lý đơn đặt
        self.ui.pushButton_kiem_2.clicked.connect(self.filter_booking_data)
        self.ui.pushButton_loc_2.clicked.connect(self.filter_booking_data)
        self.ui.pushButton_xemct.clicked.connect(self.view_booking_detail)
        self.ui.pushButton_huydon.clicked.connect(self.cancel_booking)
        self.ui.pushButton_xuatfile.clicked.connect(self.handle_export_booking_excel)
        self.ui.pushButton_lammoi_2.clicked.connect(self.load_booking_data)
        self.ui.pushButton_themdon.clicked.connect(self.handle_add_booking)

        #Nút bấm trang quản lý khachhang
        self.ui.pushButton_trangchu_4.clicked.connect(lambda: self.switch_page(0))
        self.ui.pushButton_quanlysan_4.clicked.connect(lambda: self.switch_page(1))
        self.ui.pushButton_qldon_4.clicked.connect(lambda: self.switch_page(2))
        self.ui.pushButton_qlkhachhang_4.clicked.connect(lambda: self.switch_page(3))
        self.ui.pushButton_qlkhmai_4.clicked.connect(lambda: self.switch_page(4))
        self.ui.pushButton_ttht_4.clicked.connect(lambda: self.switch_page(5))
        self.ui.pushButton_adminlog_4.clicked.connect(lambda: self.switch_page(6))
        self.ui.pushButton_taikhoan_4.clicked.connect(lambda: self.switch_page(7))

        #Nút bấm trang quản lý khuyến mãi
        self.ui.pushButton_trangchu_5.clicked.connect(lambda: self.switch_page(0))
        self.ui.pushButton_quanlysan_5.clicked.connect(lambda: self.switch_page(1))
        self.ui.pushButton_qldon_5.clicked.connect(lambda: self.switch_page(2))
        self.ui.pushButton_qlkhachhang_5.clicked.connect(lambda: self.switch_page(3))
        self.ui.pushButton_qlkhmai_5.clicked.connect(lambda: self.switch_page(4))
        self.ui.pushButton_ttht_5.clicked.connect(lambda: self.switch_page(5))
        self.ui.pushButton_adminlog_5.clicked.connect(lambda: self.switch_page(6))
        self.ui.pushButton_taikhoan_5.clicked.connect(lambda: self.switch_page(7))

        #Nút bấm trang thanh toán hoàn tiền
        self.ui.pushButton_trangchu_6.clicked.connect(lambda: self.switch_page(0))
        self.ui.pushButton_quanlysan_6.clicked.connect(lambda: self.switch_page(1))
        self.ui.pushButton_qldon_6.clicked.connect(lambda: self.switch_page(2))
        self.ui.pushButton_qlkhachhang_6.clicked.connect(lambda: self.switch_page(3))
        self.ui.pushButton_qlkhmai_6.clicked.connect(lambda: self.switch_page(4))
        self.ui.pushButton_ttht_6.clicked.connect(lambda: self.switch_page(5))
        self.ui.pushButton_adminlog_6.clicked.connect(lambda: self.switch_page(6))
        self.ui.pushButton_taikhoan_6.clicked.connect(lambda: self.switch_page(7))

        #page nhật ký admin
        self.ui.pushButton_trangchu_7.clicked.connect(lambda: self.switch_page(0))
        self.ui.pushButton_quanlysan_7.clicked.connect(lambda: self.switch_page(1))
        self.ui.pushButton_qldon_7.clicked.connect(lambda: self.switch_page(2))
        self.ui.pushButton_qlkhachhang_7.clicked.connect(lambda: self.switch_page(3))
        self.ui.pushButton_qlkhmai_7.clicked.connect(lambda: self.switch_page(4))
        self.ui.pushButton_ttht_7.clicked.connect(lambda: self.switch_page(5))
        self.ui.pushButton_adminlog_7.clicked.connect(lambda: self.switch_page(6))
        self.ui.pushButton_taikhoan_7.clicked.connect(lambda: self.switch_page(7))

        #page tài khoản
        self.ui.pushButton_trangchu_8.clicked.connect(lambda: self.switch_page(0))
        self.ui.pushButton_quanlysan_8.clicked.connect(lambda: self.switch_page(1))
        self.ui.pushButton_qldon_8.clicked.connect(lambda: self.switch_page(2))
        self.ui.pushButton_qlkhachhang_8.clicked.connect(lambda: self.switch_page(3))
        self.ui.pushButton_qlkhmai_8.clicked.connect(lambda: self.switch_page(4))
        self.ui.pushButton_ttht_8.clicked.connect(lambda: self.switch_page(5))
        self.ui.pushButton_adminlog_8.clicked.connect(lambda: self.switch_page(6))
        self.ui.pushButton_taikhoan_8.clicked.connect(lambda: self.switch_page(7))

        # --- 1.2. CÁC NÚT CHỨC NĂNG CHUNG ---
        # Ở trang Tài khoản
        self.ui.pushButton_dangxuat.clicked.connect(self.handle_logout)
        self.ui.pushButton_doimk.clicked.connect(self.handle_change_password)

        # Ở trang Nhật ký hệ thống (Admin log)
        self.ui.pushButton_2_xuatfile.clicked.connect(self.handle_export_logs_excel)

        # (Các nút thêm/sửa/xóa của từng trang sẽ được bổ sung vào đây khi code tới trang đó)

    # ==================================================
    # KHU VỰC 2: ĐIỀU HƯỚNG (NAVIGATION)
    # ==================================================
    def switch_page(self, index):
        """Đổi trang hiển thị trên QStackedWidget và tự động load dữ liệu cho trang đó"""
        self.ui.stackedWidget.setCurrentIndex(index)

        # Lazy-loading: Chỉ gọi database để lấy dữ liệu khi người dùng thực sự bấm vào trang đó
        if index == 0:
            self.load_dashboard_data()
        elif index == 1:
            self.load_court_data()
        elif index == 2:
            self.load_booking_data()
        elif index == 3:
            self.load_customer_data()
        elif index == 4:
            self.load_promotion_data()
        elif index == 5:
            self.load_financial_data()
        elif index == 6:
            self.load_system_logs()
        elif index == 7:
            self.load_account_info()

    # ==================================================
    # KHU VỰC 3: CÁC HÀM XỬ LÝ (Tạm thời để 'pass' chờ code)
    # ==================================================
    def load_dashboard_data(self):
        """Tải dữ liệu hoàn chỉnh cho Dashboard và tối ưu hóa hiển thị biểu đồ"""
        try:
            # ==========================================
            # 0. HIỂN THỊ LỜI CHÀO ADMIN
            # ==========================================
            # Dùng luôn self.current_admin_id = 1 mà bạn đã giả lập ở __init__
            ten_admin = self.admin_logic.get_admin_info(self.current_admin_id)

            # Nhớ đổi label_ten_admin thành tên thật trong Qt Designer nhé
            self.ui.label_tenadmin.setText(ten_admin)
            # ==========================================
            # 1. ĐỔ DỮ LIỆU VÀO CÁC LINE EDIT
            # ==========================================
            available_courts = self.court_logic.get_available_courts_count()
            today_bookings = self.admin_logic.get_today_bookings()
            today_revenue = self.admin_logic.get_today_revenue()
            total_customers = self.admin_logic.get_total_customers()

            self.ui.lineEdit_santrong.setText(str(available_courts))
            self.ui.lineEdit_dontoday.setText(str(today_bookings))
            self.ui.lineEdit_dttoday.setText(f"{today_revenue:,.0f} VNĐ")
            self.ui.lineEdit_sokh.setText(str(total_customers))

            # ==========================================
            # 2. HIỂN THỊ ĐƠN ĐẶT LÊN QTABLEVIEW
            # ==========================================
            latest_bookings = self.admin_logic.get_latest_bookings(limit=10)
            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(["Mã đơn", "Khách hàng", "Ngày đặt", "Trạng thái", "Tổng tiền"])

            for row_data in latest_bookings:
                row = [
                    QStandardItem(str(row_data["booking_id"])),
                    QStandardItem(str(row_data["full_name"])),
                    QStandardItem(row_data["booking_date"].strftime("%d/%m %H:%M")),
                    QStandardItem(str(row_data["status"])),
                    QStandardItem(f"{row_data['total_amount']:,.0f} đ")
                ]
                model.appendRow(row)

            self.ui.tableView.setModel(model)
            self.ui.tableView.horizontalHeader().setStretchLastSection(True)

            # ==========================================
            # 3. VẼ BIỂU ĐỒ (CÁCH MỚI - TỰ ĐỘNG CO GIÃN CHUẨN)
            # ==========================================
            chart_data = self.admin_logic.get_revenue_last_7_days()

            # Bỏ khai báo figsize để Matplotlib tự động fill theo khung Layout
            fig = Figure(dpi=100)
            # Giúp các thành phần tự động dạt ra sát lề
            fig.set_layout_engine('tight')

            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)

            if not chart_data:
                ax.text(0.5, 0.5, 'Chưa có dữ liệu 7 ngày qua',
                        ha='center', va='center', fontsize=12, color='gray', style='italic')
                ax.set_xticks([])
                ax.set_yticks([])
            else:
                dates = [item["booking_date"] for item in chart_data]
                revenues = [float(item["daily_revenue"]) for item in chart_data]

                # Vẽ cột
                bars = ax.bar(dates, revenues, color='#27ae60', width=0.5)
                ax.set_title('DOANH THU 7 NGÀY GẦN NHẤT', fontsize=12, fontweight='bold', pad=15)
                ax.set_ylabel('Doanh thu (VNĐ)', fontsize=10)

                # Hiển thị số tiền trên đầu cột
                for bar in bars:
                    height = bar.get_height()
                    ax.annotate(f'{height:,.0f}',
                                xy=(bar.get_x() + bar.get_width() / 2, height),
                                xytext=(0, 3), textcoords="offset points",
                                ha='center', va='bottom', fontsize=9, fontweight='bold')

                # Xử lý trục X
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                fig.autofmt_xdate(rotation=0)  # Để chữ ngày tháng nằm ngang cho dễ đọc

                # Làm sạch viền biểu đồ
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)

            # ---------------------------------------------------------
            # NHÚNG CANVAS VÀO QGRAPHICSVIEW BẰNG LAYOUT (QUAN TRỌNG)
            # ---------------------------------------------------------
            # 1. Kiểm tra xem QGraphicsView đã có layout chưa, nếu chưa thì tạo mới
            layout = self.ui.graphicsView.layout()
            if layout is None:
                layout = QVBoxLayout(self.ui.graphicsView)
                layout.setContentsMargins(0, 0, 0, 0)  # Xóa lề thừa
            else:
                # 2. Nếu đã có layout (do bấm Load nhiều lần), xóa cái biểu đồ cũ đi
                while layout.count():
                    item = layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()

            # 3. Nạp biểu đồ mới vào
            layout.addWidget(canvas)

            print("✅ Đã load thành công Dashboard (Biểu đồ siêu nét)!")
        except Exception as e:
            print(f"❌ Lỗi khi tải dashboard: {e}")

    def load_court_data(self):
        try:
            search_text = self.ui.lineEdit_timkiem.text().strip()
            status_filter = self.ui.comboBox_trangthai.currentText()

            courts = self.court_logic.get_filtered_courts(search_text, status_filter)

            self.ui.tableWidget.setRowCount(0)
            self.ui.tableWidget.setColumnCount(3)
            self.ui.tableWidget.setHorizontalHeaderLabels(["Mã sân", "Tên sân", "Trạng thái"])

            # Ánh xạ từ DB sang tiếng Việt để hiển thị
            status_map_display = {
                "Available": "Trống",
                "Booked": "Đã đặt",
                "Maintenance": "Bảo trì"
            }

            for row_idx, court in enumerate(courts):
                self.ui.tableWidget.insertRow(row_idx)

                item_code = QTableWidgetItem(court['court_code'])
                item_code.setData(QtCore.Qt.ItemDataRole.UserRole, court['court_id'])

                # Tên sân hiển thị court_code
                item_name = QTableWidgetItem(court['court_code'])

                db_status = court['status']
                display_status = status_map_display.get(db_status, db_status)
                item_status = QTableWidgetItem(display_status)

                if db_status == "Available":
                    item_status.setForeground(QtGui.QColor("#27ae60"))  # xanh lá
                elif db_status == "Booked":
                    item_status.setForeground(QtGui.QColor("#e67e22"))  # cam
                elif db_status == "Maintenance":
                    item_status.setForeground(QtGui.QColor("#e74c3c"))  # đỏ

                self.ui.tableWidget.setItem(row_idx, 0, item_code)
                self.ui.tableWidget.setItem(row_idx, 1, item_name)
                self.ui.tableWidget.setItem(row_idx, 2, item_status)

            header = self.ui.tableWidget.horizontalHeader()
            header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, header.ResizeMode.Stretch)
            header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)

        except Exception as e:
            print(f"❌ Lỗi load_court_data: {e}")

    def refresh_court_tab(self):
        """Reset các ô nhập và load lại bảng"""
        self.ui.lineEdit_timkiem.clear()
        self.ui.comboBox_trangthai.setCurrentIndex(0)  # Về "Tất cả"
        self.load_court_data()

    def handle_sidebar_delete(self):
        current_row = self.ui.tableWidget.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một sân để xóa!")
            return

        item_code = self.ui.tableWidget.item(current_row, 0)
        court_id = item_code.data(QtCore.Qt.ItemDataRole.UserRole)
        court_code = item_code.text()

        confirm = QMessageBox.question(
            self, "Xác nhận", f"Bạn có chắc muốn xóa sân: {court_code}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            success, message = self.court_logic.delete_court(self.current_admin_id, court_id)
            if success:
                QMessageBox.information(self, "Thành công", message)
                self.load_court_data()
                self.load_dashboard_data()
            else:
                QMessageBox.critical(self, "Lỗi", message)


    def handle_add_court(self):
        """Mở dialog thêm sân mới"""
        self.open_court_modal(None)

    def handle_sidebar_edit(self):
        current_row = self.ui.tableWidget.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một sân để sửa!")
            return

        item_code = self.ui.tableWidget.item(current_row, 0)
        court_data = {
            'court_id': item_code.data(QtCore.Qt.ItemDataRole.UserRole),
            'court_code': item_code.text(),
            'status': self.ui.tableWidget.item(current_row, 2).text()  # lấy trạng thái tiếng Việt
        }
        self.open_court_modal(court_data)

    def open_court_modal(self, court_data=None):
        from app_admin.views_admin.dialog_court_view import CourtDialog
        dialog = CourtDialog(self)
        if court_data:
            dialog.set_data(court_data)
            dialog.setWindowTitle("Chỉnh sửa sân")
        else:
            dialog.setWindowTitle("Thêm sân mới")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_court_data()
            self.load_dashboard_data()

    def load_booking_data(self):
        """Load tất cả đơn khi vào trang (reset bộ lọc)"""

        try:
            # Lấy dữ liệu từ admin_logic (cần implement phương thức get_all_bookings)
            bookings = self.admin_logic.get_all_bookings()  # Giả sử đã có

            self.ui.tableWidget_2.setRowCount(0)
            self.ui.tableWidget_2.setColumnCount(5)
            self.ui.tableWidget_2.setHorizontalHeaderLabels(
                ["Mã đơn", "Khách hàng", "Ngày đặt", "Tổng tiền", "Trạng thái"]
            )

            # Ánh xạ trạng thái DB -> tiếng Việt
            status_map = {
                "Pending": "Chờ thanh toán",
                "Confirmed": "Đã thanh toán",
                "Cancelled": "Đã hủy",
                "Completed": "Hoàn thành"
            }

            for row_idx, booking in enumerate(bookings):
                self.ui.tableWidget_2.insertRow(row_idx)

                # Mã đơn (ẩn ID)
                item_booking_id = QTableWidgetItem(str(booking["booking_id"]))
                item_booking_id.setData(QtCore.Qt.ItemDataRole.UserRole, booking["booking_id"])
                self.ui.tableWidget_2.setItem(row_idx, 0, item_booking_id)

                # Khách hàng
                self.ui.tableWidget_2.setItem(row_idx, 1, QTableWidgetItem(booking["full_name"]))

                # Ngày đặt
                booking_date = booking["booking_date"]
                if isinstance(booking_date, datetime):
                    date_str = booking_date.strftime("%d/%m/%Y %H:%M")
                else:
                    date_str = str(booking_date)
                self.ui.tableWidget_2.setItem(row_idx, 2, QTableWidgetItem(date_str))

                # Tổng tiền
                total = booking["total_amount"]
                self.ui.tableWidget_2.setItem(row_idx, 3, QTableWidgetItem(f"{total:,.0f} VNĐ"))

                # Trạng thái
                db_status = booking["status"]
                display_status = status_map.get(db_status, db_status)
                item_status = QTableWidgetItem(display_status)

                # Tô màu
                if db_status == "Pending":
                    item_status.setForeground(QtGui.QColor("#f39c12"))  # vàng
                elif db_status == "Confirmed":
                    item_status.setForeground(QtGui.QColor("#27ae60"))  # xanh lá
                elif db_status == "Cancelled":
                    item_status.setForeground(QtGui.QColor("#e74c3c"))  # đỏ
                elif db_status == "Completed":
                    item_status.setForeground(QtGui.QColor("#3498db"))  # xanh dương

                self.ui.tableWidget_2.setItem(row_idx, 4, item_status)

            # Căn chỉnh cột
            header = self.ui.tableWidget_2.horizontalHeader()
            header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, header.ResizeMode.Stretch)
            header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, header.ResizeMode.ResizeToContents)

        except Exception as e:
            print(f"❌ Lỗi load_booking_data: {e}")

    def filter_booking_data(self):
        try:
            keyword = self.ui.lineEdit_timkiem_2.text().strip()
            from_date = None
            to_date = None

            dt_from = self.ui.dateTimeEdit_from.dateTime()
            if dt_from and not dt_from.isNull():
                from_date = dt_from.toPyDateTime()

            dt_to = self.ui.dateTimeEdit_to.dateTime()
            if dt_to and not dt_to.isNull():
                to_date = dt_to.toPyDateTime()

            status = self.ui.comboBox_trangthai_2.currentText()

            bookings = self.admin_logic.search_bookings(keyword, from_date, to_date, status)
            print(f"DEBUG: Tìm thấy {len(bookings)} đơn")

            # Chỉ hiện thông báo nếu có điều kiện lọc (không phải load mặc định)
            is_filtering = keyword or from_date or to_date or status != "Tất cả"
            if not bookings and is_filtering:
                QMessageBox.information(self, "Thông báo", "Không tìm thấy đơn nào phù hợp.")
            elif not bookings and not is_filtering:
                # Load mặc định mà không có dữ liệu thì không cần thông báo
                pass

            self.display_bookings(bookings)
        except Exception as e:
            print(f"❌ Lỗi lọc đơn: {e}")
            QMessageBox.critical(self, "Lỗi", f"Đã xảy ra lỗi: {str(e)}")

    def display_bookings(self, bookings):
        """Hiển thị danh sách booking lên tableWidget_2"""
        try:
            self.ui.tableWidget_2.setRowCount(0)
            self.ui.tableWidget_2.setColumnCount(5)
            self.ui.tableWidget_2.setHorizontalHeaderLabels(
                ["Mã đơn", "Khách hàng", "Ngày đặt", "Tổng tiền", "Trạng thái"]
            )

            status_map_display = {
                "Pending": "Chờ thanh toán",
                "Confirmed": "Đã thanh toán",
                "Cancelled": "Đã hủy",
                "Completed": "Hoàn thành"
            }

            for row_idx, booking in enumerate(bookings):
                self.ui.tableWidget_2.insertRow(row_idx)

                # Mã đơn (lưu ID ẩn)
                item_id = QTableWidgetItem(str(booking["booking_id"]))
                item_id.setData(Qt.ItemDataRole.UserRole, booking["booking_id"])
                self.ui.tableWidget_2.setItem(row_idx, 0, item_id)

                # Khách hàng
                self.ui.tableWidget_2.setItem(row_idx, 1, QTableWidgetItem(booking["full_name"]))

                # Ngày đặt
                date_val = booking["booking_date"]
                if isinstance(date_val, datetime):
                    date_str = date_val.strftime("%d/%m/%Y %H:%M")
                else:
                    date_str = str(date_val)
                self.ui.tableWidget_2.setItem(row_idx, 2, QTableWidgetItem(date_str))

                # Tổng tiền
                total = booking["total_amount"]
                self.ui.tableWidget_2.setItem(row_idx, 3, QTableWidgetItem(f"{total:,.0f} đ"))

                # Trạng thái (có màu)
                db_status = booking["status"]
                display_status = status_map_display.get(db_status, db_status)
                item_status = QTableWidgetItem(display_status)

                # Tô màu
                if db_status == "Pending":
                    item_status.setForeground(QtGui.QColor("#f39c12"))  # vàng
                elif db_status == "Confirmed":
                    item_status.setForeground(QtGui.QColor("#27ae60"))  # xanh lá
                elif db_status == "Cancelled":
                    item_status.setForeground(QtGui.QColor("#e74c3c"))  # đỏ
                elif db_status == "Completed":
                    item_status.setForeground(QtGui.QColor("#3498db"))  # xanh dương

                self.ui.tableWidget_2.setItem(row_idx, 4, item_status)

            # Căn chỉnh cột
            header = self.ui.tableWidget_2.horizontalHeader()
            header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, header.ResizeMode.Stretch)
            header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, header.ResizeMode.ResizeToContents)

        except Exception as e:
            print(f"❌ Lỗi hiển thị đơn: {e}")

    def view_booking_detail(self):
        """Mở dialog xem chi tiết đơn đã chọn"""
        current_row = self.ui.tableWidget_2.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một đơn để xem chi tiết!")
            return

        booking_id_item = self.ui.tableWidget_2.item(current_row, 0)
        booking_id = booking_id_item.data(Qt.ItemDataRole.UserRole)

        dialog = BookingDetailDialog(booking_id, self.current_admin_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Nếu dialog đóng sau khi thay đổi (thanh toán/hủy) thì reload
            self.filter_booking_data()

    def cancel_booking(self):
        """Xử lý hủy đơn đã chọn (gọi thẳng từ nút Hủy)"""
        current_row = self.ui.tableWidget_2.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một đơn để hủy!")
            return

        booking_id_item = self.ui.tableWidget_2.item(current_row, 0)
        booking_id = booking_id_item.data(Qt.ItemDataRole.UserRole)
        status_item = self.ui.tableWidget_2.item(current_row, 4)
        current_status_text = status_item.text()  # tiếng Việt

        # Kiểm tra trạng thái
        if current_status_text == "Đã hủy":
            QMessageBox.information(self, "Thông báo", "Đơn này đã được hủy trước đó.")
            return
        if current_status_text == "Hoàn thành":
            QMessageBox.information(self, "Thông báo", "Đơn đã hoàn thành, không thể hủy.")
            return

        # Xác nhận
        confirm = QMessageBox.question(
            self, "Xác nhận hủy",
            f"Bạn có chắc muốn hủy đơn {booking_id_item.text()}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        reason, ok = QInputDialog.getText(self, "Lý do hủy", "Nhập lý do hủy đơn (không bắt buộc):")
        if not ok:
            reason = "Admin hủy"

        # Lấy thông tin booking để biết đã thanh toán chưa
        booking = self.admin_logic.get_booking_by_id(booking_id)
        if not booking:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy thông tin đơn.")
            return

        if booking['status'] == 'Confirmed':
            # Đã thanh toán -> hỏi hoàn tiền
            reply = QMessageBox.question(
                self, "Hoàn tiền",
                "Đơn đã thanh toán. Bạn có muốn hoàn tiền cho khách không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                success, message = self.refund_logic.process_refund(self.current_admin_id, booking_id, reason)
            else:
                success, message = self.admin_logic.update_booking_status(
                    self.current_admin_id, booking_id, 'Cancelled', reason
                )
        else:
            # Chưa thanh toán
            success, message = self.admin_logic.update_booking_status(
                self.current_admin_id, booking_id, 'Cancelled', reason
            )

        if success:
            QMessageBox.information(self, "Thành công", message)
            # Lấy danh sách court_id từ booking_details
            details = self.admin_logic.get_booking_details(booking_id)
            court_ids = list(set(d['court_id'] for d in details))  # nếu có court_id trong details
            # Cập nhật từng court
            from app_admin.core_admin.court_logic import CourtLogic
            court_logic = CourtLogic()
            for court_id in court_ids:
                court_logic.update_court_status_based_on_bookings(court_id)
            self.filter_booking_data()
            self.load_dashboard_data()
        else:
            QMessageBox.critical(self, "Lỗi", message)

    def handle_filter_booking(self):
        """Xử lý tìm kiếm và lọc đơn đặt"""
        # TODO: Thực hiện lọc theo search_text, date_from, date_to, status
        # Hiện tại chỉ load lại toàn bộ
        self.load_booking_data()
        # Sau này sẽ gọi self.admin_logic.get_filtered_bookings(...)

    def handle_view_booking_detail(self):
        """Mở dialog xem chi tiết đơn đã chọn"""
        current_row = self.ui.tableWidget_2.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một đơn để xem chi tiết!")
            return

        booking_id_item = self.ui.tableWidget_2.item(current_row, 0)
        booking_id = booking_id_item.data(QtCore.Qt.ItemDataRole.UserRole)

        dialog = BookingDetailDialog(self, booking_id, self.current_admin_id)
        dialog.exec()

    def handle_cancel_booking(self):
        """Xử lý hủy đơn đã chọn (cập nhật trạng thái thành Cancelled)"""
        current_row = self.ui.tableWidget_2.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một đơn để hủy!")
            return

        booking_id_item = self.ui.tableWidget_2.item(current_row, 0)
        booking_id = booking_id_item.data(QtCore.Qt.ItemDataRole.UserRole)
        status_item = self.ui.tableWidget_2.item(current_row, 4)
        current_status = status_item.text()  # tiếng Việt

        # Xác nhận
        confirm = QMessageBox.question(
            self, "Xác nhận hủy",
            f"Bạn có chắc muốn hủy đơn {booking_id_item.text()}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        # Lấy lý do hủy (có thể mở dialog nhập lý do)
        reason, ok = QInputDialog.getText(self, "Lý do hủy", "Nhập lý do hủy đơn (không bắt buộc):")
        if not ok:
            reason = "Admin hủy"

        success, message = self.admin_logic.update_booking_status(
            admin_id=self.current_admin_id,
            booking_id=booking_id,
            new_status="Cancelled",
            reason=reason
        )
        if success:
            QMessageBox.information(self, "Thành công", message)
            self.load_booking_data()
        else:
            QMessageBox.critical(self, "Lỗi", message)

    def handle_export_booking_excel(self):
        """Xuất danh sách đơn ra Excel (tạm thời bỏ qua)"""
        QMessageBox.information(self, "Thông báo", "Chức năng xuất Excel đang được phát triển.")

    def handle_add_booking(self):
        from app_admin.views_admin.dialog_add_booking import AddBookingDialog
        dialog = AddBookingDialog(self.current_admin_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.filter_booking_data()  # reload danh sách
            self.load_dashboard_data()
    def load_customer_data(self):
        pass

    def load_promotion_data(self):
        pass

    def load_financial_data(self):
        pass

    def load_system_logs(self):
        pass

    def load_account_info(self):
        print("Đang load thông tin Tài khoản...")
        pass

    def handle_logout(self):
        print("Đã bấm nút Đăng xuất!")
        pass

    def handle_change_password(self):
        print("Đã bấm nút Đổi mật khẩu!")
        pass

    def handle_export_logs_excel(self):
        print("Đã bấm nút Xuất Excel log!")
        pass