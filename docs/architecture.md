# Architecture – SmartJob AI & BI

## 1. Các thành phần

### Frontend
- Giao diện ứng viên.
- Giao diện nhà tuyển dụng.
- Trang tìm kiếm việc làm.
- Trang kết quả gợi ý.
- Trang Dashboard BI.

### Backend – Python
- Quản lý người dùng và phân quyền.
- Quản lý hồ sơ ứng viên, công ty và tin tuyển dụng.
- Quản lý đơn ứng tuyển.
- Cung cấp REST API.
- Kết nối AI Matching và dữ liệu phục vụ BI.

### AI Matching
- Chuẩn hóa kỹ năng.
- Tính điểm tương thích ứng viên – công việc.
- Xếp hạng kết quả.
- Trả về kỹ năng phù hợp và kỹ năng còn thiếu.

### Database
- Lưu tài khoản, hồ sơ, kỹ năng, việc làm, đơn ứng tuyển và kết quả ghép nối.

### BI
- Tổng hợp dữ liệu tuyển dụng.
- Tạo chỉ số và biểu đồ.
- Hiển thị xu hướng ngành nghề, kỹ năng và mức lương.

## 2. Luồng dữ liệu
1. Người dùng thao tác trên frontend.
2. Frontend gửi yêu cầu đến backend thông qua REST API.
3. Backend xác thực quyền và xử lý nghiệp vụ.
4. Backend đọc hoặc cập nhật database.
5. Khi cần gợi ý, backend gọi module AI Matching.
6. Kết quả ghép nối được trả về frontend và có thể lưu để phân tích.
7. BI tổng hợp dữ liệu nghiệp vụ để tạo dashboard.

## 3. Nguyên tắc tích hợp
- Database là nguồn dữ liệu nghiệp vụ chính.
- Frontend không truy cập database trực tiếp.
- AI không tự sửa dữ liệu nghiệp vụ nếu chưa qua backend.
- BI sử dụng dữ liệu đã chuẩn hóa và không tự thay đổi dữ liệu gốc.
- Các API có định dạng dữ liệu thống nhất.

## 4. Công nghệ dự kiến
- Backend: Python, Django, Django REST Framework.
- AI: Python.
- Database: PostgreSQL
- Frontend: HTML/CSS/JavaScript 
- BI: Superset
- Git: GitHub để quản lý mã nguồn.