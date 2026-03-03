USE master;
GO
IF DB_ID('BadmintonCourtManagement') IS NOT NULL
BEGIN
    ALTER DATABASE BadmintonCourtManagement 
    SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE BadmintonCourtManagement;
END
GO

CREATE DATABASE BadmintonCourtManagement;
GO
USE BadmintonCourtManagement;
GO

-- =====================================================
-- 1. TẠO CÁC BẢNG
-- =====================================================

CREATE TABLE CUSTOMER (
    customer_id INT IDENTITY(1,1) PRIMARY KEY,
    full_name NVARCHAR(100) NOT NULL,
    phone_number VARCHAR(15) NOT NULL UNIQUE,
    created_at DATETIME DEFAULT GETDATE()
);

CREATE TABLE MEMBER (
    customer_id INT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    register_date DATETIME DEFAULT GETDATE(),
    status VARCHAR(20) DEFAULT 'Active',
    FOREIGN KEY (customer_id) REFERENCES CUSTOMER(customer_id)
);

CREATE TABLE ADMIN (
    admin_id INT IDENTITY(1,1) PRIMARY KEY,
    full_name NVARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'Staff',
    status VARCHAR(20) DEFAULT 'Active'
);

CREATE TABLE COURT (
    court_id INT IDENTITY(1,1) PRIMARY KEY,
    court_code VARCHAR(10) NOT NULL UNIQUE,
    status VARCHAR(20) DEFAULT 'Available'
);

CREATE TABLE PROMOTION (
    promotion_id INT IDENTITY(1,1) PRIMARY KEY,
    promotion_name NVARCHAR(100) NOT NULL,
    discount_type VARCHAR(20) NOT NULL, 
    discount_value DECIMAL(10,2) NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    is_active BIT DEFAULT 1,
    CHECK (start_date < end_date)
);

CREATE TABLE BOOKING (
    booking_id INT IDENTITY(1,1) PRIMARY KEY,
    customer_id INT NOT NULL,
    promotion_id INT NULL,
    booking_date DATETIME DEFAULT GETDATE(),
    status VARCHAR(20) DEFAULT 'Pending', 
    total_amount DECIMAL(10,2) DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES CUSTOMER(customer_id),
    FOREIGN KEY (promotion_id) REFERENCES PROMOTION(promotion_id)
);

CREATE TABLE BOOKING_DETAIL (
    booking_detail_id INT IDENTITY(1,1) PRIMARY KEY,
    booking_id INT NOT NULL,
    court_id INT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    price_per_hour DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES BOOKING(booking_id),
    FOREIGN KEY (court_id) REFERENCES COURT(court_id),
    CHECK (end_time > start_time)
);

CREATE TABLE PAYMENT (
    payment_id INT IDENTITY(1,1) PRIMARY KEY,
    booking_id INT NOT NULL UNIQUE, 
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    payment_date DATETIME DEFAULT GETDATE(),
    status VARCHAR(20) DEFAULT 'Pending', 
    FOREIGN KEY (booking_id) REFERENCES BOOKING(booking_id)
);

CREATE TABLE REFUND (
    refund_id INT IDENTITY(1,1) PRIMARY KEY,
    booking_id INT NOT NULL UNIQUE, 
    refund_amount DECIMAL(10,2) NOT NULL,
    refund_date DATETIME DEFAULT GETDATE(),
    reason NVARCHAR(255),
    FOREIGN KEY (booking_id) REFERENCES BOOKING(booking_id)
);

CREATE TABLE ADMIN_LOG (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    admin_id INT NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    target_table VARCHAR(50) NOT NULL,
    target_id INT NOT NULL,
    reason NVARCHAR(255),
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (admin_id) REFERENCES ADMIN(admin_id)
);
GO

-- =====================================================
-- 2. THÊM CÁC RÀNG BUỘC BỔ SUNG
-- =====================================================

ALTER TABLE COURT ADD CONSTRAINT check_court_status 
CHECK (status IN ('Available', 'Booked', 'Maintenance'));

ALTER TABLE BOOKING ADD CONSTRAINT check_booking_status 
CHECK (status IN ('Pending', 'Confirmed', 'Cancelled', 'Completed'));

ALTER TABLE PAYMENT ADD CONSTRAINT check_payment_status 
CHECK (status IN ('Pending', 'Success', 'Failed'));

ALTER TABLE MEMBER ADD CONSTRAINT check_member_status 
CHECK (status IN ('Active', 'Inactive'));

ALTER TABLE PROMOTION ADD CONSTRAINT check_discount_type 
CHECK (discount_type IN ('Percentage', 'Fixed'));
GO

-- =====================================================
-- 3. TRIGGER KIỂM TRA KHÔNG TRÙNG LỊCH ĐẶT SÂN
-- =====================================================
CREATE TRIGGER trg_check_court_availability
ON BOOKING_DETAIL
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM BOOKING_DETAIL bd
        INNER JOIN inserted i ON bd.court_id = i.court_id
        WHERE bd.booking_detail_id != i.booking_detail_id
            AND bd.start_time < i.end_time
            AND bd.end_time > i.start_time
            AND EXISTS (
                SELECT 1 FROM BOOKING b 
                WHERE b.booking_id = bd.booking_id 
                AND b.status != 'Cancelled'
            )
            AND EXISTS (
                SELECT 1 FROM BOOKING b 
                WHERE b.booking_id = i.booking_id 
                AND b.status != 'Cancelled'
            )
    )
    BEGIN
        RAISERROR('Court is already booked for the selected time!', 16, 1);
        ROLLBACK TRANSACTION;
    END
END;
GO

-- (ĐÃ XÓA PHẦN 4: KHÔNG CẦN DELETE VÀ DBCC CHECKIDENT VÌ DB ĐÃ TẠO MỚI)

-- =====================================================
-- 5. CHÈN DỮ LIỆU MẪU
-- =====================================================

-- 5.1. COURT
INSERT INTO COURT (court_code, status) VALUES
('A01', 'Available'), ('A02', 'Available'), ('B01', 'Available'), ('B02', 'Available'),
('C01', 'Available'), ('C02', 'Available'), ('D01', 'Available'), ('D02', 'Available'),
('E01', 'Maintenance'), ('E02', 'Available'), ('F01', 'Available'), ('F02', 'Available');
GO

-- 5.2. ADMIN
INSERT INTO ADMIN (full_name, username, password_hash, role, status) VALUES
(N'Nguyễn Văn An', 'admin01', 'hash_admin_1', 'Super Admin', 'Active'),
(N'Trần Thị Bình', 'admin02', 'hash_admin_2', 'Manager', 'Active'),
(N'Lê Hoàng Cường', 'admin03', 'hash_admin_3', 'Staff', 'Active');
GO

-- 5.3. CUSTOMER
INSERT INTO CUSTOMER (full_name, phone_number) VALUES
(N'Phạm Văn Dũng', '0901111111'), (N'Nguyễn Thị Lan', '0902222222'), (N'Trần Văn Minh', '0903333333'),
(N'Lê Thị Hoa', '0904444444'), (N'Hoàng Văn Tuấn', '0905555555'), (N'Đặng Thị Ngọc', '0906666666'),
(N'Bùi Quang Huy', '0907777777'), (N'Vũ Thị Hạnh', '0908888888'), (N'Đỗ Văn Khải', '0909999999'),
(N'Phan Thị Thảo', '0910000000'), (N'Ngô Văn Long', '0910000001'), (N'Trịnh Thị Mai', '0910000002'),
(N'Phùng Minh Đức', '0910000003'), (N'Võ Thị Như', '0910000004'), (N'Hoàng Nhật Anh', '0910000005'),
(N'Lý Thanh Tùng', '0910000006'), (N'Tô Minh Châu', '0910000007'), (N'Dương Hoài Nam', '0910000008'),
(N'Bạch Quỳnh Anh', '0910000009'), (N'Tạ Quốc Bảo', '0910000010');
GO

-- 5.4. MEMBER
INSERT INTO MEMBER (customer_id, username, password_hash, status) VALUES
(1, 'phamdung', 'hash_mem_1', 'Active'),
(2, 'nguyentlan', 'hash_mem_2', 'Active'),
(3, 'tranminh', 'hash_mem_3', 'Inactive'),
(4, 'lethihoa', 'hash_mem_4', 'Active'),
(5, 'hoangtuan', 'hash_mem_5', 'Active');
GO

-- 5.5. PROMOTION
INSERT INTO PROMOTION (promotion_name, discount_type, discount_value, start_date, end_date, is_active) VALUES
(N'Khuyến mãi tháng 2', 'Percentage', 10.00, '2026-02-01', '2026-02-28', 1),
(N'Giảm giá thành viên', 'Percentage', 5.00, '2026-01-01', '2026-12-31', 1),
(N'Ưu đãi sáng sớm', 'Fixed', 20000.00, '2026-02-01', '2026-02-28', 1),
(N'Tết nguyên đán', 'Percentage', 15.00, '2026-02-10', '2026-02-20', 1);
GO

-- 5.6. BOOKING
INSERT INTO BOOKING (customer_id, promotion_id, booking_date, status, total_amount) VALUES
(1, 2, '2026-02-01 08:30:00', 'Completed', 240000), (2, NULL, '2026-02-01 09:15:00', 'Completed', 320000),
(3, 1, '2026-02-01 14:00:00', 'Completed', 180000), (4, NULL, '2026-02-02 16:30:00', 'Cancelled', 280000),
(5, 3, '2026-02-02 18:00:00', 'Confirmed', 400000), (6, NULL, '2026-02-03 07:00:00', 'Pending', 120000),
(7, 2, '2026-02-03 10:00:00', 'Confirmed', 360000), (8, NULL, '2026-02-03 19:00:00', 'Pending', 160000),
(9, 1, '2026-02-04 06:00:00', 'Completed', 240000), (10, NULL, '2026-02-04 12:00:00', 'Completed', 280000),
(11, 4, '2026-02-04 17:00:00', 'Confirmed', 240000), (12, NULL, '2026-02-05 09:30:00', 'Pending', 200000),
(13, 2, '2026-02-05 15:00:00', 'Completed', 360000), (14, NULL, '2026-02-05 20:00:00', 'Cancelled', 160000),
(15, 1, '2026-02-06 08:00:00', 'Confirmed', 320000), (16, NULL, '2026-02-06 13:30:00', 'Pending', 240000),
(17, 3, '2026-02-06 18:30:00', 'Confirmed', 400000), (18, NULL, '2026-02-07 07:30:00', 'Completed', 120000),
(19, 2, '2026-02-07 11:00:00', 'Pending', 200000), (20, NULL, '2026-02-07 16:00:00', 'Confirmed', 320000);
GO

-- 5.7. BOOKING_DETAIL
INSERT INTO BOOKING_DETAIL (booking_id, court_id, start_time, end_time, price_per_hour, subtotal) VALUES
(1, 1, '2026-02-01 08:00:00', '2026-02-01 10:00:00', 60000, 120000),
(5, 1, '2026-02-02 18:00:00', '2026-02-02 20:00:00', 80000, 160000),
(9, 1, '2026-02-04 06:00:00', '2026-02-04 08:00:00', 60000, 120000),
(2, 2, '2026-02-01 09:00:00', '2026-02-01 11:00:00', 60000, 120000),
(6, 2, '2026-02-03 07:00:00', '2026-02-03 09:00:00', 60000, 120000),
(10, 2, '2026-02-04 12:00:00', '2026-02-04 14:00:00', 60000, 120000),
(15, 2, '2026-02-06 08:00:00', '2026-02-06 10:00:00', 60000, 120000),
(3, 3, '2026-02-01 14:00:00', '2026-02-01 16:00:00', 60000, 120000),
(7, 3, '2026-02-03 10:00:00', '2026-02-03 12:00:00', 60000, 120000),
(11, 3, '2026-02-04 17:00:00', '2026-02-04 19:00:00', 80000, 160000),
(16, 3, '2026-02-06 13:30:00', '2026-02-06 15:30:00', 60000, 120000),
(4, 4, '2026-02-02 16:30:00', '2026-02-02 18:30:00', 80000, 160000),
(8, 4, '2026-02-03 19:00:00', '2026-02-03 21:00:00', 80000, 160000),
(12, 4, '2026-02-05 09:30:00', '2026-02-05 11:30:00', 60000, 120000),
(17, 4, '2026-02-06 18:30:00', '2026-02-06 20:30:00', 80000, 160000),
(13, 5, '2026-02-05 15:00:00', '2026-02-05 17:00:00', 60000, 120000),
(18, 5, '2026-02-07 07:30:00', '2026-02-07 09:30:00', 60000, 120000),
(14, 6, '2026-02-05 20:00:00', '2026-02-05 22:00:00', 80000, 160000),
(19, 6, '2026-02-07 11:00:00', '2026-02-07 13:00:00', 60000, 120000),
(20, 7, '2026-02-07 16:00:00', '2026-02-07 18:00:00', 80000, 160000),
(2, 7, '2026-02-01 15:00:00', '2026-02-01 17:00:00', 60000, 120000),
(3, 8, '2026-02-01 16:30:00', '2026-02-01 18:00:00', 80000, 120000),
(7, 8, '2026-02-03 13:00:00', '2026-02-03 15:00:00', 60000, 120000),
(5, 10, '2026-02-02 20:00:00', '2026-02-02 22:00:00', 80000, 160000),
(11, 10, '2026-02-04 19:30:00', '2026-02-04 21:00:00', 80000, 120000),
(1, 11, '2026-02-01 10:30:00', '2026-02-01 12:30:00', 60000, 120000),
(9, 11, '2026-02-04 08:30:00', '2026-02-04 10:30:00', 60000, 120000),
(4, 12, '2026-02-02 17:00:00', '2026-02-02 19:00:00', 80000, 160000),
(13, 12, '2026-02-05 17:30:00', '2026-02-05 19:30:00', 80000, 160000);
GO

-- 5.8. Cập nhật tổng tiền cho BOOKING
UPDATE BOOKING SET total_amount = (
    SELECT ISNULL(SUM(subtotal), 0)
    FROM BOOKING_DETAIL
    WHERE BOOKING_DETAIL.booking_id = BOOKING.booking_id
);
GO

-- 5.9. PAYMENT
INSERT INTO PAYMENT (booking_id, amount, payment_method, payment_date, status) VALUES
(1, 240000, 'Bank transfer', '2026-02-01 08:45:00', 'Success'),
(2, 320000, 'Cash', '2026-02-01 09:30:00', 'Success'),
(3, 180000, 'Bank transfer', '2026-02-01 14:15:00', 'Success'),
(4, 280000, 'Bank transfer', '2026-02-02 16:45:00', 'Failed'),
(5, 400000, 'Bank transfer', '2026-02-02 18:15:00', 'Pending'),
(7, 360000, 'Cash', '2026-02-03 10:30:00', 'Success'),
(9, 240000, 'Bank transfer', '2026-02-04 06:15:00', 'Success'),
(10, 280000, 'Bank transfer', '2026-02-04 12:30:00', 'Success'),
(11, 240000, 'Bank transfer', '2026-02-04 17:15:00', 'Success'),
(13, 360000, 'Cash', '2026-02-05 15:30:00', 'Success'),
(15, 320000, 'Bank transfer', '2026-02-06 08:20:00', 'Pending'),
(17, 400000, 'Bank transfer', '2026-02-06 19:00:00', 'Success'),
(18, 120000, 'Cash', '2026-02-07 07:50:00', 'Success'),
(19, 200000, 'Bank transfer', '2026-02-07 11:30:00', 'Pending'),
(20, 320000, 'Bank transfer', '2026-02-07 16:20:00', 'Success');
GO

-- 5.10. Thêm 3 booking mới để có dữ liệu hoàn tiền
INSERT INTO BOOKING (customer_id, promotion_id, booking_date, status, total_amount) VALUES
(2, 1, '2026-02-08 09:00:00', 'Cancelled', 180000),
(3, NULL, '2026-02-08 14:00:00', 'Cancelled', 280000),
(4, 2, '2026-02-09 18:00:00', 'Cancelled', 280000);
GO

DECLARE @max_booking INT = (SELECT MAX(booking_id) FROM BOOKING);
INSERT INTO BOOKING_DETAIL (booking_id, court_id, start_time, end_time, price_per_hour, subtotal) VALUES
(@max_booking-2, 1, '2026-02-08 09:00:00', '2026-02-08 11:00:00', 60000, 120000),
(@max_booking-2, 2, '2026-02-08 11:00:00', '2026-02-08 12:00:00', 60000, 60000),
(@max_booking-1, 3, '2026-02-08 14:00:00', '2026-02-08 16:00:00', 60000, 120000),
(@max_booking-1, 4, '2026-02-08 16:00:00', '2026-02-08 18:00:00', 80000, 160000),
(@max_booking, 5, '2026-02-09 18:00:00', '2026-02-09 20:00:00', 80000, 160000),
(@max_booking, 6, '2026-02-09 20:00:00', '2026-02-09 21:30:00', 80000, 120000);
GO

UPDATE BOOKING SET total_amount = (
    SELECT ISNULL(SUM(subtotal), 0)
    FROM BOOKING_DETAIL
    WHERE BOOKING_DETAIL.booking_id = BOOKING.booking_id
) WHERE booking_id > 20;
GO

DECLARE @max_booking INT = (SELECT MAX(booking_id) FROM BOOKING);
INSERT INTO PAYMENT (booking_id, amount, payment_method, payment_date, status) VALUES
(@max_booking-2, 180000, 'Bank transfer', '2026-02-07 10:00:00', 'Success'),
(@max_booking-1, 280000, 'Cash', '2026-02-07 15:00:00', 'Success'),
(@max_booking, 280000, 'Bank transfer', '2026-02-08 09:00:00', 'Success');
GO

DECLARE @max_booking INT = (SELECT MAX(booking_id) FROM BOOKING);
INSERT INTO REFUND (booking_id, refund_amount, refund_date, reason) VALUES
(@max_booking-2, 180000, '2026-02-08 10:30:00', N'Hủy đơn trước 3h'),
(@max_booking-1, 280000, '2026-02-08 16:30:00', N'Hủy do sân bảo trì'),
(@max_booking, 280000, '2026-02-09 19:00:00', N'Khách đổi lịch');
GO

-- 5.11. ADMIN_LOG 
INSERT INTO ADMIN_LOG (admin_id, action_type, target_table, target_id, reason, created_at) VALUES
(1, 'INSERT', 'PROMOTION', 1, N'Tạo khuyến mãi tháng 2', '2026-01-25 09:00:00'),
(1, 'UPDATE', 'COURT', 9, N'Cập nhật trạng thái bảo trì sân E01', '2026-01-30 14:30:00'),
(2, 'INSERT', 'BOOKING', 5, N'Hỗ trợ khách đặt sân', '2026-02-02 18:05:00'),
(3, 'DELETE', 'BOOKING_DETAIL', 0, N'Xóa chi tiết đặt sân do nhập sai', '2026-02-03 09:20:00'),
(1, 'UPDATE', 'BOOKING', 4, N'Cập nhật trạng thái hủy', '2026-02-03 10:00:00'),
(2, 'INSERT', 'REFUND', 1, N'Xử lý hoàn tiền cho booking 21', '2026-02-08 10:35:00'),
(3, 'INSERT', 'PAYMENT', 22, N'Nhận thanh toán tiền mặt', '2026-02-07 15:10:00'),
(1, 'UPDATE', 'PROMOTION', 3, N'Gia hạn khuyến mãi', '2026-02-05 11:00:00'),
(2, 'INSERT', 'MEMBER', 6, N'Đăng ký thành viên mới', '2026-02-06 16:00:00'),
(3, 'UPDATE', 'COURT', 12, N'Đánh dấu sân đã đặt', '2026-02-02 17:30:00');
GO

-- =====================================================
-- 6. KIỂM TRA DỮ LIỆU
-- =====================================================
SELECT COUNT(*) AS 'CUSTOMER' FROM CUSTOMER;
SELECT COUNT(*) AS 'MEMBER' FROM MEMBER;
SELECT COUNT(*) AS 'ADMIN' FROM ADMIN;
SELECT COUNT(*) AS 'COURT' FROM COURT;
SELECT COUNT(*) AS 'PROMOTION' FROM PROMOTION;
SELECT COUNT(*) AS 'BOOKING' FROM BOOKING;
SELECT COUNT(*) AS 'BOOKING_DETAIL' FROM BOOKING_DETAIL;
SELECT COUNT(*) AS 'PAYMENT' FROM PAYMENT;
SELECT COUNT(*) AS 'REFUND' FROM REFUND;
SELECT COUNT(*) AS 'ADMIN_LOG' FROM ADMIN_LOG;
GO