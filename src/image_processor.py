from PIL import Image, ImageOps, ImageEnhance, ImageFilter

def apply_image_processing(original_image, brightness_val, contrast_val, saturation_val, grayscale_val, invert, sharpness_val, threshold_enabled, threshold_val, edge_detect_enabled):
    """
    Applies all image pre-processing steps based on input parameters.
    Returns the single final processed image after all effects.
    This image is used for BOTH the middle preview AND brightness mapping.
    """
    if not original_image:
        return None

    current_image = original_image.copy()
    print("Applying image processing...")

    try:
        # --- Apply Color/Tone Adjustments ---
        is_color = current_image.mode not in ('L', '1')
        # Convert to RGB for color adjustments if needed, store original mode
        original_mode = current_image.mode
        if is_color and (saturation_val != 100 or grayscale_val > 0):
             if current_image.mode != 'RGB': current_image = current_image.convert('RGB')

        if brightness_val != 100:
            enhancer = ImageEnhance.Brightness(current_image); current_image = enhancer.enhance(brightness_val / 100.0)
        if contrast_val != 100:
            enhancer = ImageEnhance.Contrast(current_image); current_image = enhancer.enhance(contrast_val / 100.0)
        # Apply saturation only if image is still color *before* grayscale blend
        if current_image.mode == 'RGB' and saturation_val != 100:
             enhancer = ImageEnhance.Color(current_image); current_image = enhancer.enhance(saturation_val / 100.0)

        # --- Apply Grayscale ---
        if grayscale_val > 0:
             if current_image.mode != 'L':
                 grayscale_img = current_image.convert('L')
                 if grayscale_val == 100:
                     current_image = grayscale_img # Full conversion
                 else:
                     # Blend requires RGB modes
                     current_image_rgb = current_image.convert('RGB') if current_image.mode != 'RGB' else current_image
                     grayscale_rgb = grayscale_img.convert('RGB')
                     current_image = Image.blend(current_image_rgb, grayscale_rgb, grayscale_val / 100.0)

        # --- Apply Effects ---
        if sharpness_val != 100:
             enhancer = ImageEnhance.Sharpness(current_image); sharpness_factor = sharpness_val / 100.0
             current_image = enhancer.enhance(sharpness_factor)
        if invert:
             # Invert needs careful handling for different modes
             if current_image.mode == 'L': current_image = ImageOps.invert(current_image)
             elif current_image.mode == 'RGB': current_image = ImageOps.invert(current_image)
             elif current_image.mode == 'RGBA':
                  # Invert RGB, keep alpha
                  try:
                      rgb = ImageOps.invert(current_image.convert('RGB')); alpha = current_image.split()[3]
                      current_image = Image.merge('RGBA', (*rgb.split(), alpha))
                  except ValueError:
                      print("Warning: Invert failed for RGBA, skipping.")
             elif current_image.mode == '1': # Invert B&W
                 current_image = current_image.point(lambda p: 255 - p) # Simple invert for 0/255

        # --- Apply Final Conversion (Threshold or Edge Detect) IF enabled ---
        # These steps modify the image further *only if* selected
        if edge_detect_enabled:
             print("Applying Edge Detection...")
             # Edge detection requires grayscale input
             base_for_filter = current_image.convert('L') if current_image.mode != 'L' else current_image
             edge_image = base_for_filter.filter(ImageFilter.FIND_EDGES)
             current_image = ImageOps.invert(edge_image) # Invert to get black edges on white BG
        elif threshold_enabled:
             print(f"Applying threshold: {threshold_val}")
             # Threshold requires grayscale input
             base_for_filter = current_image.convert('L') if current_image.mode != 'L' else current_image
             bw_image = base_for_filter.point(lambda p: 255 if p >= threshold_val else 0, mode='1')
             current_image = bw_image.convert('L') # Convert back to L mode for consistency

        # --- Return the final processed image ---
        print("Image processing applied successfully.")
        return current_image # This single image is used for preview and mapping

    except Exception as e:
        print(f"Error during image processing: {e}")
        return None # Indicate failure