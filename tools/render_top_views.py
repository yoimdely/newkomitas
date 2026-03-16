from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
EXTRACTED_DIR = ROOT / "planirovki" / "extracted"
OUT_DIR = ROOT / "planirovki" / "topview_renders"
CANVAS_SIZE = (1600, 1200)


PALETTE = {
    "bg": (19, 17, 16, 255),
    "bg_glow": (123, 84, 43),
    "panel": (248, 244, 238, 255),
    "panel_border": (255, 251, 245, 255),
    "wall": (88, 80, 74, 255),
    "line": (128, 118, 109, 255),
    "champagne": (241, 231, 207, 255),
    "sage": (213, 226, 214, 255),
    "mist": (216, 226, 238, 255),
    "rose": (236, 218, 215, 255),
}

FONT_SANS = [
    Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
]
FONT_SANS_BOLD = [
    Path("C:/Windows/Fonts/segoeuib.ttf"),
    Path("C:/Windows/Fonts/arialbd.ttf"),
]


@dataclass(frozen=True)
class LayoutPreset:
    key: str
    slug: str
    title: str
    scenario: str
    source: str
    crop_box: tuple[int, int, int, int]


PRESETS = [
    LayoutPreset(
        key="08_pink",
        slug="01-invest-format",
        title="Инвест-формат",
        scenario="Компактный формат для инвестиционной покупки и аренды.",
        source="planirovki/extracted/1_signed/page_02_unit_08_pink.png",
        crop_box=(30, 34, 310, 188),
    ),
    LayoutPreset(
        key="07_yellow",
        slug="02-first-home",
        title="Первый собственный",
        scenario="Рациональный вариант для первого жилья в проекте.",
        source="planirovki/extracted/2_signed/page_02_unit_07_yellow.png",
        crop_box=(24, 24, 220, 307),
    ),
    LayoutPreset(
        key="01_blue",
        slug="03-for-couple",
        title="Для пары",
        scenario="Больше воздуха и удобная дневная зона для жизни вдвоём.",
        source="planirovki/extracted/1_signed/page_02_unit_01_blue.png",
        crop_box=(14, 18, 404, 226),
    ),
    LayoutPreset(
        key="03_yellow",
        slug="04-balance-format",
        title="Баланс комфорта",
        scenario="Спокойная геометрия и универсальный городской сценарий.",
        source="planirovki/extracted/1_signed/page_02_unit_03_yellow.png",
        crop_box=(14, 22, 352, 224),
    ),
    LayoutPreset(
        key="05_pink",
        slug="05-flexible-layout",
        title="Гибкий формат",
        scenario="Понятная база для комфортной жизни и свободной меблировки.",
        source="planirovki/extracted/1_signed/page_02_unit_05_pink.png",
        crop_box=(24, 22, 220, 228),
    ),
    LayoutPreset(
        key="05_green",
        slug="06-family-rhythm",
        title="Семейный ритм",
        scenario="Больше приватности и удобное разделение жизненных зон.",
        source="planirovki/extracted/3_signed/page_02_unit_05_green.png",
        crop_box=(26, 18, 222, 346),
    ),
    LayoutPreset(
        key="07_green",
        slug="07-spacious-euro",
        title="Просторный евро",
        scenario="Формат с запасом пространства для ежедневного комфорта.",
        source="planirovki/extracted/1_signed/page_02_unit_07_green.png",
        crop_box=(18, 24, 350, 228),
    ),
    LayoutPreset(
        key="04_green",
        slug="08-large-family",
        title="Для большой семьи",
        scenario="Самая просторная планировка в подборке для семейного сценария.",
        source="planirovki/extracted/1_signed/page_02_unit_04_green.png",
        crop_box=(18, 22, 352, 232),
    ),
]


def load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = FONT_SANS_BOLD if bold else FONT_SANS
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


def count_layouts() -> Counter[str]:
    counts: Counter[str] = Counter()
    for path in iter_plan_files():
        key = "_".join(path.stem.split("_")[-2:])
        counts[key] += 1
    return counts


def clear_output_dir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in OUT_DIR.iterdir():
        if path.is_file():
            path.unlink()


def clean_plan_image(source: Image.Image) -> Image.Image:
    source = source.convert("RGBA")
    cleaned = Image.new("RGBA", source.size, (0, 0, 0, 0))
    src = source.load()
    dst = cleaned.load()

    for y in range(source.height):
        for x in range(source.width):
            r, g, b, _ = src[x, y]

            if r > 246 and g > 246 and b > 246:
                dst[x, y] = (255, 255, 255, 0)
                continue

            if r > 205 and b > 155 and g < 175:
                dst[x, y] = PALETTE["wall"]
                continue

            if b > 170 and g > 120 and r < 165:
                dst[x, y] = (255, 255, 255, 0)
                continue

            if r > 170 and g < 130 and b < 145:
                dst[x, y] = (255, 255, 255, 0)
                continue

            if r > 223 and b > 198 and g > 176 and r - g > 10:
                dst[x, y] = PALETTE["rose"]
                continue

            if b > 205 and g > 192 and r > 174 and b - r > 8:
                dst[x, y] = PALETTE["mist"]
                continue

            if g > 188 and r < 220 and b < 220 and g - min(r, b) > 6:
                dst[x, y] = PALETTE["sage"]
                continue

            if r > 221 and g > 208 and b < 198 and r - b > 18:
                dst[x, y] = PALETTE["champagne"]
                continue

            if max(r, g, b) < 112:
                dst[x, y] = PALETTE["wall"]
                continue

            if max(r, g, b) - min(r, g, b) < 22:
                tone = max(132, min(214, int((r + g + b) / 3) + 24))
                dst[x, y] = (tone, tone, tone, 255)
                continue

            dst[x, y] = (244, 240, 234, 255)

    return cleaned.filter(ImageFilter.UnsharpMask(radius=1.4, percent=170, threshold=3))


def compose_board(plan: Image.Image) -> Image.Image:
    canvas = Image.new("RGBA", CANVAS_SIZE, PALETTE["bg"])

    glow_mask = Image.new("L", CANVAS_SIZE, 0)
    ImageDraw.Draw(glow_mask).ellipse((220, 130, 1430, 1080), fill=110)
    glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(170))
    glow_layer = Image.new("RGBA", CANVAS_SIZE, PALETTE["bg_glow"] + (0,))
    glow_layer.putalpha(glow_mask)
    canvas = Image.alpha_composite(canvas, glow_layer)

    panel_box = (128, 122, 1472, 1078)
    shadow_mask = Image.new("L", CANVAS_SIZE, 0)
    ImageDraw.Draw(shadow_mask).rounded_rectangle(panel_box, radius=48, fill=185)
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(38))
    shadow_layer = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    shadow_layer.putalpha(shadow_mask)
    canvas = Image.alpha_composite(canvas, shadow_layer)

    panel = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    panel_mask = Image.new("L", CANVAS_SIZE, 0)
    ImageDraw.Draw(panel_mask).rounded_rectangle(panel_box, radius=42, fill=255)
    panel.putalpha(panel_mask)
    panel = Image.alpha_composite(panel, Image.new("RGBA", CANVAS_SIZE, PALETTE["panel"]))
    canvas = Image.alpha_composite(canvas, panel)

    border = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border)
    border_draw.rounded_rectangle(panel_box, radius=42, outline=PALETTE["panel_border"], width=3)
    canvas = Image.alpha_composite(canvas, border)

    fit = ImageOps.contain(plan, (1120, 780), Image.Resampling.LANCZOS)
    fit = fit.filter(ImageFilter.UnsharpMask(radius=1.2, percent=130, threshold=2))
    pos = ((CANVAS_SIZE[0] - fit.width) // 2, (CANVAS_SIZE[1] - fit.height) // 2)
    canvas.alpha_composite(fit, pos)

    return canvas.convert("RGB")


def build_contact_sheet(items: list[dict[str, str]]) -> Path:
    cols = 2
    thumb_w = 720
    thumb_h = 540
    label_h = 104
    pad = 34
    rows = (len(items) + cols - 1) // cols
    canvas = Image.new("RGB", (pad + cols * (thumb_w + pad), pad + rows * (thumb_h + label_h + pad)), (12, 12, 13))
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(30, bold=True)
    meta_font = load_font(20)

    for index, item in enumerate(items):
        image = Image.open(ROOT / item["output"]).convert("RGB")
        image = ImageOps.fit(image, (thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = pad + (index % cols) * (thumb_w + pad)
        y = pad + (index // cols) * (thumb_h + label_h + pad)
        canvas.paste(image, (x, y))
        draw.rounded_rectangle((x, y + thumb_h + 12, x + thumb_w, y + thumb_h + label_h), radius=18, fill=(20, 20, 22))
        draw.text((x + 20, y + thumb_h + 22), item["title"], font=title_font, fill=(236, 228, 217))
        draw.text((x + 20, y + thumb_h + 60), item["scenario"], font=meta_font, fill=(190, 180, 166))

    output = OUT_DIR / "contact_sheet.png"
    canvas.save(output, quality=96)
    return output


def main() -> None:
    clear_output_dir()
    counts = count_layouts()
    manifest: list[dict[str, str | int]] = []

    for preset in PRESETS:
        source_path = ROOT / preset.source
        image = Image.open(source_path).convert("RGBA").crop(preset.crop_box)
        plan = clean_plan_image(image)
        board = compose_board(plan)
        output = OUT_DIR / f"{preset.slug}.png"
        board.save(output, quality=96)

        manifest.append(
            {
                "key": preset.key,
                "title": preset.title,
                "scenario": preset.scenario,
                "count": counts[preset.key],
                "source": preset.source,
                "output": str(output.relative_to(ROOT)).replace("\\", "/"),
            }
        )

    contact_sheet = build_contact_sheet(manifest)
    metadata = {
        "note": "Readable presentation boards generated from manually curated apartment plan crops.",
        "items": manifest,
        "contact_sheet": str(contact_sheet.relative_to(ROOT)).replace("\\", "/"),
    }
    (OUT_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Generated {len(manifest)} presentation boards")
    for item in manifest:
        print(f"{item['title']} -> {item['output']}")
    print(f"Contact sheet: {metadata['contact_sheet']}")


if __name__ == "__main__":
    main()
