# Dynamo Python Tool Rules — Revit 2024

Áp dụng cho mọi tool Dynamo Python trong hệ thống này. Mỗi tool có `progress.md`
riêng; file này là quy tắc chung, không đổi theo tool.

## 1. Môi trường & rủi ro kỹ thuật (đọc trước khi code)

- Revit 2024, Dynamo + IronPython3. API ref: https://www.revitapidocs.com/2024/
- **Wrapper**: trước khi `isinstance(...)` hoặc gọi API Revit trên object từ
  Dynamo, luôn cân nhắc `UnwrapElement(...)`. Không giả định object nhận được
  là Revit API object thuần.
- **Đơn vị**: không giả định đơn vị. Mọi chỗ đọc/ghi giá trị phải ghi rõ đơn vị
  (mm / feet / degree) và chỗ convert.
  ```python
  mm = feet * 304.8
  ```
- **Transaction**: mọi node thay đổi model phải xác định rõ có cần Transaction
  không, bắt đầu/kết thúc ở đâu. Ưu tiên `TransactionManager` thay vì
  transaction thủ công.

Đây là 4 nguồn lỗi phổ biến nhất trong hệ thống này: silent fail, sai hình học,
quên unwrap, sai đơn vị, sai assumption transaction.

## 2. Không được làm

- Không `except: pass` (không silent fail).
- Không đóng gói toàn bộ output vào 1 dict lồng nhau — output phải xem được
  bằng Watch node trực tiếp.
- Không tách node chỉ vì hàm dài hoặc muốn code "đẹp".
- Không viết node chỉ hỗ trợ single element nếu không có lý do kỹ thuật rõ ràng
  (mặc định phải hỗ trợ list, và nested list nếu cần).
- Không vá lỗi ở phase sau khi lỗi thuộc phase trước — quay lại sửa đúng node gốc.
- Không hỏi rải rác nhiều lượt khi thiếu thông tin — gộp hết câu hỏi vào 1 lượt
  (VD: Type hay Instance parameter? Tên parameter? Tolerance? Family loại gì?
  Có cần hỗ trợ batch không?).

## 3. Nên làm

- **Tách node tại ranh giới dữ liệu quan trọng**: sai ở bước đó làm hỏng toàn
  bộ kết quả phía sau, VÀ output là dữ liệu kiểm tra được trực tiếp (Point,
  Vector, Curve, CurveLoop, Solid, Element, Number, Boolean).
- **Output dạng tuple**, không dict:
  ```python
  OUT = data, log
  ```
- **Ghi rõ input/output từng node**, ví dụ:
  ```
  IN[0] = SelectModelRevit
  IN[1] = OUTPUT NODE ...
  OUT[0] = FamilySymbol
  OUT[1] = Dynamo Point (Location)
  OUT[2] = Log
  ```
- **Sanity check dùng nguồn dữ liệu khác nguồn đã tạo kết quả** — không kiểm
  tra bằng chính assumption đã dùng để tạo ra kết quả đó. Ví dụ: tạo hình học
  từ parameter → kiểm tra lại bằng geometry thực tế (và ngược lại).
- **Debug batch**: báo số phần tử thành công/thất bại, ghi rõ Element Id +
  nguyên nhân lỗi từng phần tử, một phần tử lỗi không được làm hỏng cả batch.

## 4. Quy trình làm việc

1. Trước khi code: liệt kê ngắn gọn các bước xử lý, input/output, node phụ
   thuộc, điểm rủi ro cao nhất → chờ user xác nhận.
2. Code theo phase: viết 1 cụm node → user chạy trên model thật → xác nhận →
   mới sang phase tiếp theo. Không viết hết tool rồi mới debug.

## 5. Quản lý context (progress.md của từng tool)

- Đầu phiên: đọc `progress.md`, không hỏi lại quyết định đã chốt.
- Sau mỗi phase được xác nhận: cập nhật quyết định kiến trúc, node mới, lỗi đã
  sửa, bài học, việc còn lại.
- Không nhắc lại kiến trúc/rule đã chốt — chỉ tham chiếu ngắn ("Theo Phase 2
  đã chốt", "Theo progress.md hiện tại").

## 6. Thứ tự ưu tiên khi có xung đột

Đúng & kiểm chứng được > dễ debug trên model thật > dễ bảo trì > tiết kiệm token.