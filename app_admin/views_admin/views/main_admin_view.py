from PyQt6.QtCore import QDateTime, Qt
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QTableWidgetItem, QVBoxLayout, QDialog, QInputDialog, QTableWidget
from app_admin.views_admin.ui_generated.giao_dien_admin import Ui_MainWindow
from app_admin.views_admin.dialog_booking_detail import BookingDetailDialog
from app_admin.views_admin.dialog_promotion import PromotionDialog
from app_admin.views_admin.dialog_refund import RefundDialog

from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QGraphicsScene

from datetime import datetime

# Thư viện vẽ biểu đồ cho PyQt6
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from PyQt6 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from shared.database.db_manager import db

# Import các file Logic Nghiệp vụ
from app_admin.core_admin.admin_logic import AdminLogic
from app_admin.core_admin.court_logic import CourtLogic
from app_admin.core_admin.refund_logic import RefundLogic
from app_admin.core_admin.admin_logger import AdminLogger

from app_admin.views_admin.dialog_customer_detail import CustomerDetailDialog
from app_admin.views_admin.dialog_customer_detail import CustomerEditDialog

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

        # Đặt tên cho các tab trong thanh toán hoàn tiền
        self.ui.tabWidget.setTabText(0, "Chờ thanh toán")
        self.ui.tabWidget.setTabText(1, "Đã thanh toán")
        self.ui.tabWidget.setTabText(2, "Hoàn tiền")


        # Thiết lập chế độ chọn cho các bảng thanh toán
        self.ui.tableWidget_5.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ui.tableWidget_5.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.ui.tableWidget_6.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ui.tableWidget_6.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.ui.tableWidget_7.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ui.tableWidget_7.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

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

        # Trang quản lý khách hàng
        self.ui.pushButton_themkh.clicked.connect(self.handle_add_customer)
        self.ui.pushButton_xoakh.clicked.connect(self.handle_delete_customer)
        self.ui.pushButton_chinh_sua.clicked.connect(self.handle_edit_customer)
        self.ui.pushButton_xemct_2.clicked.connect(self.handle_view_customer_detail)
        self.ui.pushButton_kiem_3.clicked.connect(self.filter_customer_data)
        self.ui.pushButton_3_loc.clicked.connect(self.filter_customer_data)

        #Nút bấm trang quản lý khuyến mãi
        self.ui.pushButton_trangchu_5.clicked.connect(lambda: self.switch_page(0))
        self.ui.pushButton_quanlysan_5.clicked.connect(lambda: self.switch_page(1))
        self.ui.pushButton_qldon_5.clicked.connect(lambda: self.switch_page(2))
        self.ui.pushButton_qlkhachhang_5.clicked.connect(lambda: self.switch_page(3))
        self.ui.pushButton_qlkhmai_5.clicked.connect(lambda: self.switch_page(4))
        self.ui.pushButton_ttht_5.clicked.connect(lambda: self.switch_page(5))
        self.ui.pushButton_adminlog_5.clicked.connect(lambda: self.switch_page(6))
        self.ui.pushButton_taikhoan_5.clicked.connect(lambda: self.switch_page(7))

        # Trang quản lý khuyến mãi
        self.ui.pushButton_themkm.clicked.connect(self.handle_add_promotion)

        #Nút bấm trang thanh toán hoàn tiền
        self.ui.pushButton_trangchu_6.clicked.connect(lambda: self.switch_page(0))
        self.ui.pushButton_quanlysan_6.clicked.connect(lambda: self.switch_page(1))
        self.ui.pushButton_qldon_6.clicked.connect(lambda: self.switch_page(2))
        self.ui.pushButton_qlkhachhang_6.clicked.connect(lambda: self.switch_page(3))
        self.ui.pushButton_qlkhmai_6.clicked.connect(lambda: self.switch_page(4))
        self.ui.pushButton_ttht_6.clicked.connect(lambda: self.switch_page(5))
        self.ui.pushButton_adminlog_6.clicked.connect(lambda: self.switch_page(6))
        self.ui.pushButton_taikhoan_6.clicked.connect(lambda: self.switch_page(7))
        # Trang thanh toán hoàn tiền
        self.ui.pushButton_xacnhantt.clicked.connect(self.handle_confirm_payment)
        self.ui.pushButton_taohoantien.clicked.connect(self.handle_create_refund_from_completed)
        # Khi chuyển tab, load lại dữ liệu? Có thể kết nối signal currentChanged
        self.ui.tabWidget.currentChanged.connect(self.on_payment_tab_changed)



        #page nhật ký admin
        self.ui.pushButton_trangchu_7.clicked.connect(lambda: self.switch_page(0))
        self.ui.pushButton_quanlysan_7.clicked.connect(lambda: self.switch_page(1))
        self.ui.pushButton_qldon_7.clicked.connect(lambda: self.switch_page(2))
        self.ui.pushButton_qlkhachhang_7.clicked.connect(lambda: self.switch_page(3))
        self.ui.pushButton_qlkhmai_7.clicked.connect(lambda: self.switch_page(4))
        self.ui.pushButton_ttht_7.clicked.connect(lambda: self.switch_page(5))
        self.ui.pushButton_adminlog_7.clicked.connect(lambda: self.switch_page(6))
        self.ui.pushButton_taikhoan_7.clicked.connect(lambda: self.switch_page(7))
        # Trang nhật ký hệ thống
        self.ui.pushButton_chonadmin.clicked.connect(self.filter_logs_by_admin)


        #page tài khoản
        self.ui.pushButton_trangchu_8.clicked.connect(lambda: self.switch_page(0))
        self.ui.pushButton_quanlysan_8.clicked.connect(lambda: self.switch_page(1))
        self.ui.pushButton_qldon_8.clicked.connect(lambda: self.switch_page(2))
        self.ui.pushButton_qlkhachhang_8.clicked.connect(lambda: self.switch_page(3))
        self.ui.pushButton_qlkhmai_8.clicked.connect(lambda: self.switch_page(4))
        self.ui.pushButton_ttht_8.clicked.connect(lambda: self.switch_page(5))
        self.ui.pushButton_adminlog_8.clicked.connect(lambda: self.switch_page(6))
        self.ui.pushButton_taikhoan_8.clicked.connect(lambda: self.switch_page(7))

        # Trang tài khoản
        self.ui.pushButton_dangxuat.clicked.connect(self.handle_logout)

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
            self.load_payment_data()
        elif index == 6:
            self.load_system_logs()
        elif index == 7:
            self.load_account_info()

    # ==================================================
    # KHU VỰC 3: CÁC HÀM XỬ LÝ (Tạm thời để 'pass' chờ code)
    # ==================================================
    def load_dashboard_data(self):
        self.admin_logic.update_completed_bookings()
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
        self.admin_logic.update_completed_bookings()
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
        self.admin_logic.update_completed_bookings()
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
        """Load danh sách khách hàng lên tableWidget_3"""
        try:
            search = self.ui.lineEdit_timkiem_3.text().strip()
            customer_type = self.ui.comboBox_trangthai_3.currentText()
            customers = self.admin_logic.search_customers(search, customer_type)

            self.ui.tableWidget_3.setRowCount(0)
            self.ui.tableWidget_3.setColumnCount(5)
            self.ui.tableWidget_3.setHorizontalHeaderLabels(["Mã KH", "Họ tên", "SĐT", "Loại", "Số đơn"])

            for row, c in enumerate(customers):
                self.ui.tableWidget_3.insertRow(row)
                item_id = QTableWidgetItem(str(c['customer_id']))
                item_id.setData(Qt.ItemDataRole.UserRole, c['customer_id'])
                self.ui.tableWidget_3.setItem(row, 0, item_id)

                self.ui.tableWidget_3.setItem(row, 1, QTableWidgetItem(c['full_name']))
                self.ui.tableWidget_3.setItem(row, 2, QTableWidgetItem(c['phone_number']))
                self.ui.tableWidget_3.setItem(row, 3, QTableWidgetItem(c['customer_type']))
                self.ui.tableWidget_3.setItem(row, 4, QTableWidgetItem(str(c['total_bookings'])))

            # Căn chỉnh cột
            header = self.ui.tableWidget_3.horizontalHeader()
            header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, header.ResizeMode.Stretch)
            header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, header.ResizeMode.ResizeToContents)
        except Exception as e:
            print(f"❌ Lỗi load_customer_data: {e}")

    def filter_customer_data(self):
        """Lọc khách hàng theo tìm kiếm và loại (gắn với nút Lọc)"""
        self.load_customer_data()

    def handle_view_customer_detail(self):
        """Xem chi tiết khách hàng (gắn với nút Xem chi tiết)"""
        row = self.ui.tableWidget_3.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một khách hàng")
            return
        item = self.ui.tableWidget_3.item(row, 0)
        customer_id = item.data(Qt.ItemDataRole.UserRole)
        dialog = CustomerDetailDialog(customer_id, self.current_admin_id, self)
        dialog.exec()

    def handle_add_customer(self):
        dialog = CustomerEditDialog(self.current_admin_id, None, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_customer_data()
            self.load_dashboard_data()

    def handle_edit_customer(self):
        """Sửa thông tin khách hàng (gắn với nút Chỉnh sửa)"""
        row = self.ui.tableWidget_3.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một khách hàng")
            return
        item = self.ui.tableWidget_3.item(row, 0)
        customer_id = item.data(Qt.ItemDataRole.UserRole)
        customer = self.admin_logic.get_customer_by_id(customer_id)
        if not customer:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy khách hàng")
            return
        dialog = CustomerEditDialog(self.current_admin_id, customer, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_customer_data()
            self.load_dashboard_data()

    def handle_delete_customer(self):
        """Xóa khách hàng (gắn với nút Xóa)"""
        row = self.ui.tableWidget_3.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một khách hàng")
            return
        item = self.ui.tableWidget_3.item(row, 0)
        customer_id = item.data(Qt.ItemDataRole.UserRole)
        customer_name = self.ui.tableWidget_3.item(row, 1).text()

        confirm = QMessageBox.question(
            self, "Xác nhận", f"Bạn có chắc muốn xóa khách hàng {customer_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            success, message = self.admin_logic.delete_customer(self.current_admin_id, customer_id)
            if success:
                QMessageBox.information(self, "Thành công", message)
                self.load_customer_data()
                self.load_dashboard_data()
            else:
                QMessageBox.critical(self, "Lỗi", message)

    def update_customer(self, customer_id, full_name, phone_number):
        existing = db.fetch_one(
            "SELECT customer_id FROM Customer WHERE phone_number = ? AND customer_id != ?",
            (phone_number, customer_id)
        )
        if existing:
            return False, "Số điện thoại đã tồn tại ở khách hàng khác."
        success = db.execute_query(
            "UPDATE Customer SET full_name = ?, phone_number = ? WHERE customer_id = ?",
            (full_name, phone_number, customer_id)
        )
        if success:
            return True, "Cập nhật thành công."
        else:
            return False, "Lỗi khi cập nhật."

    def load_promotion_data(self):
        """Tải danh sách khuyến mãi lên tableWidget_4"""
        try:
            promotions = self.admin_logic.get_all_promotions()
            self.ui.tableWidget_4.setRowCount(0)
            self.ui.tableWidget_4.setColumnCount(6)
            self.ui.tableWidget_4.setHorizontalHeaderLabels(
                ["Mã KM", "Tên chương trình", "Giá trị giảm", "Thời gian áp dụng", "Trạng thái", "Thao tác"]
            )

            for row, p in enumerate(promotions):
                self.ui.tableWidget_4.insertRow(row)
                # Mã KM
                item_id = QTableWidgetItem(str(p['promotion_id']))
                item_id.setData(Qt.ItemDataRole.UserRole, p['promotion_id'])
                self.ui.tableWidget_4.setItem(row, 0, item_id)

                # Tên
                self.ui.tableWidget_4.setItem(row, 1, QTableWidgetItem(p['promotion_name']))

                # Giá trị giảm
                if p['discount_type'] == 'Percentage':
                    value = f"{float(p['discount_value']):g}%"
                else:
                    value = f"{float(p['discount_value']):,.0f} VNĐ"
                self.ui.tableWidget_4.setItem(row, 2, QTableWidgetItem(value))

                # Thời gian
                start = p['start_date']
                end = p['end_date']
                if isinstance(start, datetime):
                    start_str = start.strftime("%d/%m/%Y")
                else:
                    start_str = str(start)
                if isinstance(end, datetime):
                    end_str = end.strftime("%d/%m/%Y")
                else:
                    end_str = str(end)
                self.ui.tableWidget_4.setItem(row, 3, QTableWidgetItem(f"{start_str} - {end_str}"))

                # Trạng thái
                status = "Hoạt động" if p['is_active'] else "Tạm dừng"
                item_status = QTableWidgetItem(status)
                if p['is_active']:
                    item_status.setForeground(QtGui.QColor("#27ae60"))  # xanh
                else:
                    item_status.setForeground(QtGui.QColor("#e74c3c"))  # đỏ
                self.ui.tableWidget_4.setItem(row, 4, item_status)

                # Thao tác (Sửa, Xóa, Bật/Tắt) – dùng nút trong ô
                self._add_action_buttons(row)

            # Căn chỉnh cột
            header = self.ui.tableWidget_4.horizontalHeader()
            header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, header.ResizeMode.Stretch)
            header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, header.ResizeMode.ResizeToContents)
        except Exception as e:
            print(f"❌ Lỗi load_promotion_data: {e}")

    def _add_action_buttons(self, row):
        """Thêm các nút Sửa, Xóa, Bật/Tắt vào hàng row"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        btn_edit = QtWidgets.QPushButton("Sửa")
        btn_edit.setFixedSize(50, 25)
        btn_edit.clicked.connect(lambda: self.edit_promotion(row))

        btn_delete = QtWidgets.QPushButton("Xóa")
        btn_delete.setFixedSize(50, 25)
        btn_delete.clicked.connect(lambda: self.delete_promotion(row))

        btn_toggle = QtWidgets.QPushButton("Bật/Tắt")
        btn_toggle.setFixedSize(70, 25)
        btn_toggle.clicked.connect(lambda: self.toggle_promotion(row))

        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        layout.addWidget(btn_toggle)
        layout.addStretch()
        self.ui.tableWidget_4.setCellWidget(row, 5, widget)

    def edit_promotion(self, row):
        """Sửa khuyến mãi ở hàng row"""
        item = self.ui.tableWidget_4.item(row, 0)
        promotion_id = item.data(Qt.ItemDataRole.UserRole)
        promotion = self.admin_logic.get_promotion_by_id(promotion_id)
        if not promotion:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy khuyến mãi")
            return
        dialog = PromotionDialog(self.current_admin_id, promotion, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_promotion_data()

    def delete_promotion(self, row):
        """Xóa khuyến mãi ở hàng row"""
        item = self.ui.tableWidget_4.item(row, 0)
        promotion_id = item.data(Qt.ItemDataRole.UserRole)
        promotion_name = self.ui.tableWidget_4.item(row, 1).text()
        confirm = QMessageBox.question(
            self, "Xác nhận", f"Bạn có chắc muốn xóa khuyến mãi '{promotion_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            success, message = self.admin_logic.delete_promotion(self.current_admin_id, promotion_id)
            if success:
                QMessageBox.information(self, "Thành công", message)
                self.load_promotion_data()
            else:
                QMessageBox.critical(self, "Lỗi", message)

    def toggle_promotion(self, row):
        """Bật/tắt trạng thái khuyến mãi"""
        item = self.ui.tableWidget_4.item(row, 0)
        promotion_id = item.data(Qt.ItemDataRole.UserRole)
        current_status_item = self.ui.tableWidget_4.item(row, 4)
        current_status = current_status_item.text()
        new_status = 0 if current_status == "Hoạt động" else 1
        action = "tắt" if new_status == 0 else "bật"
        confirm = QMessageBox.question(
            self, "Xác nhận", f"Bạn có chắc muốn {action} khuyến mãi này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            success, message = self.admin_logic.toggle_promotion_status(self.current_admin_id, promotion_id, new_status)
            if success:
                QMessageBox.information(self, "Thành công", message)
                self.load_promotion_data()
            else:
                QMessageBox.critical(self, "Lỗi", message)

    def handle_add_promotion(self):
        """Thêm khuyến mãi mới (gắn với nút Thêm)"""
        dialog = PromotionDialog(self.current_admin_id, None, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_promotion_data()

    def load_payment_data(self):
        """Load dữ liệu cho cả 3 tab thanh toán"""
        self.load_pending_payments()
        self.load_completed_payments()
        self.load_refund_requests()

    def load_pending_payments(self):
        try:
            data = self.admin_logic.get_pending_payments()
            self.ui.tableWidget_5.setRowCount(0)
            self.ui.tableWidget_5.setColumnCount(6)
            self.ui.tableWidget_5.setHorizontalHeaderLabels(
                ["Mã đơn", "Khách hàng", "SĐT", "Ngày đặt", "Tổng tiền", "Trạng thái thanh toán"]
            )
            for row, item in enumerate(data):
                self.ui.tableWidget_5.insertRow(row)
                item_id = QTableWidgetItem(str(item['booking_id']))
                item_id.setData(Qt.ItemDataRole.UserRole, item['booking_id'])
                self.ui.tableWidget_5.setItem(row, 0, item_id)
                self.ui.tableWidget_5.setItem(row, 1, QTableWidgetItem(item['full_name']))
                self.ui.tableWidget_5.setItem(row, 2, QTableWidgetItem(item['phone_number']))
                date_val = item['booking_date']
                if isinstance(date_val, datetime):
                    date_str = date_val.strftime("%d/%m/%Y %H:%M")
                else:
                    date_str = str(date_val)
                self.ui.tableWidget_5.setItem(row, 3, QTableWidgetItem(date_str))
                self.ui.tableWidget_5.setItem(row, 4, QTableWidgetItem(f"{item['total_amount']:,.0f} đ"))
                payment_status = item.get('payment_status', 'Chưa có')
                self.ui.tableWidget_5.setItem(row, 5, QTableWidgetItem(payment_status))
            # Căn chỉnh cột
            header = self.ui.tableWidget_5.horizontalHeader()
            header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, header.ResizeMode.Stretch)
            header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, header.ResizeMode.ResizeToContents)
        except Exception as e:
            print(f"❌ Lỗi load_pending_payments: {e}")

    def load_completed_payments(self):
        """Tab 1: Đã thanh toán - dùng tableWidget_7"""
        try:
            data = self.admin_logic.get_completed_payments()
            self.ui.tableWidget_7.setRowCount(0)
            self.ui.tableWidget_7.setColumnCount(6)
            self.ui.tableWidget_7.setHorizontalHeaderLabels(
                ["Mã đơn", "Khách hàng", "SĐT", "Ngày thanh toán", "Tổng tiền", "Phương thức"]
            )
            for row, item in enumerate(data):
                self.ui.tableWidget_7.insertRow(row)
                item_id = QTableWidgetItem(str(item['booking_id']))
                item_id.setData(Qt.ItemDataRole.UserRole, item['booking_id'])
                self.ui.tableWidget_7.setItem(row, 0, item_id)
                self.ui.tableWidget_7.setItem(row, 1, QTableWidgetItem(item['full_name']))
                self.ui.tableWidget_7.setItem(row, 2, QTableWidgetItem(item['phone_number']))
                date_val = item['payment_date']
                if isinstance(date_val, datetime):
                    date_str = date_val.strftime("%d/%m/%Y %H:%M")
                else:
                    date_str = str(date_val)
                self.ui.tableWidget_7.setItem(row, 3, QTableWidgetItem(date_str))
                self.ui.tableWidget_7.setItem(row, 4, QTableWidgetItem(f"{item['total_amount']:,.0f} đ"))
                self.ui.tableWidget_7.setItem(row, 5, QTableWidgetItem(item['payment_method']))
            # Căn chỉnh cột
            header = self.ui.tableWidget_7.horizontalHeader()
            header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, header.ResizeMode.Stretch)
            header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, header.ResizeMode.ResizeToContents)
        except Exception as e:
            print(f"❌ Lỗi load_completed_payments: {e}")

    def load_refund_requests(self):
        """Tab 2: Hoàn tiền - dùng tableWidget_6"""
        try:
            data = self.admin_logic.get_cancelled_bookings_for_refund()
            self.ui.tableWidget_6.setRowCount(0)
            self.ui.tableWidget_6.setColumnCount(6)
            self.ui.tableWidget_6.setHorizontalHeaderLabels(
                ["Mã đơn", "Khách hàng", "SĐT", "Ngày hủy", "Tổng tiền", "Trạng thái thanh toán"]
            )
            for row, item in enumerate(data):
                self.ui.tableWidget_6.insertRow(row)
                item_id = QTableWidgetItem(str(item['booking_id']))
                item_id.setData(Qt.ItemDataRole.UserRole, item['booking_id'])
                self.ui.tableWidget_6.setItem(row, 0, item_id)
                self.ui.tableWidget_6.setItem(row, 1, QTableWidgetItem(item['full_name']))
                self.ui.tableWidget_6.setItem(row, 2, QTableWidgetItem(item['phone_number']))
                date_val = item['booking_date']
                if isinstance(date_val, datetime):
                    date_str = date_val.strftime("%d/%m/%Y %H:%M")
                else:
                    date_str = str(date_val)
                self.ui.tableWidget_6.setItem(row, 3, QTableWidgetItem(date_str))
                self.ui.tableWidget_6.setItem(row, 4, QTableWidgetItem(f"{item['total_amount']:,.0f} đ"))
                payment_status = item.get('payment_status', 'Chưa có')
                self.ui.tableWidget_6.setItem(row, 5, QTableWidgetItem(payment_status))
            # Căn chỉnh cột
            header = self.ui.tableWidget_6.horizontalHeader()
            header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, header.ResizeMode.Stretch)
            header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, header.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, header.ResizeMode.ResizeToContents)
        except Exception as e:
            print(f"❌ Lỗi load_refund_requests: {e}")

    def handle_confirm_payment(self):
        """Xác nhận thanh toán cho đơn được chọn trong tab chờ (tableWidget_5)"""
        current_row = self.ui.tableWidget_5.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một đơn cần xác nhận thanh toán")
            return
        item = self.ui.tableWidget_5.item(current_row, 0)
        booking_id = item.data(Qt.ItemDataRole.UserRole)

        confirm = QMessageBox.question(
            self, "Xác nhận", f"Bạn có chắc đã nhận thanh toán cho đơn #{booking_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            success, message = self.admin_logic.confirm_payment(self.current_admin_id, booking_id)
            if success:
                QMessageBox.information(self, "Thành công", message)
                self.load_pending_payments()
                self.load_completed_payments()
                self.load_dashboard_data()
            else:
                QMessageBox.critical(self, "Lỗi", message)

    def handle_create_refund_from_completed(self):
        current_row = self.ui.tableWidget_7.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Thông báo", "Vui lòng chọn một đơn từ danh sách đã thanh toán")
            return

        # Lấy thông tin đơn
        item_id = self.ui.tableWidget_7.item(current_row, 0)
        booking_id = item_id.data(Qt.ItemDataRole.UserRole)
        total_amount = self.ui.tableWidget_7.item(current_row, 4).text().replace(' đ', '').replace(',', '')

        booking = self.admin_logic.get_booking_by_id(booking_id)
        if not booking:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy thông tin đơn")
            return
        if booking['status'] == 'Cancelled':
            QMessageBox.warning(self, "Thông báo", "Đơn này đã được hủy trước đó")
            return
        if booking['status'] != 'Confirmed':
            QMessageBox.warning(self, "Thông báo", "Đơn chưa được thanh toán, không thể hoàn tiền")
            return

        reason, ok = QInputDialog.getText(self, "Hoàn tiền", "Nhập lý do hủy và hoàn tiền:")
        if not ok or not reason.strip():
            return

        confirm = QMessageBox.question(
            self, "Xác nhận", f"Bạn có chắc muốn hủy đơn #{booking_id} và hoàn tiền {total_amount} đ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        from app_admin.core_admin.refund_logic import RefundLogic
        refund_logic = RefundLogic()
        success, message = refund_logic.process_refund(self.current_admin_id, booking_id, reason)

        if success:
            # Cập nhật trạng thái sân
            details = self.admin_logic.get_booking_details(booking_id)
            court_ids = list(set(d['court_id'] for d in details))
            from app_admin.core_admin.court_logic import CourtLogic
            court_logic = CourtLogic()
            for court_id in court_ids:
                court_logic.update_court_status_based_on_bookings(court_id)

            QMessageBox.information(self, "Thành công", message)
            self.load_completed_payments()
            self.load_refund_requests()
            self.load_dashboard_data()
        else:
            QMessageBox.critical(self, "Lỗi", message)

    def on_payment_tab_changed(self, index):
        """Load lại dữ liệu khi chuyển tab thanh toán"""
        if index == 0:  # Tab 0: Chờ thanh toán
            self.load_pending_payments()
        elif index == 1:  # Tab 1: Đã thanh toán
            self.load_completed_payments()
        elif index == 2:  # Tab 2: Hoàn tiền
            self.load_refund_requests()
    def load_financial_data(self):
        self.load_payment_data()

    def load_system_logs(self):
        try:
            self.load_admin_combobox()
            logs = self.logger.get_all_logs()  # dùng self.logger, không phải self.admin_logic
            self.display_logs(logs)
        except Exception as e:
            print(f"❌ Lỗi load_system_logs: {e}")

    def load_admin_combobox(self):
        """Lấy danh sách admin từ database và đổ vào comboBox"""
        # Giả sử admin_logic có method get_all_admins()
        admins = self.admin_logic.get_all_admins()
        self.ui.comboBox.clear()
        self.ui.comboBox.addItem("Tất cả admin", None)
        for admin in admins:
            self.ui.comboBox.addItem(admin['full_name'], admin['admin_id'])

    def filter_logs_by_admin(self):
        admin_id = self.ui.comboBox.currentData()
        if admin_id is None:
            logs = self.logger.get_all_logs()
        else:
            logs = self.logger.get_logs_by_admin(admin_id)  # dùng self.logger
        self.display_logs(logs)

    def display_logs(self, logs):
        """Hiển thị danh sách log lên tableWidget_9"""
        self.ui.tableWidget_9.setRowCount(0)
        self.ui.tableWidget_9.setColumnCount(4)
        self.ui.tableWidget_9.setHorizontalHeaderLabels(["Thời gian", "Admin", "Hành động", "Chi tiết"])

        for row, log in enumerate(logs):
            self.ui.tableWidget_9.insertRow(row)

            # Cột 0: Thời gian
            time_val = log['created_at']
            if isinstance(time_val, datetime):
                time_str = time_val.strftime("%d/%m/%Y %H:%M:%S")
            else:
                time_str = str(time_val)
            self.ui.tableWidget_9.setItem(row, 0, QTableWidgetItem(time_str))

            # Cột 1: Admin (tên)
            admin_name = log.get('full_name', f"Admin #{log['admin_id']}")
            self.ui.tableWidget_9.setItem(row, 1, QTableWidgetItem(admin_name))

            # Cột 2: Hành động (action_type)
            self.ui.tableWidget_9.setItem(row, 2, QTableWidgetItem(log['action_type']))

            # Cột 3: Chi tiết
            detail = f"{log['target_table']} #{log['target_id']}"
            if log.get('reason'):
                detail += f" - {log['reason']}"
            self.ui.tableWidget_9.setItem(row, 3, QTableWidgetItem(detail))

        # Căn chỉnh cột
        header = self.ui.tableWidget_9.horizontalHeader()
        header.setSectionResizeMode(0, header.ResizeMode.ResizeToContents)  # Thời gian
        header.setSectionResizeMode(1, header.ResizeMode.ResizeToContents)  # Admin
        header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)  # Hành động
        header.setSectionResizeMode(3, header.ResizeMode.Stretch)  # Chi tiết

    def load_account_info(self):
        """Hiển thị thông tin tài khoản admin hiện tại"""
        try:
            admin = self.admin_logic.get_admin_by_id(self.current_admin_id)
            if admin:
                self.ui.lineEdit_hvt.setText(admin['full_name'])
                self.ui.lineEdit_aadim.setText(str(admin['admin_id']))
                self.ui.lineEdit_chucvu.setText(admin['role'])
                self.ui.lineEdit_tendangnhap.setText(admin['username'])
                # Đặt các ô ở chế độ chỉ đọc
                self.ui.lineEdit_hvt.setReadOnly(True)
                self.ui.lineEdit_aadim.setReadOnly(True)
                self.ui.lineEdit_chucvu.setReadOnly(True)
                self.ui.lineEdit_tendangnhap.setReadOnly(True)
            else:
                print("Không tìm thấy admin")
        except Exception as e:
            print(f"❌ Lỗi load_account_info: {e}")

    def handle_logout(self):
        """Đăng xuất khỏi hệ thống"""
        reply = QMessageBox.question(
            self, "Xác nhận", "Bạn có chắc muốn đăng xuất?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Đóng cửa sổ hiện tại
            self.close()
            # Nếu có màn hình login, có thể mở lại ở đây (tùy chọn)
            # from app_admin.views_admin.login_view import LoginView
            # self.login_window = LoginView()
            # self.login_window.show()
            # Tạm thời thoát ứng dụng
            import sys
            sys.exit(0)


