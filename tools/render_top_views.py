from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
EXTRACTED_DIR = ROOT / "planirovki" / "extracted"
OUT_DIR = ROOT / "planirovki" / "topview_renders"
CANVAS_SIZE = (1600, 1200)
RENDER_LIMIT = 8


PALETTE = {
    "bg": (0, 0, 0, 0),
    "wall": (83, 75, 68, 255),
    "line": (96, 88, 81, 235),
    "annotation": (119, 129, 148, 170),
    "champagne": (236, 226, 199, 255),
    "sage": (206, 219, 207, 255),
    "mist": (211, 221, 233, 255),
    "rose": (229, 211, 206, 255),
    "stone": (224, 214, 195, 255),
}


FONT_SERIF = [
    Path("C:/Windows/Fonts/georgia.ttf"),
    Path("C:/Windows/Fonts/times.ttf"),
]
FONT_SERIF_BOLD = [
    Path("C:/Windows/Fonts/georgiab.ttf"),
    Path("C:/Windows/Fonts/timesbd.ttf"),
]
FONT_SANS = [
    Path("C:/Windows/Fonts/seguiemj.ttf"),  # fallback if standard UI fonts are absent
    Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
]
FONT_SANS_BOLD = [
    Path("C:/Windows/Fonts/seguisb.ttf"),
    Path("C:/Windows/Fonts/segoeuib.ttf"),
    Path("C:/Windows/Fonts/arialbd.ttf"),
]


@dataclass
class Candidate:
    key: str
    count: int
    source: Path


def load_font(size: int, *, serif: bool = False, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = FONT_SANS
    if serif and bold:
        candidates = FONT_SERIF_BOLD
    elif serif:
        candidates = FONT_SERIF
    elif bold:
        candidates = FONT_SANS_BOLD
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def iter_plan_files() -> list[Path]:
    return sorted(
        path
        for path in EXTRACTED_DIR.rglob("*.png")
        if "debug" not in path.parts and path.is_file()
    )


def pick_top_candidates(limit: int) -> list[Candidate]:
    counts: Counter[str] = Counter()
    first_seen: dict[str, Path] = {}
    for path in iter_plan_files():
        key = "_".join(path.stem.split("_")[-2:])
        counts[key] += 1
        first_seen.setdefault(key, path)
    return [
        Candidate(key=key, count=count, source=first_seen[key])
        for key, count in counts.most_common(limit)
    ]


def trim_white_border(image: Image.Image, threshold: int = 248) -> Image.Image:
    rgb = image.convert("RGB")
    background = Image.new("RGB", rgb.size, (255, 255, 255))
    diff = ImageChops.difference(rgb, background).convert("L")
    bbox = diff.point(lambda value: 255 if value > 255 - threshold else 0).getbbox()
    if not bbox:
        return rgb
    return rgb.crop(bbox)


def classify_pixel(r: int, g: int, b: int) -> tuple[int, int, int, int]:
    if r > 247 and g > 247 and b > 247:
        return PALETTE["bg"]

    if r > 225 and b > 225 and g < 175:
        return PALETTE["wall"]

    if r > 212 and g > 205 and b > 188:
        return PALETTE["stone"]

    if r > 206 and g > 206 and b < 190:
        return PALETTE["champagne"]

    if g > 196 and r < 215 and b < 215:
        return PALETTE["sage"]

    if b > 210 and g > 210 and r > 180:
        return PALETTE["mist"]

    if r > 220 and b > 204 and g > 180:
        return PALETTE["rose"]

    if max(r, g, b) < 105:
        return PALETTE["line"]

    if b > 190 and g > 165 and r < 190:
        return PALETTE["annotation"]

    if r > 195 and g < 165 and b < 165:
        return PALETTE["annotation"]

    if max(r, g, b) - min(r, g, b) < 28:
        alpha = 225 if max(r, g, b) < 180 else 205
        return (115, 106, 98, alpha)

    return (198, 188, 176, 225)


def stylize_plan(source: Image.Image) -> tuple[Image.Image, Image.Image]:
    image = trim_white_border(source)
    rgba = Image.new("RGBA", image.size, PALETTE["bg"])
    pixels_in = image.load()
    pixels_out = rgba.load()
    for y in range(image.height):
        for x in range(image.width):
            pixels_out[x, y] = classify_pixel(*pixels_in[x, y])

    alpha = rgba.getchannel("A")
    mask = alpha.point(lambda value: 255 if value > 10 else 0)

    light = Image.new("RGBA", image.size, (255, 246, 231, 0))
    light.putalpha(ImageChops.offset(mask, -4, -6).filter(ImageFilter.GaussianBlur(12)).point(lambda v: min(v, 60)))
    dark = Image.new("RGBA", image.size, (46, 37, 31, 0))
    dark.putalpha(ImageChops.offset(mask, 8, 10).filter(ImageFilter.GaussianBlur(18)).point(lambda v: min(v, 86)))
    rgba = Image.alpha_composite(rgba, dark)
    rgba = Image.alpha_composite(rgba, light)

    contour = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(5)), mask.filter(ImageFilter.MinFilter(5)))
    outline = Image.new("RGBA", image.size, (63, 56, 51, 0))
    outline.putalpha(contour.point(lambda v: min(v, 92)))
    rgba = Image.alpha_composite(rgba, outline)

    return rgba, mask


def fit_into_canvas(image: Image.Image, box: tuple[int, int]) -> Image.Image:
    scale = min(box[0] / image.width, box[1] / image.height)
    new_size = (
        max(1, int(round(image.width * scale))),
        max(1, int(round(image.height * scale))),
    )
    return image.resize(new_size, Image.Resampling.LANCZOS)


def add_blurred_glow(canvas: Image.Image, bbox: tuple[int, int, int, int], color: tuple[int, int, int], opacity: int, blur: int) -> Image.Image:
    mask = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(mask).ellipse(bbox, fill=opacity)
    mask = mask.filter(ImageFilter.GaussianBlur(blur))
    layer = Image.new("RGBA", canvas.size, color + (0,))
    layer.putalpha(mask)
    return Image.alpha_composite(canvas, layer)


def compose_scene(plan: Image.Image, mask: Image.Image, candidate: Candidate, rank: int) -> Image.Image:
    scene = Image.new("RGBA", CANVAS_SIZE, (16, 14, 15, 255))

    vertical = ImageOps.colorize(
        Image.linear_gradient("L").resize(CANVAS_SIZE),
        black="#141212",
        white="#2b221d",
    ).convert("RGBA")
    scene = Image.alpha_composite(scene, vertical)
    scene = add_blurred_glow(scene, (180, 70, 1480, 950), (120, 83, 42), 90, 130)
    scene = add_blurred_glow(scene, (-220, -40, 820, 760), (82, 79, 92), 55, 130)
    scene = add_blurred_glow(scene, (480, 620, 1320, 1320), (170, 103, 42), 75, 170)

    content = fit_into_canvas(plan, (1280, 860))
    alpha = fit_into_canvas(mask.convert("L"), (1280, 860))
    x = (CANVAS_SIZE[0] - content.width) // 2 + 70
    y = (CANVAS_SIZE[1] - content.height) // 2 + 55

    depth_mask = Image.new("L", CANVAS_SIZE, 0)
    for offset in range(10, 27):
        depth_mask.paste(40 + (offset - 10) * 2, (x + offset, y + offset), alpha)
    depth_mask = depth_mask.filter(ImageFilter.GaussianBlur(16))
    depth = Image.new("RGBA", CANVAS_SIZE, (58, 40, 27, 0))
    depth.putalpha(depth_mask)
    scene = Image.alpha_composite(scene, depth)

    floor_shadow = Image.new("L", CANVAS_SIZE, 0)
    shadow_box = (x - 90, y + content.height - 40, x + content.width + 110, y + content.height + 120)
    ImageDraw.Draw(floor_shadow).ellipse(shadow_box, fill=160)
    floor_shadow = floor_shadow.filter(ImageFilter.GaussianBlur(55))
    floor_layer = Image.new("RGBA", CANVAS_SIZE, (21, 15, 13, 0))
    floor_layer.putalpha(floor_shadow)
    scene = Image.alpha_composite(scene, floor_layer)

    glass_plate = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    plate_mask = Image.new("L", CANVAS_SIZE, 0)
    ImageDraw.Draw(plate_mask).rounded_rectangle(
        (x - 26, y - 26, x + content.width + 26, y + content.height + 26),
        radius=30,
        fill=72,
    )
    plate_mask = plate_mask.filter(ImageFilter.GaussianBlur(8))
    glass_plate.putalpha(plate_mask)
    glass_plate = Image.alpha_composite(
        glass_plate,
        Image.new("RGBA", CANVAS_SIZE, (255, 255, 255, 18)),
    )
    scene = Image.alpha_composite(scene, glass_plate)

    top_highlight_mask = Image.new("L", CANVAS_SIZE, 0)
    ImageDraw.Draw(top_highlight_mask).rounded_rectangle(
        (x - 26, y - 26, x + content.width + 26, y + 56),
        radius=30,
        fill=80,
    )
    top_highlight_mask = top_highlight_mask.filter(ImageFilter.GaussianBlur(18))
    top_highlight = Image.new("RGBA", CANVAS_SIZE, (255, 244, 230, 0))
    top_highlight.putalpha(top_highlight_mask)
    scene = Image.alpha_composite(scene, top_highlight)

    plan_layer = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    plan_layer.paste(content, (x, y), content)
    scene = Image.alpha_composite(scene, plan_layer)

    edge_mask = Image.new("L", CANVAS_SIZE, 0)
    edge_mask.paste(alpha.filter(ImageFilter.MaxFilter(7)), (x - 1, y - 1))
    edge_mask = edge_mask.filter(ImageFilter.GaussianBlur(4))
    edge = Image.new("RGBA", CANVAS_SIZE, (255, 242, 225, 0))
    edge.putalpha(edge_mask.point(lambda value: min(value, 56)))
    scene = Image.alpha_composite(scene, edge)

    draw = ImageDraw.Draw(scene)
    title_font = load_font(34, serif=True, bold=True)
    key_font = load_font(23, bold=True)
    meta_font = load_font(22)
    small_font = load_font(18)

    card_x = 76
    card_y = 72
    card_w = 468
    card_h = 96
    draw.rounded_rectangle(
        (card_x, card_y, card_x + card_w, card_y + card_h),
        radius=26,
        fill=(8, 8, 9, 150),
        outline=(72, 57, 45, 110),
        width=2,
    )
    draw.text((card_x + 26, card_y + 16), "NEW KOMITAS", font=small_font, fill=(198, 188, 173, 180))
    draw.text((card_x + 26, card_y + 36), "Top-View Render", font=title_font, fill=(246, 239, 230, 235))
    badge = f"No. {rank:02d}"
    badge_width = draw.textbbox((0, 0), badge, font=key_font)[2]
    draw.text((card_x + card_w - 26 - badge_width, card_y + 42), badge, font=key_font, fill=(214, 178, 126, 220))
    draw.text((card_x + 26, card_y + 70), candidate.key.replace("_", " / "), font=key_font, fill=(214, 178, 126, 205))

    footer_x = 76
    footer_y = CANVAS_SIZE[1] - 126
    footer_w = 454
    footer_h = 62
    draw.rounded_rectangle(
        (footer_x, footer_y, footer_x + footer_w, footer_y + footer_h),
        radius=22,
        fill=(10, 10, 11, 148),
        outline=(66, 52, 40, 90),
        width=2,
    )
    draw.text((footer_x + 24, footer_y + 18), f"Repeated layout in source set: {candidate.count} times", font=meta_font, fill=(224, 214, 194, 215))

    return scene.convert("RGB")


def build_contact_sheet(items: list[dict[str, str]]) -> Path:
    cols = 2
    thumb_w = 720
    thumb_h = 540
    label_h = 84
    pad = 36
    rows = (len(items) + cols - 1) // cols
    canvas = Image.new("RGB", (pad + cols * (thumb_w + pad), pad + rows * (thumb_h + label_h + pad)), (12, 12, 13))
    draw = ImageDraw.Draw(canvas)
    name_font = load_font(30, serif=True)
    meta_font = load_font(22)

    for index, item in enumerate(items):
        image = Image.open(item["output"]).convert("RGB")
        image = ImageOps.fit(image, (thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = pad + (index % cols) * (thumb_w + pad)
        y = pad + (index // cols) * (thumb_h + label_h + pad)
        canvas.paste(image, (x, y))
        draw.rounded_rectangle((x, y + thumb_h + 12, x + thumb_w, y + thumb_h + label_h), radius=18, fill=(20, 20, 22))
        draw.text((x + 18, y + thumb_h + 22), item["key"].replace("_", " / "), font=name_font, fill=(236, 228, 217))
        draw.text((x + 18, y + thumb_h + 52), f"{item['count']} repetitions", font=meta_font, fill=(184, 171, 155))

    output = OUT_DIR / "contact_sheet.png"
    canvas.save(output, quality=96)
    return output


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    selected = pick_top_candidates(RENDER_LIMIT)
    manifest: list[dict[str, str | int]] = []

    for index, candidate in enumerate(selected, start=1):
        source = Image.open(candidate.source).convert("RGB")
        plan, mask = stylize_plan(source)
        render = compose_scene(plan, mask, candidate, index)
        output = OUT_DIR / f"{index:02d}_{candidate.key}_{candidate.count}x.png"
        render.save(output, quality=96)
        manifest.append(
            {
                "rank": index,
                "key": candidate.key,
                "count": candidate.count,
                "source": str(candidate.source.relative_to(ROOT)).replace("\\", "/"),
                "output": str(output.relative_to(ROOT)).replace("\\", "/"),
            }
        )

    contact_sheet = build_contact_sheet(manifest)
    metadata = {
        "note": "Stylized top-view render concepts generated from the most repeated extracted apartment layouts.",
        "items": manifest,
        "contact_sheet": str(contact_sheet.relative_to(ROOT)).replace("\\", "/"),
    }
    (OUT_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Generated {len(manifest)} renders")
    for item in manifest:
        print(f"{item['rank']:02d}. {item['key']} -> {item['output']}")
    print(f"Contact sheet: {metadata['contact_sheet']}")


if __name__ == "__main__":
    main()
