import sys
import os
import math
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QSizePolicy, QPushButton, QFileDialog, QTextEdit,
    QGroupBox, QFontComboBox, QSpinBox, QComboBox, QSlider, QCheckBox,
    QSpacerItem
)
from PySide6.QtGui import QPalette, QColor, QPixmap, QFontDatabase
from PySide6.QtCore import Qt, Slot, QSize

# Import Pillow
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter
from PIL.ImageQt import ImageQt

# --- Constants ---
DEFAULT_FONT_SIZE = 12
DEFAULT_DENSITY = 10
MAX_DENSITY = 500 # Increased max density
DEFAULT_THRESHOLD = 128
DEFAULT_BRIGHTNESS = 100
DEFAULT_CONTRAST = 100
DEFAULT_SATURATION = 100
DEFAULT_HUE = 0 # Hue not implemented yet
DEFAULT_SHARPNESS = 100
FALLBACK_FONTS = ["arial.ttf", "times.ttf", "cour.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
ASCII_GRADIENTS = {
    "Standard 10-level": " .:-=+*#%@",
    "Standard 70-level": ' .\'`^",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$',
    "Blocks": " ░▒▓█",
    "Simple": " .oO0@",
}
DEFAULT_GRADIENT_NAME = "Standard 10-level"
SKIP_RENDER_VALUE = None

# Helper function to create labeled sliders
def create_labeled_slider(label_text, min_val, max_val, default_val, parent_layout, change_slot, tooltip=""):
    """Creates a QLabel and QSlider pair and adds them to the layout."""
    hbox = QHBoxLayout()
    label = QLabel(f"{label_text}: {default_val}")
    label.setMinimumWidth(100) # Align labels somewhat
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(min_val, max_val)
    slider.setValue(default_val)
    slider.setToolTip(tooltip)
    # Update label text when slider value changes
    slider.valueChanged.connect(lambda value, lbl=label, txt=label_text: lbl.setText(f"{txt}: {value}"))
    # Connect the main slot to handle processing/rendering
    slider.valueChanged.connect(change_slot)
    hbox.addWidget(label)
    hbox.addWidget(slider)
    parent_layout.addLayout(hbox)
    return label, slider # Return widgets for potential later access

class PreviewLabel(QLabel):
    """Custom QLabel for previews that handles scaling on resize."""
    def __init__(self, text=""):
        super().__init__(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.setScaledContents(False)
        self._pixmap = QPixmap()

    def setPixmap(self, pixmap):
        """Sets the internal pixmap and scales it for display."""
        if pixmap and not pixmap.isNull():
            self._pixmap = pixmap
            self._scale_pixmap()
        else:
            self._pixmap = QPixmap()
            super().setPixmap(QPixmap()) # Clear the label pixmap

    def clear(self):
        """Clears the pixmap and text."""
        self._pixmap = QPixmap()
        super().clear()
        super().setText("")

    def resizeEvent(self, event):
        """Rescales the internal pixmap when the label is resized."""
        if not self._pixmap.isNull():
            self._scale_pixmap()
        super().resizeEvent(event)

    def _scale_pixmap(self):
        """Scales the stored pixmap to fit the label size."""
        if self._pixmap.isNull():
            return
        scaled_pixmap = self._pixmap.scaled(self.size(),
                                            Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)
        super().setPixmap(scaled_pixmap)


class MainWindow(QMainWindow):
    """Main application window."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WordWeave Artist")
        self.setGeometry(100, 100, 1400, 800)

        # State variables
        self.original_image = None
        self.processed_image_display = None # Image after color/tone adjustments for display
        self.processed_image_map = None   # Image after final conversion (gray/thresh/edge) for mapping
        self.rendered_image = None
        self.word_list = []
        self.selected_font_name = None
        self.selected_font_size = DEFAULT_FONT_SIZE
        self.brightness_map = {}
        self.word_density = DEFAULT_DENSITY
        self.grid_placement_data = []
        self.gradient_source = "Custom Word List"
        self.selected_ascii_gradient = ASCII_GRADIENTS[DEFAULT_GRADIENT_NAME]
        # Image Processing States
        self.threshold_enabled = False
        self.threshold_value = DEFAULT_THRESHOLD
        self.brightness_value = DEFAULT_BRIGHTNESS
        self.contrast_value = DEFAULT_CONTRAST
        self.saturation_value = DEFAULT_SATURATION
        self.hue_value = DEFAULT_HUE # Not implemented yet
        self.grayscale_value = 0
        self.invert_enabled = False
        self.sharpness_value = DEFAULT_SHARPNESS
        self.edge_detect_enabled = False

        # --- UI Setup ---
        self._init_ui()
        self.update_selected_font(self.font_combo.currentFont()) # Initialize font name
        self.show()

    def _init_ui(self):
        """Initializes the user interface components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        left_panel = self._create_left_panel()
        main_layout.addWidget(left_panel)

        right_panel = self._create_right_panel()
        main_layout.addWidget(right_panel)

        main_layout.setStretchFactor(left_panel, 1)
        main_layout.setStretchFactor(right_panel, 4)

    def _create_left_panel(self):
        """Creates the left settings panel widget."""
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.Shape.StyledPanel)
        left_panel.setFixedWidth(350)
        left_palette = left_panel.palette()
        left_palette.setColor(QPalette.ColorRole.Window, QColor(230, 230, 230))
        left_panel.setAutoFillBackground(True)
        left_panel.setPalette(left_palette)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Image Pre-processing Group ---
        image_group = QGroupBox("Image Pre-processing")
        image_layout = QVBoxLayout()
        # Import Button
        self.import_button = QPushButton("Import Image")
        self.import_button.clicked.connect(self.open_image_dialog)
        image_layout.addWidget(self.import_button)

        # Basic Adjustments (Sliders)
        self.brightness_label, self.brightness_slider = create_labeled_slider(
            "Brightness", 0, 200, self.brightness_value, image_layout, self.trigger_processing_and_render, "Adjust brightness (100=original)")
        self.contrast_label, self.contrast_slider = create_labeled_slider(
            "Contrast", 0, 200, self.contrast_value, image_layout, self.trigger_processing_and_render, "Adjust contrast (100=original)")
        self.saturation_label, self.saturation_slider = create_labeled_slider(
            "Saturation", 0, 200, self.saturation_value, image_layout, self.trigger_processing_and_render, "Adjust color saturation (100=original)")
        # Hue slider placeholder (not implemented)
        # self.hue_label, self.hue_slider = create_labeled_slider("Hue Shift", -180, 180, self.hue_value, image_layout, self.trigger_processing_and_render, "Shift colors (-180 to +180 degrees)")
        self.grayscale_label, self.grayscale_slider = create_labeled_slider(
            "Grayscale", 0, 100, self.grayscale_value, image_layout, self.trigger_processing_and_render, "Convert to grayscale (100=full)")

        # Toggles and Effects
        self.invert_checkbox = QCheckBox("Invert Colors")
        self.invert_checkbox.setChecked(self.invert_enabled)
        self.invert_checkbox.stateChanged.connect(self.update_invert_enabled)
        image_layout.addWidget(self.invert_checkbox)

        self.sharpness_label, self.sharpness_slider = create_labeled_slider(
            "Sharpness", 0, 300, self.sharpness_value, image_layout, self.trigger_processing_and_render, "Adjust sharpness (100=original)")

        # Threshold Controls
        threshold_hbox = QHBoxLayout()
        self.threshold_checkbox = QCheckBox("Enable Threshold")
        self.threshold_checkbox.setChecked(self.threshold_enabled)
        self.threshold_checkbox.stateChanged.connect(self.update_threshold_enabled)
        threshold_hbox.addWidget(self.threshold_checkbox)
        self.threshold_value_label = QLabel(f"Value: {self.threshold_value}")
        self.threshold_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        threshold_hbox.addWidget(self.threshold_value_label)
        image_layout.addLayout(threshold_hbox)

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(0, 255)
        self.threshold_slider.setValue(self.threshold_value)
        self.threshold_slider.valueChanged.connect(self.update_threshold_value)
        self.threshold_slider.setEnabled(self.threshold_enabled)
        image_layout.addWidget(self.threshold_slider)

        # Edge Detection Controls
        edge_hbox = QHBoxLayout()
        self.edge_checkbox = QCheckBox("Enable Edge Detect")
        self.edge_checkbox.setChecked(self.edge_detect_enabled)
        self.edge_checkbox.stateChanged.connect(self.update_edge_detect_enabled)
        edge_hbox.addWidget(self.edge_checkbox)
        # Add dropdown for edge type later if needed
        image_layout.addLayout(edge_hbox)

        image_group.setLayout(image_layout)
        left_layout.addWidget(image_group)

        # --- Word/Gradient Source Group ---
        source_group = QGroupBox("Gradient Source")
        source_layout = QVBoxLayout()
        self.gradient_source_combo = QComboBox()
        self.gradient_source_combo.addItem("Custom Word List")
        self.gradient_source_combo.addItems(ASCII_GRADIENTS.keys())
        self.gradient_source_combo.currentTextChanged.connect(self.update_gradient_source)
        source_layout.addWidget(self.gradient_source_combo)
        self.word_list_label = QLabel("Custom Words:")
        source_layout.addWidget(self.word_list_label)
        self.word_list_edit = QTextEdit()
        self.word_list_edit.setPlaceholderText("Enter words here...")
        self.word_list_edit.setFixedHeight(80)
        self.word_list_edit.textChanged.connect(self.parse_word_list_from_text)
        source_layout.addWidget(self.word_list_edit)
        self.load_words_button = QPushButton("Load Words from File (.txt)")
        self.load_words_button.clicked.connect(self.load_words_from_file)
        source_layout.addWidget(self.load_words_button)
        source_group.setLayout(source_layout)
        left_layout.addWidget(source_group)

        # --- Generation & Styling Group ---
        gen_style_group = QGroupBox("Generation & Styling")
        gen_style_layout = QVBoxLayout()
        font_label = QLabel("Font:")
        gen_style_layout.addWidget(font_label)
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(self.update_selected_font)
        gen_style_layout.addWidget(self.font_combo)
        size_label = QLabel("Font Size:")
        gen_style_layout.addWidget(size_label)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 72)
        self.font_size_spin.setValue(self.selected_font_size)
        self.font_size_spin.valueChanged.connect(self.update_font_size)
        gen_style_layout.addWidget(self.font_size_spin)
        density_label = QLabel("Density:")
        gen_style_layout.addWidget(density_label)
        self.density_spin = QSpinBox()
        self.density_spin.setRange(1, MAX_DENSITY) # Use constant
        self.density_spin.setValue(self.word_density)
        self.density_spin.setToolTip(f"Approx items per 100x100 area (Max: {MAX_DENSITY})")
        self.density_spin.valueChanged.connect(self.update_density)
        gen_style_layout.addWidget(self.density_spin)
        self.import_font_button = QPushButton("Import Custom Font (.ttf/.otf)")
        self.import_font_button.setEnabled(False)
        self.import_font_button.setToolTip("Feature not yet implemented")
        gen_style_layout.addWidget(self.import_font_button)
        gen_style_group.setLayout(gen_style_layout)
        left_layout.addWidget(gen_style_group)

        left_layout.addStretch()
        self._update_word_list_controls_state() # Set initial state
        return left_panel

    def _create_right_panel(self):
        """Creates the right panel containing the three preview areas."""
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        grid_layout = QGridLayout(right_panel)
        grid_layout.setSpacing(10)
        self.original_preview = PreviewLabel("Original Image")
        self.bw_preview = PreviewLabel("Processed Image") # Shows intermediate processing
        self.render_preview = PreviewLabel("WordWeave Render")
        grid_layout.addWidget(QLabel("<b>Original:</b>"), 0, 0, Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.original_preview, 1, 0)
        grid_layout.addWidget(QLabel("<b>Processed:</b>"), 0, 1, Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.bw_preview, 1, 1)
        grid_layout.addWidget(QLabel("<b>Rendered Output:</b>"), 0, 2, Qt.AlignmentFlag.AlignCenter)
        grid_layout.addWidget(self.render_preview, 1, 2)
        grid_layout.setColumnStretch(0, 1); grid_layout.setColumnStretch(1, 1); grid_layout.setColumnStretch(2, 1)
        grid_layout.setRowStretch(1, 1)
        return right_panel

    # --- Slots and Event Handlers ---

    def _update_single_preview(self, label_widget, image_to_display):
        """Helper to update a specific PreviewLabel widget."""
        if image_to_display:
            try:
                display_image = image_to_display
                # Ensure RGBA for QPixmap conversion, Pillow handles other modes internally
                if display_image.mode != 'RGBA':
                    display_image = display_image.convert('RGBA')
                q_image = ImageQt(display_image)
                pixmap = QPixmap.fromImage(q_image)
                label_widget.setPixmap(pixmap) # Let the custom label handle scaling
            except Exception as e:
                print(f"Error updating preview: {e}")
                label_widget.setText(f"Error:\n{e}")
                label_widget.setPixmap(QPixmap()) # Clear pixmap on error
        else:
            label_widget.clear() # Clear pixmap
            label_widget.setText("N/A") # Set placeholder text

    @Slot()
    def open_image_dialog(self):
        """Opens dialog, loads image, updates original preview, triggers processing & render."""
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp)")
        file_dialog.setViewMode(QFileDialog.ViewMode.Detail)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                image_path = file_paths[0]
                print(f"Selected image: {image_path}")
                try:
                    self.original_image = Image.open(image_path)
                    self._update_single_preview(self.original_preview, self.original_image)
                    # Reset processing controls to defaults when loading new image? Optional.
                    # self.reset_processing_controls() # Add this method if desired
                    self.trigger_processing_and_render() # Trigger initial processing and render
                    print("Image loaded.")
                except Exception as e:
                    print(f"Error loading image: {e}")
                    # Clear all state on error
                    self.original_image = None; self.processed_image_display = None; self.processed_image_map = None; self.rendered_image = None
                    self.original_preview.clear(); self.bw_preview.clear(); self.render_preview.clear()
                    self.original_preview.setText(f"Error:\n{e}")

    # --- Image Processing Slots ---
    @Slot(int)
    def update_threshold_enabled(self, state):
        self.threshold_enabled = (state == Qt.CheckState.Checked.value)
        self.threshold_slider.setEnabled(self.threshold_enabled)
        print(f"Thresholding {'enabled' if self.threshold_enabled else 'disabled'}")
        # If enabling threshold, disable edge detect (mutually exclusive for map image)
        if self.threshold_enabled and self.edge_detect_enabled:
            self.edge_checkbox.setChecked(False) # This will trigger update_edge_detect_enabled
        else:
            self.trigger_processing_and_render()

    @Slot(int)
    def update_threshold_value(self, value):
        self.threshold_value = value
        self.threshold_value_label.setText(f"Value: {value}")
        if self.threshold_enabled: self.trigger_processing_and_render()

    @Slot(int)
    def update_invert_enabled(self, state):
        self.invert_enabled = (state == Qt.CheckState.Checked.value)
        print(f"Invert {'enabled' if self.invert_enabled else 'disabled'}")
        self.trigger_processing_and_render()

    @Slot(int)
    def update_edge_detect_enabled(self, state):
        self.edge_detect_enabled = (state == Qt.CheckState.Checked.value)
        print(f"Edge Detect {'enabled' if self.edge_detect_enabled else 'disabled'}")
        # If enabling edge detect, disable threshold (mutually exclusive for map image)
        if self.edge_detect_enabled and self.threshold_enabled:
            self.threshold_checkbox.setChecked(False) # This will trigger update_threshold_enabled
        else:
            self.trigger_processing_and_render()

    # Generic slot for sliders that just need to trigger processing
    @Slot()
    def trigger_processing_and_render(self):
        """Slot connected to most processing sliders/checkboxes. Updates state and triggers processing/render."""
        # Update internal state from sliders/checkboxes first
        self.brightness_value = self.brightness_slider.value()
        self.contrast_value = self.contrast_slider.value()
        self.saturation_value = self.saturation_slider.value()
        # self.hue_value = self.hue_slider.value() # Hue skipped
        self.grayscale_value = self.grayscale_slider.value()
        self.sharpness_value = self.sharpness_slider.value()
        # Checkbox states are updated directly via their specific slots (update_invert_enabled etc.)

        if self._apply_image_processing(): # Apply processing first
            self.trigger_render() # Then trigger render if processing was ok

    @Slot()
    def _apply_image_processing(self):
        """Applies ALL image pre-processing steps based on UI controls.
           Updates self.processed_image_display and self.processed_image_map.
        """
        if not self.original_image:
            self.processed_image_display = None; self.processed_image_map = None
            self._update_single_preview(self.bw_preview, None)
            return False

        current_image = self.original_image.copy()
        print("Applying image processing...")

        try:
            # --- Apply Color/Tone Adjustments (Order can matter) ---
            is_color = current_image.mode not in ('L', '1')

            # Convert to RGB for color adjustments if needed
            if is_color and (self.saturation_value != 100 or self.grayscale_value > 0): # Hue skipped
                 if current_image.mode != 'RGB': current_image = current_image.convert('RGB')

            if self.brightness_value != 100:
                enhancer = ImageEnhance.Brightness(current_image); current_image = enhancer.enhance(self.brightness_value / 100.0)
            if self.contrast_value != 100:
                enhancer = ImageEnhance.Contrast(current_image); current_image = enhancer.enhance(self.contrast_value / 100.0)
            # Apply saturation only if image is still color
            if current_image.mode == 'RGB' and self.saturation_value != 100:
                enhancer = ImageEnhance.Color(current_image); current_image = enhancer.enhance(self.saturation_value / 100.0)

            # --- Apply Grayscale ---
            if self.grayscale_value > 0:
                 if current_image.mode != 'L': # Only apply if not already grayscale
                     grayscale_img = current_image.convert('L')
                     if self.grayscale_value == 100:
                         current_image = grayscale_img # Full conversion
                     else:
                         # Blend requires RGB modes
                         current_image_rgb = current_image.convert('RGB') if current_image.mode != 'RGB' else current_image
                         grayscale_rgb = grayscale_img.convert('RGB')
                         current_image = Image.blend(current_image_rgb, grayscale_rgb, self.grayscale_value / 100.0)

            # --- Apply Effects ---
            if self.sharpness_value != 100:
                 enhancer = ImageEnhance.Sharpness(current_image)
                 sharpness_factor = self.sharpness_value / 100.0
                 current_image = enhancer.enhance(sharpness_factor)

            if self.invert_enabled:
                 # Invert works best on L or RGB modes usually
                 if current_image.mode == 'L': current_image = ImageOps.invert(current_image)
                 elif current_image.mode == 'RGB': current_image = ImageOps.invert(current_image)
                 elif current_image.mode == 'RGBA':
                      rgb = ImageOps.invert(current_image.convert('RGB')); alpha = current_image.split()[3]
                      current_image = Image.merge('RGBA', (*rgb.split(), alpha))
                 # else: Invert might not work well on '1' mode directly

            # Store this version for the "Processed" preview pane
            self.processed_image_display = current_image.copy()
            self._update_single_preview(self.bw_preview, self.processed_image_display)

            # --- Final Conversion for Mapping ---
            # Always start from the state *after* color/tone/effects for mapping conversion
            image_for_map = current_image

            # Convert to Grayscale ('L' mode) as basis for threshold/edge/map
            if image_for_map.mode != 'L':
                grayscale_for_map = image_for_map.convert('L')
            else:
                grayscale_for_map = image_for_map # Already grayscale

            # Apply Edge Detection or Thresholding (Mutually Exclusive for map source)
            if self.edge_detect_enabled:
                 print("Applying Edge Detection for map...")
                 final_map_image = grayscale_for_map.filter(ImageFilter.FIND_EDGES)
                 # Optional: Invert edges? final_map_image = ImageOps.invert(final_map_image)
            elif self.threshold_enabled:
                 print(f"Applying threshold for map: {self.threshold_value}")
                 bw_image = grayscale_for_map.point(lambda p: 255 if p >= self.threshold_value else 0, mode='1')
                 final_map_image = bw_image.convert('L') # Use thresholded B&W for map
            else:
                 print("Using grayscale image for brightness map.")
                 final_map_image = grayscale_for_map # Use the grayscale version

            self.processed_image_map = final_map_image # Store the image used for mapping
            print("Image processing applied successfully.")
            return True

        except Exception as e:
            print(f"Error during image processing: {e}")
            # Fallback: show original in processed view? Or clear?
            self.processed_image_display = self.original_image.copy() if self.original_image else None
            self.processed_image_map = None
            self._update_single_preview(self.bw_preview, self.processed_image_display)
            self.bw_preview.setText(f"Processing Error:\n{e}") # Show error text too
            return False


    # --- Gradient/Word List Slots ---
    @Slot()
    def parse_word_list_from_text(self):
        text = self.word_list_edit.toPlainText(); delimiters = [',', '\n']; words = []; current_word = ''
        for char in text:
            if char in delimiters:
                if current_word: words.append(current_word)
                current_word = ''
            else: current_word += char
        if current_word: words.append(current_word)
        self.word_list = [word.strip() for word in words if word.strip()]
        if self.gradient_source == "Custom Word List": self._update_brightness_map(); self.trigger_render()

    @Slot()
    def load_words_from_file(self):
        file_dialog = QFileDialog(self); file_dialog.setNameFilter("Text Files (*.txt)"); file_dialog.setViewMode(QFileDialog.ViewMode.Detail); file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                file_path = file_paths[0]; print(f"Loading words from: {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f: lines = f.readlines(); loaded_words = [line.strip() for line in lines if line.strip()]; self.word_list_edit.setPlainText("\n".join(loaded_words)); print(f"Words loaded successfully.")
                except Exception as e: print(f"Error loading words from file: {e}")

    @Slot(str)
    def update_gradient_source(self, source_text):
        self.gradient_source = source_text; print(f"Gradient source changed to: {self.gradient_source}")
        if source_text != "Custom Word List": self.selected_ascii_gradient = ASCII_GRADIENTS.get(source_text, "?")
        self._update_word_list_controls_state(); self._update_brightness_map(); self.trigger_render()

    def _update_word_list_controls_state(self): enable = (self.gradient_source == "Custom Word List"); self.word_list_label.setEnabled(enable); self.word_list_edit.setEnabled(enable); self.load_words_button.setEnabled(enable)


    # --- Styling Slots ---
    @Slot()
    def update_selected_font(self, font): self.selected_font_name = font.family(); print(f"Selected Font: {self.selected_font_name}"); self.trigger_render()
    @Slot()
    def update_font_size(self, size): self.selected_font_size = size; print(f"Selected Font Size: {self.selected_font_size}"); self.trigger_render()
    @Slot()
    def update_density(self, density): self.word_density = density; print(f"Density: {self.word_density}"); self.trigger_render()


    # --- Core Logic ---
    def _get_current_gradient_list(self):
        if self.gradient_source == "Custom Word List": return self.word_list
        else: return list(self.selected_ascii_gradient)

    def _update_brightness_map(self):
        self.brightness_map = {}; gradient_items = self._get_current_gradient_list()
        if not gradient_items: print("Gradient source is empty..."); return
        unique_items = [];
        if self.gradient_source == "Custom Word List": unique_items = sorted(list(set(gradient_items)))
        else: seen = set(); unique_items = [x for x in gradient_items if not (x in seen or seen.add(x))]
        num_items = len(unique_items)
        if num_items == 0: print("Gradient source has no usable items."); return
        effective_range = 255.0; bucket_size = effective_range / num_items; current_threshold = 0.0; temp_map = {}
        for i, item in enumerate(unique_items):
            upper_threshold = math.ceil(current_threshold + bucket_size); upper_threshold = min(upper_threshold, effective_range - 1)
            start_brightness = math.floor(current_threshold) + 1 if i > 0 else 0
            for brightness in range(int(start_brightness), int(upper_threshold) + 1):
                 if brightness < 255: temp_map[brightness] = item
            current_threshold += bucket_size
        self.brightness_map = temp_map; self.brightness_map[255] = SKIP_RENDER_VALUE
        print(f"Brightness map updated with {num_items} items (plus skip for white).")

    def get_item_for_brightness(self, brightness_value):
        brightness_value = max(0, min(255, int(brightness_value)))
        return self.brightness_map.get(brightness_value, "?")

    def _try_load_font(self, font_name, size):
        try: return ImageFont.truetype(font_name, size)
        except IOError:
            print(f"Warning: Font '{font_name}' not found directly. Trying fallbacks...")
            for fallback in FALLBACK_FONTS:
                try: return ImageFont.truetype(fallback, size)
                except IOError: continue
            print(f"Error: Could not load font '{font_name}' or any fallback.")
            try: return ImageFont.load_default()
            except Exception as e_def: print(f"Error loading Pillow default font: {e_def}"); return None

    def generate_grid_placement(self):
        """Generates word/char placement data based on a grid using processed_image_map."""
        self.grid_placement_data = []
        if not self.processed_image_map or not self.brightness_map: print("Cannot generate grid..."); return
        img_width, img_height = self.processed_image_map.size
        area_per_100x100 = 100 * 100; total_pixels = img_width * img_height
        estimated_total_items = (total_pixels / area_per_100x100) * self.word_density
        if estimated_total_items <= 0: return
        aspect_ratio = img_width / img_height if img_height > 0 else 1
        num_cols = max(1, int(math.sqrt(estimated_total_items * aspect_ratio)))
        num_rows = max(1, int(math.sqrt(estimated_total_items / aspect_ratio)))
        cell_width = img_width / num_cols; cell_height = img_height / num_rows
        print(f"Grid: {num_cols}x{num_rows} cells ({cell_width:.1f}x{cell_height:.1f} pixels/cell)")
        try: pixels = self.processed_image_map.load()
        except Exception as e: print(f"Error accessing pixel data: {e}"); return
        for r in range(num_rows):
            for c in range(num_cols):
                x1, y1 = int(c * cell_width), int(r * cell_height); x2, y2 = int((c + 1) * cell_width), int((r + 1) * cell_height)
                x1, y1 = max(0, x1), max(0, y1); x2, y2 = min(img_width, x2), min(img_height, y2)
                if x1 >= x2 or y1 >= y2: continue
                try:
                    total_brightness = 0; count = 0
                    # Simple pixel iteration for average brightness
                    for y_pix in range(y1, y2):
                        for x_pix in range(x1, x2): total_brightness += pixels[x_pix, y_pix]; count += 1
                    if count == 0: continue
                    avg_brightness = total_brightness / count
                except Exception as e_stat: print(f"Error calculating cell brightness at ({r},{c}): {e_stat}"); continue
                item = self.get_item_for_brightness(avg_brightness)
                if item is not SKIP_RENDER_VALUE:
                    target_x = (x1 + x2) / 2; target_y = (y1 + y2) / 2
                    self.grid_placement_data.append((item, (target_x, target_y)))
        print(f"Generated {len(self.grid_placement_data)} grid placements (skipped white areas).")

    def render_word_grid(self):
        """Renders the words/chars, skipping items marked as SKIP_RENDER_VALUE."""
        if not self.original_image: return None
        if not self.grid_placement_data:
             print("Render skipped: No items to place.")
             render_width, render_height = self.original_image.size
             return Image.new('RGB', (render_width, render_height), color=(255, 255, 255))
        render_width, render_height = self.original_image.size
        img = Image.new('RGB', (render_width, render_height), color = (255, 255, 255))
        d = ImageDraw.Draw(img); font_name = self.selected_font_name; font_size = self.selected_font_size
        font = self._try_load_font(font_name, font_size)
        if font is None: self.render_preview.setText(f"Failed font load: '{font_name}'"); self.render_preview.setPixmap(QPixmap()); return None
        rendered_count = 0
        for item, (target_x, target_y) in self.grid_placement_data:
            if item is SKIP_RENDER_VALUE: continue
            try:
                try: d.text((target_x, target_y), str(item), fill=(0, 0, 0), font=font, anchor="mm")
                except TypeError: # Fallback for older Pillow
                    bbox = d.textbbox((0, 0), str(item), font=font); text_width = bbox[2] - bbox[0]; text_height = bbox[3] - bbox[1]
                    draw_x = target_x - text_width / 2; draw_y = target_y - text_height / 2
                    d.text((draw_x, draw_y), str(item), fill=(0, 0, 0), font=font)
                rendered_count += 1
            except Exception as e: print(f"Error drawing item '{item}': {e}")
        print(f"Rendered {rendered_count} items onto grid using font '{font.path if hasattr(font, 'path') else font_name}'.")
        return img

    def trigger_render(self):
        """Coordinates the steps needed generate and render the WordWeave. Assumes processing is done."""
        print("--- Triggering Render ---")
        self.rendered_image = None
        self.render_preview.clear(); self.render_preview.setText("Rendering...")
        QApplication.processEvents() # Allow UI to update text

        # 1. Ensure processed_image_map exists (created by _apply_image_processing)
        if not self.processed_image_map:
             print("Render cancelled: No processed image available for mapping."); self.render_preview.setText("No Map Image"); return

        # 2. Ensure brightness map is updated
        self._update_brightness_map()
        if not self.brightness_map: print("Render cancelled: Brightness map error."); self.render_preview.setText("No Map"); return

        # 3. Generate placement data using the processed_image_map
        self.generate_grid_placement()

        # 4. Render the grid
        self.rendered_image = self.render_word_grid()

        # 5. Update the specific render preview
        if self.rendered_image: self._update_single_preview(self.render_preview, self.rendered_image)
        else:
            if not self.render_preview.text(): self.render_preview.setText("Render Error")


# --- Main Execution ---
def main():
    """Main function to start the application."""
    print("Starting WordWeave Artist with PySide6...")
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()