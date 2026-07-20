# Dynamo Tool: Annotate Cửa / Cửa sổ (Detail Component)

Tự động tạo Detail Component annotation cho Door và Window trong Plan View, đặt đúng vị trí và tự điều chỉnh theo kích thước thực tế của cửa và độ dày tường.

---

# 1. Chức năng

Khi chọn một hoặc nhiều Door/Window trong Plan View, tool sẽ:

* Tạo Detail Component line-based tại tâm cửa.
* Đặt annotation song song với wall centerline.
* Tự tính chiều dài:

```text
Length = Width cửa + 2 * extra_mm (mặc định 20mm mỗi bên)
```

* Tự tạo Type mới nếu chưa tồn tại:

```text
<Tên gốc>_T<wallThickness>
```

* Gán:

```text
Width_Door (Type Parameter) = độ dày tường (mm)
```

* Tự động kiểm tra duplicate: bỏ qua annotation đã tồn tại tại cùng vị trí và hướng.
* Có node kiểm tra độc lập (N9Check) để verify kết quả.

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
    ├── N1.py
    ├── N2.py
    ├── N3.py
    ├── N4.py
    ├── N5.py
    ├── N6.py
    ├── N7.py
    ├── N8.py
    ├── N9.py
    └── N9Check.py
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
N9.py
N9Check.py
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
| N9Check | Kiểm tra kết quả annotation |

---

# 6. Sơ đồ nối dây

## Chạy batch

```text
N1 → N3, N4, N7

N4 → N5, N6

N2 + N5 → N8

N8 + N7 + N6 + N3 → N9

N9 + N1 + N4 → N9Check (optional, để verify)
```

Tất cả các node từ `N3 → N9` đều hỗ trợ list input.

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
6. (Optional) Dùng `N9Check` để tự động verify kết quả.
7. Kiểm tra kết quả bằng các node Dynamo có sẵn (Watch, List.Contains, v.v.).

---

# 8. Trạng thái hiện tại

✅ Tool đã hoàn thành và hoạt động ổn định.

Đã hoàn thiện:

* Tạo annotation đúng vị trí.
* Tạo annotation đúng hướng.
* Tự tạo Type theo độ dày tường.
* Hỗ trợ xử lý batch.
* Tự động chống duplicate annotation.
* Có node kiểm tra độc lập (N9Check) để verify tự động.

**Kiểm tra tự động bằng N9Check:**

Node `N9Check` sẽ tự động verify:

* Vị trí annotation có đúng ở giữa cửa không (tolerance 1mm).
* Chiều dài annotation có đúng không (tolerance 1mm).
* Hướng annotation có song song với wall không (tolerance dot product > 0.999).

**Output N9Check:**

* `OUT[0]`: List<bool> - True/False/None cho từng phần tử
* `OUT[1]`: List<string> - "OK" hoặc mô tả deviation
* `OUT[2]`: Log tổng hợp

**Kiểm tra thủ công** (nếu cần): dùng các node Dynamo có sẵn (Watch, List.Contains, v.v.) để kiểm tra:

* `Width_Door` (type parameter) có bằng độ dày tường không.
* `Length` có bằng `Width cửa + 2 * extra_mm` không.

---

# 9. Ghi chú

* `progress.md` chứa toàn bộ lịch sử phát triển, quyết định kiến trúc và các lỗi đã xử lý.
* Khi thay đổi tên parameter trong family, cần cập nhật đồng thời các node sử dụng parameter đó.
* N9 có cơ chế chống duplicate tự động dựa trên vị trí midpoint + hướng + type.
* N8 hỗ trợ custom parameter name qua input `IN[2]` (mặc định: "Width_Door").
* Tất cả node đều hỗ trợ batch processing (list input) mà không cần List.Map.