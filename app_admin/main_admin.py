import sys
from PyQt6.QtWidgets import QApplication
from views_admin.views.main_admin_view import MainAdminView

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Mở màn hình quản lý
    main_window = MainAdminView()
    main_window.show()

    sys.exit(app.exec())