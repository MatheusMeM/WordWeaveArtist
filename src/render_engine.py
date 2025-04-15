import math
from PIL import Image, ImageDraw, ImageFont

# --- Constants ---
SKIP_RENDER_VALUE = None
FALLBACK_FONTS = ["arial.ttf", "times.ttf", "cour.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
# Define ASCII Gradients here as well
ASCII_GRADIENTS = { # Reverted name
    "Standard 10-level": " .:-=+*#%@",
    "Standard 70-level": ' .\'`^",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$',
    "Blocks": " ░▒▓█",
    "Simple": " .oO0@",
    "Structural": " .,:;|=+H#",
    "Binary": " 01",
    "Math Symbols": " .'-÷*≠≥≤∞#",
    "Circles": " ·∘°∙●⬤", # Unicode
    "Lines": " .-¯—|¦#",   # Unicode might be needed for some dashes/lines
    "Curves": " .,~)(SCG@",
    "Sparse Outline": "   .'*",
    "Noise Texture": "?!@#$%^&*()_+=-{}[]\\|;:'\",.<>/"
}

DEFAULT_GRADIENT_NAME = "Standard 10-level" # Keep default name if needed elsewhere

def update_brightness_map(gradient_items, gradient_source_name):
    """
    Creates the mapping from brightness levels (0-255) to gradient items (words/chars).
    Pure white (255) maps to SKIP_RENDER_VALUE.
    Returns the brightness map dictionary.
    """
    brightness_map = {}
    if not gradient_items:
        print("Gradient source is empty, cannot create brightness map.")
        return brightness_map

    # Use unique items, sorted (alphabetical for words, string order for ASCII)
    unique_items = []
    if gradient_source_name == "Custom Word List":
         unique_items = sorted(list(set(gradient_items)))
    else: # For ASCII gradients, maintain the defined order
         seen = set()
         unique_items = [x for x in gradient_items if not (x in seen or seen.add(x))]

    num_items = len(unique_items)
    if num_items == 0:
         print("Gradient source contains no usable items.")
         return brightness_map

    effective_range = 255.0
    bucket_size = effective_range / num_items
    current_threshold = 0.0
    temp_map = {}
    for i, item in enumerate(unique_items):
        upper_threshold = math.ceil(current_threshold + bucket_size)
        upper_threshold = min(upper_threshold, effective_range - 1)
        start_brightness = math.floor(current_threshold) + 1 if i > 0 else 0
        for brightness in range(int(start_brightness), int(upper_threshold) + 1):
             if brightness < 255: temp_map[brightness] = item
        current_threshold += bucket_size

    brightness_map = temp_map
    brightness_map[255] = SKIP_RENDER_VALUE # Explicitly map pure white to skip
    print(f"Brightness map updated with {num_items} items (plus skip for white).")
    return brightness_map

def get_item_for_brightness(brightness_map, brightness_value):
    """Returns the word/char/SKIP corresponding to the brightness value."""
    brightness_value = max(0, min(255, int(brightness_value)))
    return brightness_map.get(brightness_value, "?") # Use default '?' if somehow missing

def try_load_font(font_name, size):
    """Attempts to load a font, trying fallbacks if necessary."""
    try: return ImageFont.truetype(font_name, size)
    except IOError:
        print(f"Warning: Font '{font_name}' not found directly. Trying fallbacks...")
        for fallback in FALLBACK_FONTS:
            try: return ImageFont.truetype(fallback, size)
            except IOError: continue
        print(f"Error: Could not load font '{font_name}' or any fallback.")
        try: return ImageFont.load_default()
        except Exception as e_def: print(f"Error loading Pillow default font: {e_def}"); return None

def generate_grid_placement(processed_image_map, brightness_map, word_density):
    """Generates word/char placement data based on a grid using processed_image_map."""
    grid_placement_data = []
    if not processed_image_map or not brightness_map:
        print("Cannot generate grid: Missing processed map image or brightness map.")
        return grid_placement_data

    # Ensure map image is 'L' mode for pixel access
    map_image_l = processed_image_map
    if map_image_l.mode != 'L':
        print("Warning: Map image was not 'L' mode, converting.")
        map_image_l = map_image_l.convert('L')

    img_width, img_height = map_image_l.size
    area_per_100x100 = 100 * 100; total_pixels = img_width * img_height
    estimated_total_items = (total_pixels / area_per_100x100) * word_density
    if estimated_total_items <= 0: return grid_placement_data

    aspect_ratio = img_width / img_height if img_height > 0 else 1
    num_cols = max(1, int(math.sqrt(estimated_total_items * aspect_ratio)))
    num_rows = max(1, int(math.sqrt(estimated_total_items / aspect_ratio)))
    cell_width = img_width / num_cols; cell_height = img_height / num_rows
    print(f"Grid: {num_cols}x{num_rows} cells ({cell_width:.1f}x{cell_height:.1f} pixels/cell)")

    try: pixels = map_image_l.load()
    except Exception as e: print(f"Error accessing pixel data: {e}"); return grid_placement_data

    for r in range(num_rows):
        for c in range(num_cols):
            x1, y1 = int(c * cell_width), int(r * cell_height); x2, y2 = int((c + 1) * cell_width), int((r + 1) * cell_height)
            x1, y1 = max(0, x1), max(0, y1); x2, y2 = min(img_width, x2), min(img_height, y2)
            if x1 >= x2 or y1 >= y2: continue
            try:
                total_brightness = 0; count = 0
                for y_pix in range(y1, y2):
                    for x_pix in range(x1, x2): total_brightness += pixels[x_pix, y_pix]; count += 1
                if count == 0: continue
                avg_brightness = total_brightness / count
            except Exception as e_stat: print(f"Error calculating cell brightness at ({r},{c}): {e_stat}"); continue

            item = get_item_for_brightness(brightness_map, avg_brightness)
            if item is not SKIP_RENDER_VALUE:
                target_x = (x1 + x2) / 2; target_y = (y1 + y2) / 2
                grid_placement_data.append((item, (target_x, target_y)))

    print(f"Generated {len(grid_placement_data)} grid placements (skipped white areas).")
    return grid_placement_data

def render_word_grid(original_image_size, grid_placement_data, font_name, font_size):
    """Renders the words/chars based on placement data."""
    if not original_image_size: return None
    render_width, render_height = original_image_size

    if not grid_placement_data:
         print("Render skipped: No items to place.")
         return Image.new('RGB', (render_width, render_height), color=(255, 255, 255))

    img = Image.new('RGB', (render_width, render_height), color = (255, 255, 255))
    d = ImageDraw.Draw(img)
    font = try_load_font(font_name, font_size)

    if font is None:
        print(f"Render failed: Could not load font '{font_name}'")
        return None # Indicate failure

    rendered_count = 0
    for item, (target_x, target_y) in grid_placement_data:
        if item is SKIP_RENDER_VALUE: continue # Should be pre-filtered
        try:
            # Use anchor='mm' for centering if available (newer Pillow)
            try: d.text((target_x, target_y), str(item), fill=(0, 0, 0), font=font, anchor="mm")
            except TypeError: # Fallback for older Pillow
                bbox = d.textbbox((0, 0), str(item), font=font); text_width = bbox[2] - bbox[0]; text_height = bbox[3] - bbox[1]
                draw_x = target_x - text_width / 2; draw_y = target_y - text_height / 2
                d.text((draw_x, draw_y), str(item), fill=(0, 0, 0), font=font)
            rendered_count += 1
        except Exception as e: print(f"Error drawing item '{item}': {e}")

    print(f"Rendered {rendered_count} items onto grid using font '{font.path if hasattr(font, 'path') else font_name}'.")
    return img