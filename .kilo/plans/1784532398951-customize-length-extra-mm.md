# Plan: Sanity-check vị trí Detail Component (cross-check độc lập)

## Mục tiêu
Kiểm tra các Detail Component vừa tạo (N9 OUT[0]) có đúng **nằm giữa cửa**, mỗi bên
cách đều mép cửa `IN[4]` mm (extra), song song wall centerline hay không.

Đây là **sanity check** → dùng nguồn dữ liệu **độc lập** với logic tạo (N7/N3/N6),
không tính lại từ output của N7/N3/N6.

## Nguồn độc lập (KHÔNG dùng N7/N3/N6 output)
Từ mỗi cửa (N1 element) và wall host (N4):

1. **Tâm cửa kỳ vọng** — `el.BoundingBox(activeView)`:
   `center = (Min + Max) / 2` (chỉ X,Y; Z lấy view elevation).
   → Độc lập với `LocationPoint` (N7).

2. **Bề rộng cửa thực tế dọc wall** — chiếu bbox lên hướng wall:
   - Hướng wall từ `wall.Location.LocationCurve` (tangent, normalize XY).
   - Project 4 đỉnh bbox lên trục wall → `proj_min`, `proj_max`.
   - `door_extent = proj_max - proj_min` (feet → mm).
   → Độc lập với param `Width` (N3) — đo từ geometry thật.

3. **Hướng kỳ vọng** — chính là wall tangent ở trên.

## Giá trị thực tế (đọc lại annotation đã tạo)
Từ N9 OUT[0] (FamilyInstance):
- `loc = anno.Location`; phải là `LocationCurve`.
- `c = loc.Curve`; `mid = c.Evaluate(0.5, True)`.
- `len_ft = c.Length`; `dir = (ep - sp)` normalize XY.
- → Đo output thật, hoàn toàn độc lập với công thức tạo.

## So sánh (tolerance)
- Vị trí: `dist(mid_actual, center_expected)` ≤ **1 mm**.
- Độ dài: `|len_actual_mm - (door_extent + 2*extra_mm)|` ≤ **1 mm**.
  (`extra_mm` = IN[4] của N9, truyền vào node này để biết kỳ vọng).
- Hướng: `dot(|dir_actual|, |dir_expected|)` > **0.999** (bất kể chiều).
- Kết quả: `pass = vị trí OK AND độ dài OK AND hướng OK`.

## Node mới: N9Check (VerifyAnnotationPlacement)
Input:
- IN[0] = N9 OUT[0] (FamilyInstance hoặc List<FamilyInstance>, có thể lẫn None do skip)
- IN[1] = N1 OUT[0] (List<Element> cửa, cùng thứ tự với N9)
- IN[2] = N4 OUT[0] (List<Wall> host, cùng thứ tự)
- IN[3] = extra_mm mỗi bên (number, default 20) — khớp IN[4] N9
Output (tuple):
- OUT[0] = List<bool> (pass/fail từng phần tử, None nếu skip/null)
- OUT[1] = List<string> (deviation detail: "OK" hoặc "pos +3.2mm, len -1.0mm, dir")
- OUT[2] = Log (tổng: pass X / total Y, lỗi)

### Xử lý
- Unwrap an toàn; bỏ qua phần tử None (skip từ N9) → đánh dấu `None`.
- Align index: N9 list có thể ngắn hơn nếu N9 trả single — chuẩn hóa về list.
- Với mỗi i: lấy anno, el, wall; đọc geometry; so sánh; ghi deviation.
- Batch-native (isinstance list/tuple), guard từng phần tử (1 lỗi không break batch).
- Không tạo/sửa model → **không cần Transaction**.

## Rủi ro
- **Thứ tự N9 vs N1/N4**: N9 lấy symbol từ N8 (theo thickness), nhưng index tạo vẫn
  khớp thứ tự input pts/vecs/widths = thứ tự N1. Giả định N9 OUT[0] cùng thứ tự N1.
  → Nếu không khớp, cross-check sai cặp. Cần verify trên model: chạy N1, N4, N9,
  N9Check cùng 1 selection.
- **BoundingBox null** (element chưa hiện trong view) → fallback báo lỗi, không silent.
- **Wall host null** (unhosted) → N4 đã báo lỗi; N9Check báo "no wall" cho phần tử đó.
- **Z elevation**: so chỉ X,Y; Z lấy view elevation (giống N9).
- **Direction sign**: dùng abs dot, bất kể chiều line.

## Validation (trên model thật)
1. Chọn 1 cửa → N1,N4,N9 (IN[4]=20) → N9Check: expect `pass=True`, deviation "OK".
2. Đổi IN[4]=30 → N9Check: độ dài kỳ vọng = door_extent + 60; annotation cũ (40) sẽ
   FAIL (len sai) → chứng tỏ check phát hiện được. Tạo mới với 30 → pass.
3. Batch 3 cửa → N9Check trả 3 bool, đúng thứ tự.
4. Dời cửa thủ công vài mm → N9Check báo `pos +X mm` (vì đọc bbox mới).
5. So với Watch node: deviation string rõ ràng, dễ debug.

## Cập nhật progress.md
Sau validated:
- Gạch bỏ mục "Kiểm tra vị trí đặt detail..." trong "Việc còn lại".
- Thêm vào "Lỗi đã fix" / "Node hiện có": N9Check verify placement (independent
  bbox + wall curve vs read-back annotation).
