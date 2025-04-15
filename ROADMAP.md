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
- `[x]` Brightness-to-Word/Character Mapping (Handles skip white)
- `[x]` Predefined Character Set Gradients (Selection implemented)
- `[x]` Custom Word List Gradient Usage (Selection implemented)

## UI & Controls

**1. Input/Output & Basic Setup:**
- `[x]` Main Window Structure (PySide6)
- `[x]` Left Settings Panel Layout
- `[x]` Right Preview Panel Layout (3 Previews Implemented)
- `[x]` Original Image Preview Area
- `[x]` Processed (B&W) Image Preview Area
- `[x]` Final Render Preview Area
- `[x]` Image Import Button
- `[x]` Word List Input (Text Area)
- `[x]` Word List Input (Load from .txt file)
- `[ ]` Reset Settings Button
- `[ ]` Copy Art to Clipboard Button

**2. Image Pre-processing Controls:**
- `[ ]` DELETE Automatic Black & White Conversion 
- `[ ]` Adjustable Thresholding Slider with a toogle check box to enable or disable the feature
- `[ ]` Brightness Slider
- `[ ]` Saturation Slider
- `[ ]` Grayscale Slider
- `[ ]` Contrast Slider
- `[ ]` Hue Slider
- `[ ]` Invert Colors Toggle
- `[ ]` Sharpness Slider
- `[ ]` Edge Detection Slider with a toogle check box to enable or disable the feature 

**3. Word Generation & Styling Controls:**
- `[x]` Word Density Control (SpinBox)
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
- `[x]` Step 1: Project Setup
- `[x]` Step 2: Basic GUI Window (PySide6)
- `[x]` Step 3: Image Loading & Display (Multi-preview)
- `[x]` Step 4: B&W Conversion Implemented (Fixed Threshold)
- `[x]` Step 5: Word List Input
- `[x]` Step 6: Font Selection & Basic Rendering (Workaround implemented)
- `[x]` Step 7: Brightness-to-Item Mapping Logic (Handles skip white)
- `[x]` Step 8: Basic Placement Strategy (Grid-Based) Implemented
- `[x]` Step 9: Rendering Engine V1 (Grid) Implemented (Handles skip white)
- `[x]` Step 10: Preview Panel Integration (3 Previews Implemented)