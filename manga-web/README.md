# Web đọc truyện (nhiều bộ truyện, nhiều chương)

Web tĩnh, không cần server chạy nền, không cần máy tính bật. Ảnh chỉ được
tải khi cuộn tới gần (`loading="lazy"`), nên điện thoại không tải nguyên
chương/bộ truyện cùng lúc.

## Cấu trúc project

```
manga-web/
├── index.html                     trang chủ — danh sách BỘ TRUYỆN
├── series.html                    danh sách CHƯƠNG của 1 bộ truyện
├── reader.html                    đọc 1 chương
├── manifest.json                  danh sách bộ truyện (tự sinh, đừng sửa tay)
├── generate_manifest.py           script quét ảnh, tự tạo mọi manifest/pages.json
├── assets/style.css
└── series/
    ├── truyen-mau-1/
    │   ├── manifest.json          tên bộ truyện + danh sách chương (tự sinh)
    │   └── chapters/
    │       ├── chuong-01/
    │       │   ├── 001.jpg
    │       │   ├── 002.jpg
    │       │   └── pages.json     danh sách ảnh của chương này (tự sinh)
    │       └── chuong-02/
    │           └── ...
    └── truyen-mau-2/
        └── ...
```


## Cách thêm MỘT BỘ TRUYỆN MỚI

1. Tạo folder mới trong `series/`, tên không dấu không khoảng trắng, ví dụ:
   ```
   series/ten-truyen-moi/chapters/chuong-01/001.jpg
   series/ten-truyen-moi/chapters/chuong-01/002.jpg
   ```
2. Chạy lại script:
   ```
   python3 generate_manifest.py
   ```
3. Mở `series/ten-truyen-moi/manifest.json`, sửa `"title"` thành tên thật
   của bộ truyện, sửa `"title"` từng chương nếu muốn. (Không cần sửa
   `manifest.json` ở gốc — file đó tự sinh lại toàn bộ mỗi lần chạy script.)
4. (Tuỳ chọn) Muốn có **ảnh bìa bộ truyện** hiện ở trang chủ: bỏ 1 file ảnh
   tên `cover.jpg` (hoặc `.png`/`.webp`) thẳng vào `series/ten-truyen-moi/`,
   rồi chạy lại script — tự nhận, không cần sửa tay manifest.
5. (Tuỳ chọn) Muốn có **ảnh bìa riêng cho 1 chương**: bỏ file `cover.jpg`
   thẳng vào folder chương đó (cùng chỗ với `001.jpg`...), chạy lại script —
   file này tự thành ảnh đại diện chương, không bị tính là trang truyện.

## Cách thêm MỘT CHƯƠNG MỚI cho bộ truyện đã có

1. Tạo folder chương mới trong `series/<ten-bo-truyen>/chapters/`, ví dụ
   `series/ten-truyen-moi/chapters/chuong-02/`, bỏ ảnh vào (đặt tên
   `001.jpg, 002.jpg...` theo đúng thứ tự trang).
2. Chạy lại `python3 generate_manifest.py`.
3. Xong — chương mới tự xuất hiện trong danh sách, và trang đọc chương
   trước đó cũng tự có nút "Chương tiếp theo" trỏ sang chương mới.

**Lưu ý về tên folder:** nếu 1 bộ truyện có hơn 9 chương, nên đặt số có
số 0 phía trước (`chuong-01`, `chuong-02`,... `chuong-10`) để sắp xếp
đúng thứ tự, tương tự cho tên bộ truyện nếu đánh số.

**Không cần tự resize ảnh nữa** — script tự resize/nén mọi ảnh rộng hơn
1280px (cần cài `pip3 install pillow` một lần). Ảnh đã đủ nhỏ thì bỏ qua,
không nén lặp lại làm giảm chất lượng.

**Đổi tên folder bộ truyện/chương** thì title tự cập nhật theo tên folder
mới khi chạy lại script — trừ khi đã tự sửa tay title thành tên khác,
lúc đó script giữ nguyên, không ghi đè.

## Xem thử trước khi deploy

Trình duyệt chặn `fetch()` khi mở file bằng cách double-click (file://), nên
cần chạy qua 1 server cục bộ để test:

```
cd manga-web
python3 -m http.server 8000
```

Mở `http://localhost:8000` trên trình duyệt máy tính (hoặc điện thoại cùng
mạng wifi, dùng địa chỉ IP của máy tính thay cho `localhost`).

## Deploy lên web (miễn phí)


## Lưu ý

- Web công khai, ai có link cũng xem được, không có mật khẩu.
- Ảnh càng nặng thì tải càng lâu dù có lazy-load — resize ảnh trước khi
  đăng là quan trọng nhất để đọc mượt trên điện thoại.
- Đừng sửa tay `manifest.json` ở thư mục gốc hay các file `pages.json` —
  các file này tự sinh lại toàn bộ mỗi lần chạy `generate_manifest.py`,
  sửa tay xong chạy script lại sẽ mất. Chỉ sửa tay phần `title`/`subtitle`/
  `cover` trong `series/<slug>/manifest.json`.
