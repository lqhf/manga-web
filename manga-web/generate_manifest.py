#!/usr/bin/env python3
"""
Quét thư mục series/, tự động tạo:
  - series/<bộ-truyện>/chapters/<chương>/pages.json   (danh sách ảnh, đã sắp thứ tự)
  - series/<bộ-truyện>/manifest.json                   (danh sách chương của bộ truyện đó)
  - manifest.json                                       (danh sách tất cả bộ truyện, ở gốc project)

Cấu trúc cần có trước khi chạy:
  series/
    ten-bo-truyen-1/
      cover.jpg                      (tuỳ chọn — ảnh bìa của bộ truyện)
      chapters/
        chuong-01/
          cover.jpg                  (tuỳ chọn — ảnh bìa của riêng chương này)
          001.jpg, 002.jpg, ...
        chuong-02/
          001.jpg, ...
    ten-bo-truyen-2/
      chapters/
        chuong-01/
          ...

Cách dùng:
  python3 generate_manifest.py

Chạy lại script này mỗi khi bạn thêm/xoá bộ truyện, thêm/xoá chương, đổi tên
folder, hoặc thêm/xoá/đổi ảnh.

- Title tự lấy theo TÊN FOLDER hiện tại, kể cả khi bạn đổi tên folder sau
  này — trừ khi bạn đã tự tay sửa title thành một cái tên khác, lúc đó
  script sẽ giữ nguyên title bạn đã sửa, không ghi đè.
- File tên "cover.jpg/png/webp/..." đặt thẳng trong folder bộ truyện hoặc
  trong folder 1 chương sẽ tự được nhận làm ảnh bìa (không tính là trang
  truyện).
- Ảnh rộng hơn 1280px sẽ tự được resize + nén lại (cần cài Pillow: xem
  thông báo khi chạy script nếu chưa có).
"""

import json
import re
from pathlib import Path

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

ROOT = Path(__file__).parent
SERIES_DIR = ROOT / "series"
ROOT_MANIFEST_PATH = ROOT / "manifest.json"

IMG_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
MAX_WIDTH = 1280       # ảnh rộng hơn mức này sẽ bị resize nhỏ lại
JPEG_QUALITY = 85       # chất lượng nén khi lưu lại ảnh jpg (không nén quá tay)


def natural_key(name: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def default_title(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").strip().capitalize()


def load_json(path: Path):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def is_cover_name(filename: str) -> bool:
    return Path(filename).stem.lower() == "cover"


def find_cover_file(folder: Path):
    """Tìm file tên 'cover.<ext>' nằm thẳng trong folder (không phải trang truyện)."""
    if not folder.exists():
        return None
    for f in sorted(folder.iterdir(), key=lambda x: natural_key(x.name)):
        if f.is_file() and f.suffix.lower() in IMG_EXTS and is_cover_name(f.name):
            return f.name
    return None


def resize_if_needed(path: Path):
    """Resize + nén ảnh nếu rộng hơn MAX_WIDTH. Ảnh đã đủ nhỏ thì bỏ qua
    (không nén lại nhiều lần làm giảm chất lượng)."""
    if not HAS_PIL or not path.exists():
        return
    try:
        with Image.open(path) as im:
            width, height = im.size
            if width <= MAX_WIDTH:
                return
            ratio = MAX_WIDTH / width
            new_size = (MAX_WIDTH, max(1, round(height * ratio)))
            if path.suffix.lower() in (".jpg", ".jpeg") and im.mode != "RGB":
                im = im.convert("RGB")
            resized = im.resize(new_size, Image.LANCZOS)
            save_kwargs = {"optimize": True}
            if path.suffix.lower() in (".jpg", ".jpeg"):
                save_kwargs["quality"] = JPEG_QUALITY
            resized.save(path, **save_kwargs)
            print(f"      ↓ nén {path.name}: {width}px → {MAX_WIDTH}px")
    except Exception as e:
        print(f"      ⚠  Không nén được {path.name}: {e}")


def process_series(series_dir: Path):
    """Quét 1 bộ truyện, trả về (title, cover, số chương) để dùng ở manifest gốc."""
    slug = series_dir.name
    chapters_dir = series_dir / "chapters"

    old_series_data = load_json(series_dir / "manifest.json")
    old_chapter_meta = {c.get("slug"): c for c in old_series_data.get("chapters", [])}

    # --- title: tự theo tên folder, trừ khi bạn đã tự sửa tay ---
    old_title = old_series_data.get("title")
    old_auto_title = old_series_data.get("_auto_title")
    new_default_title = default_title(slug)
    title = new_default_title if (old_title is None or old_title == old_auto_title) else old_title

    # --- ảnh bìa bộ truyện: file "cover.*" đặt thẳng trong folder bộ truyện ---
    detected_cover = find_cover_file(series_dir)
    if detected_cover:
        resize_if_needed(series_dir / detected_cover)
        cover = detected_cover
    else:
        cover = old_series_data.get("cover", "")

    chapters_out = []
    if chapters_dir.exists():
        chapter_dirs = sorted(
            [d for d in chapters_dir.iterdir() if d.is_dir()],
            key=lambda d: natural_key(d.name),
        )
        for d in chapter_dirs:
            ch_slug = d.name
            old_ch = old_chapter_meta.get(ch_slug, {})

            all_files = sorted(
                [f for f in d.iterdir() if f.is_file() and f.suffix.lower() in IMG_EXTS],
                key=lambda f: natural_key(f.name),
            )

            ch_cover = None
            images = []
            for f in all_files:
                if ch_cover is None and is_cover_name(f.name):
                    ch_cover = f.name
                else:
                    images.append(f.name)

            if not images:
                print(f"    ⚠  Bỏ qua chương '{ch_slug}' — không có ảnh nào.")
                continue

            for fname in images:
                resize_if_needed(d / fname)
            if ch_cover:
                resize_if_needed(d / ch_cover)

            (d / "pages.json").write_text(
                json.dumps(images, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            old_ch_title = old_ch.get("title")
            old_ch_auto_title = old_ch.get("_auto_title")
            ch_default_title = default_title(ch_slug)
            ch_title = ch_default_title if (old_ch_title is None or old_ch_title == old_ch_auto_title) else old_ch_title

            ch_out = {
                "slug": ch_slug,
                "title": ch_title,
                "_auto_title": ch_default_title,
                "pages": len(images),
            }
            if ch_cover:
                ch_out["cover"] = ch_cover
            chapters_out.append(ch_out)
            print(f"    ✓ {ch_slug}: {len(images)} trang" + (" (có bìa riêng)" if ch_cover else ""))

    series_manifest = {
        "title": title,
        "_auto_title": new_default_title,
        "subtitle": old_series_data.get("subtitle", "Chọn một chương để đọc"),
        "cover": cover,
        "chapters": chapters_out,
    }
    (series_dir / "manifest.json").write_text(
        json.dumps(series_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "slug": slug,
        "title": series_manifest["title"],
        "cover": series_manifest["cover"],
        "chapters": len(chapters_out),
    }


def main():
    if not HAS_PIL:
        print("⚠  Chưa có thư viện Pillow nên sẽ KHÔNG tự resize/nén ảnh được.")
        print("   Cài bằng lệnh: pip3 install pillow\n")

    if not SERIES_DIR.exists():
        print(f"Không tìm thấy thư mục {SERIES_DIR}. Hãy tạo series/<ten-bo-truyen>/chapters/<ten-chuong>/ trước.")
        return

    series_dirs = sorted(
        [d for d in SERIES_DIR.iterdir() if d.is_dir()],
        key=lambda d: natural_key(d.name),
    )
    if not series_dirs:
        print(f"Không có bộ truyện nào trong {SERIES_DIR}.")
        return

    series_out = []
    for d in series_dirs:
        print(f"  Bộ truyện: {d.name}")
        info = process_series(d)
        if info["chapters"] == 0:
            print(f"    ⚠  '{d.name}' chưa có chương nào có ảnh — vẫn liệt kê nhưng sẽ trống.")
        series_out.append(info)

    root_manifest = {"series": series_out}
    ROOT_MANIFEST_PATH.write_text(
        json.dumps(root_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nĐã ghi manifest.json với {len(series_out)} bộ truyện.")
    print("Muốn đặt title riêng khác tên folder: sửa tay 'title' trong series/<slug>/manifest.json,")
    print("script sẽ nhận biết và không ghi đè title đó nữa ở các lần chạy sau.")


if __name__ == "__main__":
    main()
