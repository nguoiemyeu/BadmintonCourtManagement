from datetime import datetime, timedelta, time

# Cấu hình hằng số để dễ bảo trì
PRICE_BEFORE_17 = 60000
PRICE_AFTER_17 = 80000
MEMBER_DISCOUNT = 0.05  # 5%

def parse_datetime(datetime_str):
    """Chuyển chuỗi từ UI/DB thành datetime."""
    try:
        return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
    except ValueError:
        return None

def is_valid_time_range(start_time, end_time):
    """Kiểm tra thời gian hợp lệ và cùng một ngày."""
    if end_time <= start_time:
        return False, "Thời gian kết thúc phải sau thời gian bắt đầu."
    if start_time.date() != end_time.date():
        return False, "Hệ thống chỉ hỗ trợ đặt sân trong cùng một ngày."
    return True, ""

def is_time_overlap(start1, end1, start2, end2):
    """Kiểm tra trùng lịch (Dùng cho logic tìm sân trống)."""
    return start1 < end2 and start2 < end1

def can_cancel_booking(start_time):
    """Kiểm tra điều kiện hủy trước 3 giờ."""
    now = datetime.now()
    # Nếu thời gian hiện tại đã qua thời gian bắt đầu thì không thể hủy
    if now >= start_time:
        return False
    return (start_time - now) >= timedelta(hours=3)

def calculate_time_based_price(start_time, end_time):
    """
    Tính tiền tối ưu: Chia làm 2 khoảng dựa trên mốc 17:00.
    """
    valid, msg = is_valid_time_range(start_time, end_time)
    if not valid:
        return 0

    # Mốc 17h của ngày đặt sân
    pivot_time = datetime.combine(start_time.date(), time(17, 0))

    # Khoảng 1: Trước 17h
    before_17_start = start_time
    before_17_end = min(end_time, pivot_time)
    duration_before = max(0, (before_17_end - before_17_start).total_seconds() / 3600)

    # Khoảng 2: Sau 17h
    after_17_start = max(start_time, pivot_time)
    after_17_end = end_time
    duration_after = max(0, (after_17_end - after_17_start).total_seconds() / 3600)

    total = (duration_before * PRICE_BEFORE_17) + (duration_after * PRICE_AFTER_17)
    return round(total, -2) # Làm tròn đến hàng trăm (VD: 120.050 -> 120.100)

def apply_member_discount(total_amount, is_member):
    """Áp dụng giảm giá thành viên."""
    if is_member:
        return total_amount * (1 - MEMBER_DISCOUNT)
    return total_amount