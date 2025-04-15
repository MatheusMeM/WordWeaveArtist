# WordWeave Artist

## 1. Project Goal

WordWeave Artist is a desktop application designed to transform raster images into a unique "Word-Weave" / "Crossword Texture" ASCII art style. Instead of single characters, it uses user-defined words or predefined ASCII character sets, densely placed based on the source image's tones, creating a textual representation of the image.

## 2. Core Workflow & Data Handling

The application follows this general data flow:

1.  **Image Import:** The user imports a raster image (`original_image`). Displayed in "Input Image" preview.
2.  **Image Processing:** All user-selected adjustments (Brightness, Contrast, Saturation, Grayscale, Invert, Sharpness, Threshold, Edge Detect) are applied sequentially by `image_processor.apply_image_processing`. Edge detection results are inverted (black edges on white). The single resulting image (`processed_image`) is generated. This represents the final state after all user adjustments.
3.  **Processed Preview:** The final `processed_image` is displayed in the "Processed Image" preview pane, giving direct visual feedback on the source for mapping.
4.  **Gradient Source:** The user selects either a "Custom Word List" or a predefined "ASCII Character Set".
5.  **Brightness Mapping:** `render_engine.update_brightness_map` creates a mapping (`brightness_map`) based on the selected gradient source. It calculates the brightness of pixels in the `processed_image` (converting to grayscale 'L' mode internally if needed) and assigns words/characters to brightness ranges (0-254). Pure white (255) maps to `SKIP_RENDER_VALUE`.
6.  **Placement Generation:** `render_engine.generate_grid_placement` uses the `processed_image` (ensured to be 'L' mode) and `brightness_map`.
    *   The image is divided into a grid based on `word_density`.
    *   The average brightness of each grid cell is calculated from the `processed_image`.
    *   The `brightness_map` determines the word/character (`item`) for that brightness.
    *   If `item` is not `SKIP_RENDER_VALUE`, its target position (cell center) is stored.
7.  **Rendering:** `render_engine.render_word_grid` creates a new blank canvas.
    *   It iterates through the placement data.
    *   For each `item` and position, it loads the selected font (with fallbacks) using `render_engine.try_load_font`.
    *   The `item` is drawn onto the canvas.
8.  **Output Preview:** The final rendered image is displayed in the "Output Image" preview pane.

The processing and rendering pipeline (`trigger_processing_and_render` -> `_apply_image_processing` -> `trigger_render` -> `generate_grid_placement` -> `render_word_grid`) is executed whenever relevant UI controls are changed.

## 3. Key Code Components

*   **`src/main.py` (`MainWindow`):**
    *   Manages the main application window, UI layout (using `_create_left_panel`, `_create_right_panel`), and widgets (`PreviewLabel`, sliders, checkboxes, etc.).
    *   Holds the application state (image objects, processing settings, styling settings).
    *   Connects UI signals (button clicks, slider changes) to slots.
    *   Orchestrates the overall workflow by calling functions in helper modules.
    *   Handles file dialogs (`open_image_dialog`, `load_words_from_file`).
    *   Updates preview panes (`_update_single_preview`).
*   **`src/image_processor.py`:**
    *   `apply_image_processing()`: Takes the original image and all processing settings, applies them sequentially (color/tone -> grayscale -> effects -> threshold/edge), and returns the single final processed image used for preview and mapping.
*   **`src/render_engine.py`:**
    *   `update_brightness_map()`: Creates the brightness-to-item mapping dictionary.
    *   `get_item_for_brightness()`: Looks up an item in the map based on brightness.
    *   `try_load_font()`: Loads fonts with fallbacks.
    *   `generate_grid_placement()`: Calculates average brightness from the processed image cells and determines item placements.
    *   `render_word_grid()`: Draws the items onto the final output canvas.
*   **Constants:** Defined in respective modules (`main.py`, `render_engine.py`).

## 4. Setup & Running

1.  **Prerequisites:** Python 3.x, `pip`.
2.  **Clone/Download:** Get the project files.
3.  **Navigate:** Open a terminal in the `WordWeaveArtist` project directory.
4.  **Virtual Environment (Recommended):**
    *   Create: `python -m venv venv`
    *   Activate (Windows): `.\venv\Scripts\activate`
    *   Activate (macOS/Linux): `source venv/bin/activate`
5.  **Install Dependencies:** `pip install -r requirements.txt`
6.  **Run:** `python src/main.py` (Ensure the virtual environment is active).

## 5. Dependencies

See `requirements.txt` (PySide6, Pillow).

## 6. Development Roadmap

See `ROADMAP.md`.