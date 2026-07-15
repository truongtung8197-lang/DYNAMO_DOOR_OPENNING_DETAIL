# Progress — Dynamo Tool: Annotate Cửa/Cửa sổ

## Mục tiêu tool
Quét chọn Doors + Windows ở Plan View, tự động tạo Detail Component annotation tại vị trí mỗi cửa:
- **Width (Type parameter)** = độ dày tường (wall thickness)
- **Length (Instance parameter)** = width cửa + 40mm (tự động từ Line)
- **Hướng:** Song song wall centerline
- **Vị trí:** Tâm cửa (Location Point)

## Quyết định kiến trúc đã chốt (15/7/2026)

| Câu hỏi | Quyết định |
|---------|------------|
| Input Detail Component | Chọn 1 instance có sẵn trong model → lấy FamilySymbol |
| Hướng đặt annotation | Song song wall centerline (dọc theo tường) |
| Vị trí đặt | Location Point của door/window |
| Width khác nhau | Duplicate Type mới, tên = `<Tên gốc>_T<wallThickness>` |
| Plan View | Active view hiện tại |
| Công thức Length | Width cửa + 40mm (20mm × 2 bên) |
| Unhosted door/window | Báo lỗi (không silent skip) |
| Width (DC Type) = wall thickness | ✅ |

## Kiến trúc node (đã hoàn thành — batch mode)

### Phase 1: Input nodes ✅
| Node | Mô tả | File |
|------|-------|------|
| **N1: GetSelectedElements** | Lọc Doors + Windows từ selection | `N1_GetSelectedElements.py` |
| **N2: PickDetailComponent** | Lấy FamilySymbol từ DC instance có sẵn | `N2_PickDetailComponent.py` |

### Phase 2: Đọc dữ liệu element ✅ (batch)
| Node | Mô tả | Input từ | File |
|------|-------|---------|------|
| **N3: GetWidth** | Width cửa (Type → Symbol) | N1 | `N3_GetWidth.py` |
| **N4: GetHostWall** | Host wall | N1 | `N4_GetHostWall.py` |
| **N5: GetWallThickness** | Độ dày tường từ BoundingBox | N4 | `N5_GetWallThickness.py` |
| **N6: GetWallOrientation** | Vector hướng wall | N4 | `N6_GetWallOrientation.py` |
| **N7: GetLocationPoint** | Location Point tâm cửa | N1 | `N7_GetLocationPoint.py` |

### Phase 3: Tạo annotation ✅ (batch)
| Node | Mô tả | Input từ | File |
|------|-------|---------|------|
| **N8: GetOrCreateType** | Duplicate type (Width = wall thickness) → ElementId | N2 + N5 | `N8_GetOrCreateType.py` |
| **N9: CreateAnnotation** | Tạo line-based DC (Length tự động từ Line) | N8 + N7 + N6 + N3 | `N9_CreateAnnotation.py` |

### Phase 4: Sanity check ⚠️ (cần sửa tiếp)
| Node | Mô tả | Input từ | File | Trạng thái |
|------|-------|---------|------|-----------|
| **N10: SanityCheck** | Width vs thickness, Length vs width+40mm | N9 + N3 + N5 | `N10_SanityCheck.py` | ⚠️ Cần debug |

## Sơ đồ nối dây batch (N1 → N10)

### Input của từng node
- **N1** (Select Model Elements): không input — lấy từ selection Revit
- **N2** (PickDetailComponent): không input — pick 1 DC instance có sẵn
- **N3** (GetWidth): ← N1
- **N4** (GetHostWall): ← N1
- **N5** (GetWallThickness): ← N4
- **N6** (GetWallOrientation): ← N4
- **N7** (GetLocationPoint): ← N1
- **N8** (GetOrCreateType): ← N2 + N5
- **N9** (CreateAnnotation): ← N8 + N7 + N6 + N3
- **N10** (SanityCheck): ← N9 + N3 + N5


**Giải thích:** N3, N4, N7 đều nhận trực tiếp từ N1 (song song, không nối tiếp). N10 nhận 3 input: output annotation từ N9, Width từ N3, và Thickness từ N5.

**Lưu ý:** Tất cả node N3-N10 đều hỗ trợ list input. Để chạy batch, nối theo đúng sơ đồ trên (N1 chia 3 nhánh N3/N4/N7; N4 sinh N5/N6; N2+N5 → N8; N8+N7+N6+N3 → N9; N9+N3+N5 → N10).

## Những lỗi đã fix và bài học

### N1 — BuiltInCategory
- **Lỗi:** `el.Category.Id.IntegerValue` → crash
- **Fix:** Dùng `el.Category.BuiltInCategory` so sánh enum

### N2 — LocationCurve + format string
- **Lỗi 1:** DC có LocationCurve thay vì LocationPoint
- **Lỗi 2:** `GetParameters("Type Name")` → lỗi
- **Lỗi 3:** `:F2` format specifier không hoạt động với Dynamo Point
- **Fix:** Check cả 2 loại location, dùng `.Name`, bỏ format specifier

### N3 — Width là Type parameter
- **Lỗi:** Đọc từ instance → ra 0.0
- **Fix:** Đọc từ `el.Symbol` (FamilySymbol)

### N4 — Host + IntegerValue
- **Lỗi:** Crash khi Host null, `IntegerValue` lỗi
- **Fix:** Check null trước, dùng `.Id` thay `.IntegerValue`

### N5, N6 — Dynamo wrapper
- **Lỗi:** `isinstance(wall, Wall)` trả về False vì wall bị Dynamo wrap
- **Fix:** `UnwrapElement(wall)` trước khi check

### N8 — Transaction + API method
- **Lỗi 1:** `GetSymbolIds()` → sai method
- **Lỗi 2:** Thiếu Transaction khi duplicate type
- **Fix:** `GetFamilySymbolIds()`, wrap trong TransactionManager

### N9 — Vòng đời object qua wire Dynamo
- **Lỗi 1:** "The line is not in the plane of view" → set Z = view elevation
- **Lỗi 2:** "The referenced object is not valid" → Revit XYZ mất valid qua wire
- **Lỗi 3:** Transaction thủ công fail → dùng `TransactionManager` của Dynamo
- **Lỗi 4:** "The parameter is read-only" → Length là read-only trong family
- **Lỗi 5:** N8 output bị wrap thành `[list, log]` → N9 nhận sai kiểu
- **Fix:** Copy XYZ mới, dùng TransactionManager, bỏ set Length parameter, thêm `unwrap_deep()` để xử lý nested lists

### N10 — Output format từ N9
- **Lỗi:** N9 output là `[list_annotation, log_string]`, N10 đọc sai
- **Fix:** Thêm `extract_list_from_output()` để parse đúng format

## Lịch sử thay đổi quan trọng
- 15/7/2026: Toàn bộ tool hoàn thành (10 nodes, 4 phases)
- 15/7/2026: Rewrite N3-N10 để hỗ trợ batch (list input) — dễ sử dụng, ít lỗi hơn
- 15/7/2026: Fix N5/N6 unwrap Dynamo wrapper + fix N1 output wrap `[[list]]`
- 15/7/2026: Fix N9 unwrap_deep() cho N8 output + fix N10 extract_list_from_output()

## Cần làm tiếp (phiên sau)
- Thêm cách xử lý chống duplicate nếu có những chỗ được chọn lại và chạy trên 2 lần
- Thêm 1 node code block để tuỳ biến được giá trị cộng thêm vào chiều dài detail (Hiện tại đang là cố định 20mm)
- *Nâng cao*: Có node để chọn mặt bằng cần vẽ detail vào, sau đó có thể sử dụng phối cảnh 3d để chọn các đối tượng cửa

## Cách sử dụng

### Single element (test)
```
N1 → List.GetItemAtIndex(0) → N3, N4, N7
N4 → N5, N6
N2 + N5 → N8
N8 + N7 + N6 + N3 → N9
N9 + N3 + N5 → N10
```

### Batch (nhiều cửa)
```
N1 → N3, N4, N7
N4 → N5, N6
N2 + N5 → N8
N8 + N7 + N6 + N3 → N9
N9 + N3 + N5 → N10
```

Tất cả node N3-N10 đều tự động nhận list input. Không cần List.GetItemAtIndex hay List.Map.
