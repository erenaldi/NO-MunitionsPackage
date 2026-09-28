import argparse
from collections import deque
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter


VIEW_CROPS = {
    "side": (145, 58, 1055, 224),
    "top": (145, 222, 1055, 351),
    "nose": (532, 370, 782, 616),
    "tail": (798, 370, 1048, 616),
}
ROTATE_RENDER = {"side": 90, "top": 90, "nose": 0, "tail": 0}
FLIP_REFERENCE = {"side": False, "top": True, "nose": False, "tail": False}


def extract_reference_features(image):
    grayscale = image.convert("L")
    dark_features = grayscale.point(lambda value: 255 if value < 228 else 0)
    return dark_features.filter(ImageFilter.MaxFilter(5))


def extract_render_mask(image):
    grayscale = image.convert("L")
    solid_geometry = grayscale.point(lambda value: 255 if value < 220 else 0)
    return solid_geometry.filter(ImageFilter.MinFilter(3)).filter(
        ImageFilter.MaxFilter(3)
    )


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
    return result


def fill_silhouette(mask):
    closed = mask.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(5))
    width, height = closed.size
    inverse = ImageChops.invert(closed)
    exterior = Image.new("L", closed.size)
    source = inverse.load()
    target = exterior.load()
    queue = deque()
    for x in range(width):
        queue.extend(((x, 0), (x, height - 1)))
    for y in range(height):
        queue.extend(((0, y), (width - 1, y)))
    while queue:
        x, y = queue.popleft()
        if target[x, y] or source[x, y] == 0:
            continue
        target[x, y] = 255
        for point in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= point[0] < width and 0 <= point[1] < height:
                queue.append(point)
    return ImageChops.invert(exterior)


def outline(mask):
    expanded = mask.filter(ImageFilter.MaxFilter(5))
    contracted = mask.filter(ImageFilter.MinFilter(5))
    return ImageChops.subtract(expanded, contracted)


def crop_to_mask(image, mask):
    bbox = mask.getbbox()
    if bbox is None:
        raise ValueError("Silhouette mask is empty")
    return image.crop(bbox), mask.crop(bbox)


def make_overlay(reference, render, view, output):
    reference_crop = reference.crop(VIEW_CROPS[view])
    if FLIP_REFERENCE[view]:
        reference_crop = reference_crop.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    reference_features = extract_reference_features(reference_crop)
    reference_mask = fill_silhouette(largest_component(reference_features))
    reference_bbox = reference_mask.getbbox()
    if reference_bbox is None:
        raise ValueError("Reference silhouette mask is empty")
    reference_mask = reference_mask.crop(reference_bbox)
    reference_features = reference_features.crop(reference_bbox)

    render = render.convert("RGB").rotate(ROTATE_RENDER[view], expand=True)
    render_mask = fill_silhouette(largest_component(extract_render_mask(render)))
    render, render_mask = crop_to_mask(render, render_mask)

    scale = render.width / reference_mask.width
    scaled_height = max(1, round(reference_mask.height * scale))
    target_size = (render.width, scaled_height)
    reference_mask = reference_mask.resize(target_size, Image.Resampling.NEAREST)
    reference_features = reference_features.resize(target_size, Image.Resampling.NEAREST)

    red_features = Image.new("RGBA", target_size, (220, 30, 30, 0))
    red_features.putalpha(reference_features.point(lambda value: value // 5))
    red_outline = Image.new("RGBA", target_size, (220, 30, 30, 0))
    red_outline.putalpha(outline(reference_mask))

    padding = 60
    canvas_height = max(render.height, scaled_height) + padding * 2
    canvas = Image.new("RGBA", (render.width + padding * 2, canvas_height), "white")
    model_y = round((canvas_height - render.height) * 0.5)
    reference_y = round((canvas_height - scaled_height) * 0.5)
    canvas.alpha_composite(render.convert("RGBA"), (padding, model_y))
    canvas.alpha_composite(red_features, (padding, reference_y))
    canvas.alpha_composite(red_outline, (padding, reference_y))
    ImageDraw.Draw(canvas).text(
        (padding, 18),
        f"{view.upper()} - red: R-93M reference   CAD: detailed Kris",
        fill="black",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("render_directory", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()

    reference = Image.open(args.reference).convert("RGB")
    for view in VIEW_CROPS:
        render_path = args.render_directory / f"IRM-S4_Kris_{view}.png"
        output_path = args.output_directory / f"IRM-S4_Kris_{view}_stencil.png"
        make_overlay(reference, Image.open(render_path), view, output_path)
        print(f"saved {output_path}")


if __name__ == "__main__":
    main()
