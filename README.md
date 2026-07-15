Tôi thấy `README.md` hiện tại đang trùng với `progress.md` khá nhiều. `README` nên tập trung vào **cách cài đặt và sử dụng**, còn lịch sử debug và bài học nên để trong `progress.md`.

Tôi đề xuất sửa thành như sau.

---

# Dynamo Tool: Annotate Cửa / Cửa sổ (Detail Component)

Tự động tạo Detail Component annotation cho Door và Window trong Plan View, đặt đúng vị trí và tự điều chỉnh theo kích thước thực tế của cửa và độ dày tường.

---

# 1. Chức năng

Khi chọn một hoặc nhiều Door/Window trong Plan View, tool sẽ:

* Tạo Detail Component line-based tại tâm cửa.
* Đặt annotation song song với wall centerline.
* Tự tính chiều dài:

```text
Length = Width cửa + 40 mm
```

* Tự tạo Type mới nếu chưa tồn tại:

```text
<Tên gốc>_T<wallThickness>
```

* Gán:

```text
Width_Door (Type Parameter) = độ dày tường
```

* Kiểm tra kết quả sau khi tạo annotation bằng node `N10`.

---

# 2. Yêu cầu

* Revit + Dynamo.
* IronPython.
* Một Detail Component line-based đã được load vào project.
* Family phải có Type Parameter:

```text
Width_Door
```

* Door và Window phải được host bởi Wall.
* Chạy trong Plan View.

---

# 3. Cấu trúc thư mục

```text
.
├── README.md
├── progress.md
├── Home.dyn
└── src/
    ├── N1_GetSelectedElements.py
    ├── N2_PickDetailComponent.py
    ├── N3_GetWidth.py
    ├── N4_GetHostWall.py
    ├── N5_GetWallThickness.py
    ├── N6_GetWallOrientation.py
    ├── N7_GetLocationPoint.py
    ├── N8_GetOrCreateType.py
    ├── N9_CreateAnnotation.py
    └── N10_SanityCheck.py
```

---

# 4. Cách liên kết file `.py` vào Dynamo

Mỗi Python Node trong Dynamo chỉ cần chứa đoạn code sau:

```python
import io

path = r"D:\Working\DYNAMO_DOOR_OPENNING_DETAIL-main\src\N1.py"

exec(
    compile(
        io.open(path, encoding="utf-8").read(),
        path,
        "exec"
    ),
    globals()
)
```

Chỉ cần thay đổi:

```python
path = r"..."
```

thành đường dẫn tương ứng của từng node:

```text
N1.py
N2.py
...
N10.py
```

Cách này giúp:

* Không phải copy code vào Dynamo.
* Dễ sửa lỗi.
* Dễ cập nhật phiên bản.
* Toàn bộ logic nằm trong thư mục `src`.

---

# 5. Các node

| Node | Chức năng                    |
| ---- | ---------------------------- |
| N1   | Lấy Door/Window từ Selection |
| N2   | Chọn Detail Component mẫu    |
| N3   | Lấy chiều rộng cửa           |
| N4   | Lấy Host Wall                |
| N5   | Lấy độ dày tường             |
| N6   | Lấy hướng tường              |
| N7   | Lấy tâm cửa                  |
| N8   | Tìm hoặc tạo Type phù hợp    |
| N9   | Tạo annotation               |
| N10  | Kiểm tra kết quả             |

---

# 6. Sơ đồ nối dây

## Chạy batch

```text
N1 → N3, N4, N7

N4 → N5, N6

N2 + N5 → N8

N8 + N7 + N6 + N3 → N9

N9 + N3 + N5 → N10
```

Tất cả các node từ `N3 → N10` đều hỗ trợ list input.

Không cần:

* `List.Map`
* `List.GetItemAtIndex`
* Python loop bên ngoài

---

# 7. Quy trình sử dụng

1. Mở Plan View.
2. Chọn các Door và Window.
3. Dùng `N2` để chọn một Detail Component mẫu trong model.
4. Nối dây theo sơ đồ ở mục 6.
5. Chạy graph Dynamo.
6. Kiểm tra kết quả tại output của `N10`.

---

# 8. Trạng thái hiện tại

✅ Tool đã hoàn thành và hoạt động ổn định.

Đã hoàn thiện:

* Tạo annotation đúng vị trí.
* Tạo annotation đúng hướng.
* Tự tạo Type theo độ dày tường.
* Hỗ trợ xử lý batch.
* Tự kiểm tra bằng `N10`.

`N10_SanityCheck` hiện đã hoạt động bình thường và xác nhận:

* `Width_Door = Wall Thickness`
* `Length = Door Width + 40 mm`

---

# 9. Ghi chú

* Node `N10` chỉ dùng để kiểm tra kết quả, không ảnh hưởng đến việc tạo annotation.
* `progress.md` chứa toàn bộ lịch sử phát triển, quyết định kiến trúc và các lỗi đã xử lý.
* Khi thay đổi tên parameter trong family, cần cập nhật đồng thời các node sử dụng parameter đó.
