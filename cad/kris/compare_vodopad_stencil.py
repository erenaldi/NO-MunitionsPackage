import argparse
from collections import deque
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter


REFERENCE_SIZE = (772, 397)
MIDDLE_CROP = (30, 132, 740, 238)


def threshold_reference(image):
    grayscale = image.convert("L")
    return grayscale.point(lambda value: 255 if value < 248 else 0)


def largest_component(mask):
    width, height = mask.size
    pixels = mask.load()
    visited = bytearray(width * height)
    largest = []

    for y in range(height):
        for x in range(width):
            offset = y * width + x
            if visited[offset] or pixels[x, y] == 0:
                continue

            component = []
            queue = deque([(x, y)])
            visited[offset] = 1
            while queue:
                current_x, current_y = queue.popleft()
                component.append((current_x, current_y))
                for next_x, next_y in (
                    (current_x - 1, current_y),
                    (current_x + 1, current_y),
                    (current_x, current_y - 1),
                    (current_x, current_y + 1),
                ):
                    if not (0 <= next_x < width and 0 <= next_y < height):
                        continue
                    next_offset = next_y * width + next_x
                    if visited[next_offset] or pixels[next_x, next_y] == 0:
                        continue
                    visited[next_offset] = 1
                    queue.append((next_x, next_y))

            if len(component) > len(largest):
                largest = component

    result = Image.new("L", mask.size)
    result_pixels = result.load()
    for x, y in largest:
        result_pixels[x, y] = 255
    return result.filter(ImageFilter.MaxFilter(3))


def render_mask(image):
    background = Image.new("RGB", image.size, image.getpixel((0, 0)))
    difference = ImageChops.difference(image.convert("RGB"), background).convert("L")
    return difference.point(lambda value: 255 if value > 6 else 0)


def centerline(mask):
    bbox = mask.getbbox()
    if bbox is None:
        raise ValueError("Silhouette mask is empty")
    left, top, right, bottom = bbox
    start_x = left + round((right - left) * 0.30)
    end_x = left + round((right - left) * 0.70)
    rows = []
    pixels = mask.load()
    for x in range(start_x, end_x):
        ys = [y for y in range(top, bottom) if pixels[x, y]]
        if ys:
            rows.append((ys[0] + ys[-1]) / 2.0)
    return sum(rows) / len(rows)


def outline(mask):
    expanded = mask.filter(ImageFilter.MaxFilter(5))
    contracted = mask.filter(ImageFilter.MinFilter(5))
    return ImageChops.subtract(expanded, contracted)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("render", type=Path)
    parser.add_argument("outline_output", type=Path)
    parser.add_argument("overlay_output", type=Path)
    args = parser.parse_args()

    reference = Image.open(args.reference).convert("RGB")
    scale_x = reference.width / REFERENCE_SIZE[0]
    scale_y = reference.height / REFERENCE_SIZE[1]
    crop_box = tuple(
        round(value * (scale_x if index % 2 == 0 else scale_y))
        for index, value in enumerate(MIDDLE_CROP)
    )
    reference_crop = reference.crop(crop_box)
    reference_mask = largest_component(threshold_reference(reference_crop))
    reference_bbox = reference_mask.getbbox()
    if reference_bbox is None:
        raise ValueError("No middle-missile silhouette found")
    reference_mask = reference_mask.crop(reference_bbox)
    reference_center = centerline(reference_mask)

    render = Image.open(args.render).convert("RGB").rotate(90, expand=True)
    model_mask = render_mask(render)
    model_bbox = model_mask.getbbox()
    if model_bbox is None:
        raise ValueError("No CAD silhouette found")
    render = render.crop(model_bbox)
    model_mask = model_mask.crop(model_bbox)
    model_center = centerline(model_mask)

    scale = render.width / reference_mask.width
    scaled_height = round(reference_mask.height * scale)
    reference_mask = reference_mask.resize(
        (render.width, scaled_height), Image.Resampling.NEAREST
    )
    reference_center *= scale
    reference_outline = outline(reference_mask)

    red_outline = Image.new("RGBA", reference_mask.size, (220, 30, 30, 0))
    red_outline.putalpha(reference_outline)
    args.outline_output.parent.mkdir(parents=True, exist_ok=True)
    outline_preview = Image.new("RGB", reference_mask.size, "white")
    outline_preview.paste((220, 30, 30), mask=reference_outline)
    outline_preview.save(args.outline_output)

    padding = 60
    canvas_height = max(render.height, scaled_height) + padding * 2
    canvas = Image.new("RGBA", (render.width + padding * 2, canvas_height), "white")
    model_y = round((canvas_height - render.height) / 2)
    canvas.alpha_composite(render.convert("RGBA"), (padding, model_y))

    model_center_y = model_y + model_center
    reference_y = round(model_center_y - reference_center)
    canvas.alpha_composite(red_outline, (padding, reference_y))

    draw = ImageDraw.Draw(canvas)
    draw.text((padding, 18), "Red: reference outline   Gray: CAD model", fill="black")
    args.overlay_output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(args.overlay_output)


if __name__ == "__main__":
    main()
