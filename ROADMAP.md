# WordWeave Artist - Feature Roadmap

This document tracks the implementation status of features based on the initial concept and feedback.

**Status Legend:**
- `[ ] Not Started`
- `[/]` Partially Implemented
- `[x]` Implemented
- `[!] Needs Change/Review` (Based on feedback or issues)

---

## Core Functionality
- `[x]` Image Import (PNG, JPG, BMP)
- `[/]` Word/Character-Based Rendering Engine (Grid logic implemented, skips white)
- `[x]` Brightness-to-Word/Character Mapping (Handles skip white, uses final processed image brightness)
- `[x]` Predefined Character Set Gradients (Selection implemented)
- `[x]` Custom Word List Gradient Usage (Selection implemented)

## UI & Controls

**1. Input/Output & Basic Setup:**
- `[x]` Main Window Structure (PySide6)
- `[x]` Left Settings Panel Layout
- `[x]` Right Preview Panel Layout (3 Previews Implemented)
- `[x]` Input Image Preview Area
- `[x]` Processed Image Preview Area (Shows final image after all processing)
- `[x]` Output Image Preview Area (Rendered ASCII Art)
- `[x]` Image Import Button
- `[x]` Word List Input (Text Area)
- `[x]` Word List Input (Load from .txt file)
- `[ ]` Reset Settings Button
- `[ ]` Copy Art to Clipboard Button

**2. Image Pre-processing Controls:**
- `[x]` Adjustable Thresholding Slider & Toggle
- `[x]` Brightness Slider
- `[x]` Saturation Slider
- `[x]` Grayscale Slider
- `[x]` Contrast Slider
- `[x]` Invert Colors Toggle
- `[x]` Sharpness Slider
- `[x]` Edge Detection Toggle (Simple Filter, Inverted Output)

**3. Word Generation & Styling Controls:**
- `[x]` Word Density Control (SpinBox, Increased Max)
- `[!]` Font Selection Dropdown (System Fonts - Workaround Implemented)
- `[ ]` Font Selection (Import Custom TTF/OTF) - *Enhancement Needed*
- `[x]` Font Size Control (SpinBox)
- `[x]` Gradient Source Selection Dropdown (Custom List vs. Predefined ASCII)
- `[ ]` Word Placement Strategy Dropdown (Grid-Based, Organic/Iterative)
- `[ ]` Word Orientation Options
- `[ ]` Space Density / Word Spacing Slider
- `[ ]` Quality Enhancements Dropdown (Anti-Aliasing)

**4. Presentation & Export Controls:**
- `[ ]` Background Color Picker
- `[ ]` Transparent Background (PNG) Toggle
- `[ ]` Transparent Frame Slider
- `[ ]` Output Width Input
- `[ ]` Output Height Input (Optional Aspect Ratio Link)
- `[ ]` JPG Quality Slider
- `[ ]` Save as PNG Button
- `[ ]` Save as JPG Button

## Performance
- `[ ]` Real-time Preview Optimizations (Debouncing, Downscaling, Async)

---
*Implementation Steps Status:*
- `[x]` Step 1-10: Core structure, UI, basic rendering, multi-preview implemented.
- `[x]` Step 11: Image Pre-processing Controls Added & Integrated.
- `[x]` Step 12: Processed Preview shows final mapping image.
- `[x]` Step 13: Density limit increased.
- `[x]` Step 14: Refactored into `image_processor.py` and `render_engine.py`.
- `[x]` Step 15: Corrected processed preview logic and naming.
- `[x]` Step 16: Inverted Edge Detection output.