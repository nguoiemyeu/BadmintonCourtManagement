import re


# ==============================
# 1. KIỂM TRA RỖNG
# ==============================
def is_not_empty(value):
    """Kiểm tra giá trị không được rỗng hoặc chỉ toàn khoảng trắng."""
    return value is not None and str(value).strip() != ""


# ==============================
# 2. VALIDATE SỐ ĐIỆN THOẠI (VIỆT NAM)
# ==============================
def validate_phone(phone):
    """
    Kiểm tra số điện thoại Việt Nam.
    Trả về: (True/False, "Thông báo lỗi")
    """
    if not is_not_empty(phone):
        return False, "Số điện thoại không được để trống."

    # Loại bỏ các ký tự không phải số (dấu cách, dấu chấm, dấu gạch ngang)
    clean_phone = re.sub(r"\D", "", str(phone))

    pattern = r"^(0[3|5|7|8|9])([0-9]{8})$"
    if re.match(pattern, clean_phone):
        return True, ""
    return False, "Số điện thoại không hợp lệ (Phải có 10 số, bắt đầu bằng 03, 05, 07, 08, 09)."


# ==============================
# 3. VALIDATE EMAIL
# ==============================
def validate_email(email):
    if not is_not_empty(email):
        return False, "Email không được để trống."

    # Regex chuẩn hơn cho Email
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if re.match(pattern, str(email)):
        return True, ""
    return False, "Định dạng Email không hợp lệ."


# ==============================
# 4. VALIDATE USERNAME
# ==============================
def validate_username(username):
    if not is_not_empty(username):
        return False, "Tên đăng nhập không được để trống."

    if len(str(username)) < 4:
        return False, "Tên đăng nhập phải có ít nhất 4 ký tự."

    pattern = r"^[a-zA-Z0-9_]+$"
    if re.match(pattern, str(username)):
        return True, ""
    return False, "Tên đăng nhập chỉ được chứa chữ cái, số và dấu gạch dưới."


# ==============================
# 5. VALIDATE PASSWORD
# ==============================
def validate_password(password):
    if not is_not_empty(password):
        return False, "Mật khẩu không được để trống."

    pwd_str = str(password)
    if len(pwd_str) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự."

    if " " in pwd_str:
        return False, "Mật khẩu không được chứa khoảng trắng."

    return True, ""


# ==============================
# 6. KIỂM TRA SỐ DƯƠNG
# ==============================
def is_positive_number(value):
    try:
        num = float(value)
        return num > 0
    except (ValueError, TypeError):
        return False