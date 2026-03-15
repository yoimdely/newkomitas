from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


SOURCE_DIR = Path("planirovki")
OUTPUT_DIR = SOURCE_DIR / "extracted"
DEBUG_DIR = OUTPUT_DIR / "debug"

COLOR_CENTERS = {
    "green": (162, 226, 163),
    "yellow": (247, 255, 189),
    "blue": (203, 231, 251),
    "pink": (254, 205, 243),
}
COLOR_STROKES = {
    "green": "#00aa55",
    "yellow": "#d4b000",
    "blue": "#0088ff",
    "pink": "#cc33aa",
}


@dataclass
class Component:
    x1: int
    y1: int
    x2: int
    y2: int
    area: int

    @property
    def box(self) -> tuple[int, int, int, int]:
        return self.x1, self.y1, self.x2, self.y2

    @property
    def center(self) -> tuple[float, float]:
        return (self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2


def sanitize_stem(stem: str, index: int) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", stem).strip("_").lower()
    return slug or f"section_{index:02d}"


def color_distance_sq(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return sum((a[i] - b[i]) * (a[i] - b[i]) for i in range(3))


def overlap(a1: int, a2: int, b1: int, b2: int) -> int:
    return max(0, min(a2, b2) - max(a1, b1) + 1)


def bbox_distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> tuple[int, int]:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    dx = max(0, max(ax1 - bx2, bx1 - ax2))
    dy = max(0, max(ay1 - by2, by1 - ay2))
    return dx, dy


def intersects(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 < bx1 or ax1 > bx2 or ay2 < by1 or ay1 > by2)


def find_plan_bbox(img: Image.Image) -> tuple[int, int, int, int] | None:
    px = img.load()
    w, h = img.size
    xs: list[int] = []
    ys: list[int] = []

    for y in range(h):
        if y >= h * 0.72:
            break
        for x in range(w):
            r, g, b = px[x, y]
            if r > 230 and b > 150 and g < 140:
                xs.append(x)
                ys.append(y)

    if not xs:
        return None

    return min(xs), min(ys), max(xs), max(ys)


def build_color_components(
    img: Image.Image,
    center: tuple[int, int, int],
    plan_bbox: tuple[int, int, int, int],
) -> tuple[list[Component], list[Component]]:
    px = img.load()
    w, h = img.size
    plan_x1, plan_y1, plan_x2, plan_y2 = plan_bbox
    shrink = max(40, min(plan_x2 - plan_x1, plan_y2 - plan_y1) // 15)
    inner_bbox = (plan_x1 + shrink, plan_y1 + shrink, plan_x2 - shrink, plan_y2 - shrink)
    threshold = 35 * 35

    mask = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if color_distance_sq(px[x, y], center) < threshold:
                mask[y][x] = 1

    visited = [[False] * w for _ in range(h)]
    small_rows: list[Component] = []
    large_components: list[Component] = []

    for y in range(h):
        for x in range(w):
            if visited[y][x] or not mask[y][x]:
                continue

            stack = [(x, y)]
            visited[y][x] = True
            area = 0
            minx = maxx = x
            miny = maxy = y

            while stack:
                cx, cy = stack.pop()
                area += 1
                minx = min(minx, cx)
                miny = min(miny, cy)
                maxx = max(maxx, cx)
                maxy = max(maxy, cy)

                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx] and mask[ny][nx]:
                        visited[ny][nx] = True
                        stack.append((nx, ny))

            bw = maxx - minx + 1
            bh = maxy - miny + 1
            if area < 800 or bw < 20 or bh < 20:
                continue

            comp = Component(minx, miny, maxx, maxy, area)
            box = comp.box
            near_plan = (
                minx < plan_x2 + 120
                and maxx > plan_x1 - 120
                and miny < plan_y2 + 120
                and maxy > plan_y1 - 120
            )

            if near_plan and not intersects(box, inner_bbox) and area < 16000 and bw < 180 and bh < 180:
                small_rows.append(comp)
            elif intersects(box, plan_bbox) and area > 5000:
                large_components.append(comp)

    small_rows.sort(key=lambda item: (item.x1, item.y1))
    labels: list[list[int]] = []
    for row in small_rows:
        matched = False
        for group in labels:
            gx1, gy1, gx2, gy2, garea = group
            ov = overlap(row.x1, row.x2, gx1, gx2)
            minw = min(row.x2 - row.x1 + 1, gx2 - gx1 + 1)
            gap = row.y1 - gy2
            if ov >= minw * 0.7 and 0 <= gap <= 28:
                group[0] = min(gx1, row.x1)
                group[1] = min(gy1, row.y1)
                group[2] = max(gx2, row.x2)
                group[3] = max(gy2, row.y2)
                group[4] = garea + row.area
                matched = True
                break
        if not matched:
            labels.append([row.x1, row.y1, row.x2, row.y2, row.area])

    merged_labels = [Component(*group) for group in labels if group[4] > 3000]
    return merged_labels, large_components


def side_for_label(label: Component, plan_bbox: tuple[int, int, int, int]) -> str:
    x1, y1, x2, y2 = label.box
    px1, py1, px2, py2 = plan_bbox
    distances = (
        (abs(x2 - px1), "left"),
        (abs(x1 - px2), "right"),
        (abs(y2 - py1), "top"),
        (abs(y1 - py2), "bottom"),
    )
    return min(distances)[1]


def merge_apartment_parts(seed: Component, components: list[Component], seed_index: int) -> tuple[int, int, int, int]:
    ux1, uy1, ux2, uy2 = seed.box
    members = {seed_index}
    changed = True

    while changed:
        changed = False
        for index, component in enumerate(components):
            if index in members:
                continue

            dx, dy = bbox_distance((ux1, uy1, ux2, uy2), component.box)
            ovx = overlap(ux1, ux2, component.x1, component.x2)
            ovy = overlap(uy1, uy2, component.y1, component.y2)
            if (dx <= 28 and ovy > 20) or (dy <= 28 and ovx > 20) or (dx <= 18 and dy <= 18):
                ux1 = min(ux1, component.x1)
                uy1 = min(uy1, component.y1)
                ux2 = max(ux2, component.x2)
                uy2 = max(uy2, component.y2)
                members.add(index)
                changed = True

    return ux1, uy1, ux2, uy2


def extract_page_assignments(img: Image.Image) -> list[dict]:
    plan_bbox = find_plan_bbox(img)
    if not plan_bbox:
        return []

    assignments: list[dict] = []
    for color_name, center in COLOR_CENTERS.items():
        labels, components = build_color_components(img, center, plan_bbox)
        if not labels or not components:
            continue

        for label in labels:
            side = side_for_label(label, plan_bbox)
            lcx, lcy = label.center

            best_index = None
            best_score = float("inf")
            for index, component in enumerate(components):
                cx, cy = component.center
                if side == "top":
                    score = abs(component.y1 - label.y2) * 5 + abs(cx - lcx)
                elif side == "left":
                    score = abs(component.x1 - label.x2) * 5 + abs(cy - lcy)
                elif side == "right":
                    score = abs(label.x1 - component.x2) * 5 + abs(cy - lcy)
                else:
                    score = abs(label.y1 - component.y2) * 5 + abs(cx - lcx)

                if score < best_score:
                    best_score = score
                    best_index = index

            if best_index is None:
                continue

            bbox = merge_apartment_parts(components[best_index], components, best_index)
            assignments.append(
                {
                    "color": color_name,
                    "side": side,
                    "label_box": list(label.box),
                    "bbox": list(bbox),
                }
            )

    assignments.sort(key=lambda item: (item["bbox"][1], item["bbox"][0]))
    deduped: list[dict] = []
    for item in assignments:
        if deduped and item["color"] == deduped[-1]["color"] and item["bbox"] == deduped[-1]["bbox"]:
            continue
        deduped.append(item)
    return deduped


def save_debug_overlay(img: Image.Image, assignments: list[dict], out_path: Path) -> None:
    debug = img.copy()
    draw = ImageDraw.Draw(debug)
    for index, item in enumerate(assignments, 1):
        color = COLOR_STROKES[item["color"]]
        draw.rectangle(item["label_box"], outline=color, width=3)
        draw.rectangle(item["bbox"], outline=color, width=6)
        draw.text((item["bbox"][0], max(0, item["bbox"][1] - 18)), str(index), fill=color)
    debug.save(out_path)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    metadata: list[dict] = []
    pdf_files = sorted(
        [
            path
            for path in SOURCE_DIR.glob("*.pdf")
            if path.name not in {"sample.pdf", "sample_last.pdf"}
        ]
    )

    for pdf_index, pdf_path in enumerate(pdf_files, 1):
        safe_stem = sanitize_stem(pdf_path.stem, pdf_index)
        pdf_out_dir = OUTPUT_DIR / safe_stem
        pdf_out_dir.mkdir(parents=True, exist_ok=True)

        document = fitz.open(pdf_path)
        for page_index in range(document.page_count):
            page = document[page_index]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            assignments = extract_page_assignments(img)
            if not assignments:
                continue

            debug_path = DEBUG_DIR / f"{safe_stem}_page_{page_index + 1:02d}.png"
            save_debug_overlay(img, assignments, debug_path)

            for unit_index, item in enumerate(assignments, 1):
                x1, y1, x2, y2 = item["bbox"]
                pad = 36
                crop_box = (
                    max(0, x1 - pad),
                    max(0, y1 - pad),
                    min(img.width, x2 + pad),
                    min(img.height, y2 + pad),
                )
                crop = img.crop(crop_box)
                file_name = f"page_{page_index + 1:02d}_unit_{unit_index:02d}_{item['color']}.png"
                crop_path = pdf_out_dir / file_name
                crop.save(crop_path)

                metadata.append(
                    {
                        "pdf_file": pdf_path.name,
                        "output_group": safe_stem,
                        "page": page_index + 1,
                        "unit_index": unit_index,
                        "color": item["color"],
                        "side": item["side"],
                        "bbox": item["bbox"],
                        "label_box": item["label_box"],
                        "crop_path": str(crop_path.relative_to(OUTPUT_DIR)).replace("\\", "/"),
                        "debug_path": str(debug_path.relative_to(OUTPUT_DIR)).replace("\\", "/"),
                    }
                )

    metadata_path = OUTPUT_DIR / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Extracted {len(metadata)} apartment crops into {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
