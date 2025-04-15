# WordWeave Artist

## 1. Project Goal

WordWeave Artist is a desktop application designed to transform raster images into a unique "Word-Weave" / "Crossword Texture" ASCII art style. Instead of single characters, it uses user-defined words or predefined ASCII character sets, densely placed based on the source image's tones, creating a textual representation of the image.

## 2. Core Workflow & Data Handling

The application follows this general data flow:

1.  **Image Import:** The user imports a raster image (`original_image`).
2.  **B&W Conversion:** The image is immediately converted to a black and white representation (`processed_image`) using a fixed threshold (currently `BW_THRESHOLD = 128`). Pure white pixels have a value of 255, black pixels 0.
3.  **Gradient Source:** The user selects either a "Custom Word List" (entered/loaded) or a predefined "ASCII Character Set".
4.  **Brightness Mapping:** Based on the selected gradient source, a mapping (`brightness_map`) is created. This map assigns each word/character to a range of brightness values (0-254). Pure white (255) is explicitly mapped to a special `SKIP_RENDER_VALUE`.
5.  **Placement Generation:** Currently uses a "Grid-Based" strategy (`generate_grid_placement`).
    *   The B&W `processed_image` is divided into a grid based on the selected `word_density`.
    *   The average brightness of each grid cell is calculated.
    *   The `brightness_map` is used to determine the word/character (`item`) for that average brightness.
    *   If the `item` is not `SKIP_RENDER_VALUE`, its target position (cell center) is stored in `grid_placement_data`.
6.  **Rendering:** The `render_word_grid` function creates a new blank canvas.
    *   It iterates through the `grid_placement_data`.
    *   For each `item` and its position, it attempts to load the selected font (`selected_font_name`, `selected_font_size`) using Pillow's `ImageFont.truetype`, with fallbacks for common fonts if the primary one fails.
    *   The `item` (word or character) is drawn onto the canvas, centered at its target position.
7.  **Preview Update:** The application displays three previews:
    *   `original_preview`: Shows the `original_image`.
    *   `bw_preview`: Shows the `processed_image` (B&W).
    *   `render_preview`: Shows the final `rendered_image` generated in step 6.

This entire process (steps 4-7) is triggered (`trigger_render`) whenever a relevant setting (image load, gradient source, word list, font, size, density) is changed.

## 3. Key Code Components (`src/main.py`)

*   **`MainWindow`:** The main application class inheriting from `QMainWindow`. Manages UI elements, state variables (images, settings), and connects signals/slots.
*   **`PreviewLabel`:** Custom `QLabel` subclass used for the three preview areas. Handles automatic scaling of the displayed `QPixmap` while maintaining aspect ratio when the label is resized.
*   **`_init_ui`, `_create_left_panel`, `_create_right_panel`:** Methods responsible for setting up the GUI layout and widgets.
*   **`_update_single_preview`:** Helper function to load a Pillow image into a specific `PreviewLabel`.
*   **`open_image_dialog`:** Handles importing the image, triggers B&W conversion and the main render process.
*   **`apply_bw_conversion`:** Converts the `original_image` to `processed_image` (B&W 'L' mode).
*   **`_get_current_gradient_list`:** Returns either the user's `word_list` or the characters from the `selected_ascii_gradient`.
*   **`_update_brightness_map`:** Creates the dictionary mapping brightness values (0-254) to words/chars, assigning `SKIP_RENDER_VALUE` to 255.
*   **`get_item_for_brightness`:** Looks up the appropriate word/char/SKIP value for a given brightness in the `brightness_map`.
*   **`generate_grid_placement`:** Calculates grid cell brightness from `processed_image` and determines which items (excluding SKIP) to place where, storing results in `grid_placement_data`.
*   **`_try_load_font`:** Attempts to load the selected font using Pillow, with fallbacks.
*   **`render_word_grid`:** Creates the final output image by drawing items from `grid_placement_data` using the loaded font.
*   **`trigger_render`:** Orchestrates the process: ensures B&W image exists, updates map, generates placement, renders grid, and updates the final preview pane.
*   **Signal Handlers (`parse_word_list_from_text`, `load_words_from_file`, `update_gradient_source`, etc.):** Respond to UI interactions, update application state, and call `trigger_render`.

## 4. Setup & Running

1.  **Prerequisites:** Python 3.x, `pip`.
2.  **Clone/Download:** Get the project files.
3.  **Navigate:** Open a terminal in the `WordWeaveArtist` project directory.
4.  **Virtual Environment (Recommended):**
    *   Create: `python -m venv venv`
    *   Activate (Windows): `.\venv\Scripts\activate`
    *   Activate (macOS/Linux): `source venv/bin/activate`
5.  **Install Dependencies:** `pip install -r requirements.txt`
6.  **Run:** `python src/main.py` (Ensure the virtual environment is active in the terminal).

## 5. Dependencies

See `requirements.txt` (Currently PySide6 and Pillow).

## 6. Development Roadmap

See `ROADMAP.md` for planned features and current implementation status.