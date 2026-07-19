# Progress — Dynamo Tool: Annotate Cửa/Cửa sổ

## Trạng thái hiện tại
Phase 1-3 xong (batch, 9 node N1-N9). N10 **đã xoá** — chuyển sang kiểm tra thủ công
bằng các node Dynamo có sẵn (Watch, List.Contains, v.v.).

## Mục tiêu tool
Quét Doors + Windows ở Plan View, tự động tạo Detail Component annotation tại
vị trí mỗi cửa: Width (Type param) = độ dày tường; Length (Instance param) =
width cửa + 40mm; hướng song song wall centerline; vị trí = Location Point.

## Quyết định kiến trúc đã chốt (15/7/2026)

| Câu hỏi | Quyết định |
|---|---|
| Input Detail Component | Chọn 1 instance có sẵn trong model → lấy FamilySymbol |
| Hướng đặt annotation | Song song wall centerline |
| Vị trí đặt | Location Point của door/window |
| Width khác nhau | Duplicate Type mới, tên = `<Tên gốc>_T<wallThickness>` |
| Plan View | Active view hiện tại |
| Công thức Length | Width cửa + 40mm (20mm × 2 bên) |
| Unhosted door/window | Báo lỗi, không silent skip |
| Tên parameter Width | Configurable, default `"Width_Door"` (IN[2] ở N8) |

## Node hiện có (tất cả N3-N10 hỗ trợ list/batch)

| Node | Mô tả | Input | Trạng thái |
|---|---|---|---|
| N1 GetSelectedElements | Lọc Doors+Windows từ selection | — | ✅ |
| N2 PickDetailComponent | Lấy FamilySymbol từ DC instance | — | ✅ |
| N3 GetWidth | Width cửa (từ Symbol, không phải instance) | N1 | ✅ |
| N4 GetHostWall | Host wall | N1 | ✅ |
| N5 GetWallThickness | Độ dày tường từ `WallType.Width` | N4 | ✅ |
| N6 GetWallOrientation | Vector hướng wall | N4 | ✅ |
| N7 GetLocationPoint | Location Point tâm cửa | N1 | ✅ |
| N8 GetOrCreateType | Duplicate type (Width=thickness), IN[2]=paramName | N2+N5 | ✅ |
| N9 CreateAnnotation | Tạo line-based DC | N8+N7+N6+N3 | ✅ |

## Sơ đồ nối dây (single element hay batch dùng chung 1 sơ đồ)
```
N1 ─┬→ N3
    ├→ N4 → N5 → N8 (+ N2)
    │        └→ N6
    └→ N7
N8 + N7 + N6 + N3 → N9
```
Test 1 phần tử: `N1 → List.GetItemAtIndex(0)` trước khi vào N3/N4/N7. Batch
nhiều cửa: nối thẳng N1, không cần `List.Map`. IN[2] (N8) là
string tên parameter, để trống dùng mặc định `"Width_Door"`.

## Lỗi đã fix (tool này)

| Node | Lỗi | Fix |
|---|---|---|
| N1 | `Category.Id.IntegerValue` crash | Dùng `Category.BuiltInCategory` |
| N2 | DC có `LocationCurve` thay `LocationPoint`; `:F2` không work với Dynamo Point | Check cả 2 loại location; bỏ format specifier |
| N3 | Width đọc từ instance ra 0.0 | Đọc từ `el.Symbol` |
| N4 | Crash khi Host null | Check null trước, dùng `.Id` thay `.IntegerValue` |
| N5 | Sai công thức: dùng bbox → ra chiều cao tường thay vì độ dày | Dùng `WallType.Width` |
| N8 | `GetSymbolIds()` sai method; thiếu Transaction | `GetFamilySymbolIds()`, wrap `TransactionManager` |
| N8 | File N8.py/N5.py từng bị dán nhầm code N2 | Viết lại đúng logic (18/7) |
| N9 | Line không nằm trong plane view; XYZ mất valid qua wire; toán tử XYZ +/- không hoạt động | Set Z=view elevation; copy XYZ mới; tính tọa độ thủ công |
| N9 | Length param read-only trong family | Bỏ set Length, để auto từ Line |

## Lỗi generic đã gặp nhiều lần, cân nhắc cập nhật vào AGENTS.md
`hasattr(obj, "__iter__")` trả `True` sai cho `FamilySymbol`/`FamilyInstance`
(dùng `isinstance(obj, (list, tuple))`); output node trước có thể bị Dynamo
wrap thành `[list, log]` cần unwrap khi nhận. *(Đã đề xuất đưa 2 rule này lên
AGENTS.md vì sẽ tái diễn ở tool khác — xem phần dưới.)*

## Việc còn lại
- [ ] Kiểm tra vị trí đặt detail có đúng ở giữa cửa không (mỗi bên cách đều mép cửa 20mm)
- [ ] Chống duplicate khi chạy lại — nếu bị trùng thì hiện thông báo
- [ ] Node code block để tuỳ biến giá trị cộng thêm vào Length (hiện fix cứng 20mm)
- [ ] (Nâng cao) chọn plan view + dùng phối cảnh 3D để chọn đối tượng cửa

## Lịch sử thay đổi
- 15/7: Hoàn thành 10 node, 4 phase; rewrite N3-N10 hỗ trợ batch; fix N5/N6 unwrap
- 18/7: Fix N5.py/N8.py sai nội dung; fix N8 "no len()"; thêm configurable param
  name; fix N5 sai công thức thickness; fix N9 iterable + XYZ operator; N10 vẫn
  chưa fix được
- **19/7: Fix N10 — thay `.Symbol` bằng `GetTypeId()`; thêm `UnwrapElement` + `get_fresh_element`; sửa input parsing**
- **20/7: Xoá N10, chuyển sang kiểm tra thủ công bằng node Dynamo có sẵn**
