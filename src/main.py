import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QSizePolicy, QPushButton, QFileDialog, QTextEdit,
    QGroupBox, QFontComboBox, QSpinBox, QComboBox, QSlider, QCheckBox,
    QSpacerItem
)
from PySide6.QtGui import QPalette, QColor, QPixmap
from PySide6.QtCore import Qt, Slot, QSize

# Import Pillow and helper modules
from PIL import Image
from PIL.ImageQt import ImageQt
from image_processor import apply_image_processing # Import image processing function
from render_engine import ( # Import rendering functions and constants
    update_brightness_map,
    generate_grid_placement,
    render_word_grid,
    SKIP_RENDER_VALUE,
    ASCII_GRADIENTS, # Use the correct constant name
    DEFAULT_GRADIENT_NAME
)

# --- Constants ---
DEFAULT_FONT_SIZE = 12
DEFAULT_DENSITY = 10
MAX_DENSITY = 500
DEFAULT_THRESHOLD = 128
DEFAULT_BRIGHTNESS = 100
DEFAULT_CONTRAST = 100
DEFAULT_SATURATION = 100
DEFAULT_HUE = 0 # Not implemented yet
DEFAULT_SHARPNESS = 100

# Helper function to create labeled sliders
def create_labeled_slider(label_text, min_val, max_val, default_val, parent_layout, change_slot, tooltip=""):
    hbox = QHBoxLayout(); label = QLabel(f"{label_text}: {default_val}"); label.setMinimumWidth(100)
    slider = QSlider(Qt.Orientation.Horizontal); slider.setRange(min_val, max_val); slider.setValue(default_val)
    slider.setToolTip(tooltip)
    slider.valueChanged.connect(lambda value, lbl=label, txt=label_text: lbl.setText(f"{txt}: {value}"))
    slider.valueChanged.connect(change_slot)
    hbox.addWidget(label); hbox.addWidget(slider); parent_layout.addLayout(hbox)
    return label, slider

class PreviewLabel(QLabel):
    """Custom QLabel for previews that handles scaling on resize."""
    def __init__(self, text=""): super().__init__(text); self.setAlignment(Qt.AlignmentFlag.AlignCenter); self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored); self.setScaledContents(False); self._pixmap = QPixmap()
    def setPixmap(self, pixmap):
        if pixmap and not pixmap.isNull(): self._pixmap = pixmap; self._scale_pixmap()
        else: self._pixmap = QPixmap(); super().setPixmap(QPixmap())
    def clear(self): self._pixmap = QPixmap(); super().clear(); super().setText("")
    def resizeEvent(self, event):
        if not self._pixmap.isNull(): self._scale_pixmap()
        super().resizeEvent(event)
    def _scale_pixmap(self):
        if self._pixmap.isNull(): return
        scaled_pixmap = self._pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        super().setPixmap(scaled_pixmap)

class MainWindow(QMainWindow):
    """Main application window - Handles UI and state management."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WordWeave Artist")
        self.setGeometry(100, 100, 1400, 800)

        # --- State Variables ---
        self.original_image = None
        self.processed_image = None # Stores result after ALL processing steps
        self.rendered_image = None
        self.word_list = []; self.selected_font_name = None; self.selected_font_size = DEFAULT_FONT_SIZE
        self.brightness_map = {}; self.word_density = DEFAULT_DENSITY; self.grid_placement_data = []
        self.gradient_source = "Custom Word List"; self.selected_ascii_gradient = ASCII_GRADIENTS[DEFAULT_GRADIENT_NAME]
        self.threshold_enabled = False; self.threshold_value = DEFAULT_THRESHOLD
        self.brightness_value = DEFAULT_BRIGHTNESS; self.contrast_value = DEFAULT_CONTRAST
        self.saturation_value = DEFAULT_SATURATION; self.hue_value = DEFAULT_HUE
        self.grayscale_value = 0; self.invert_enabled = False
        self.sharpness_value = DEFAULT_SHARPNESS; self.edge_detect_enabled = False

        # --- UI Setup ---
        self._init_ui()
        self.update_selected_font(self.font_combo.currentFont()) # Initialize font name
        self.show()

    def _init_ui(self):
        """Initializes the user interface components."""
        central_widget = QWidget(); self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget); main_layout.setContentsMargins(5, 5, 5, 5); main_layout.setSpacing(10)
        left_panel = self._create_left_panel(); main_layout.addWidget(left_panel)
        right_panel = self._create_right_panel(); main_layout.addWidget(right_panel)
        main_layout.setStretchFactor(left_panel, 1); main_layout.setStretchFactor(right_panel, 4)

    def _create_left_panel(self):
        """Creates the left settings panel widget."""
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.Shape.StyledPanel); left_panel.setFixedWidth(350)
        left_palette = left_panel.palette(); left_palette.setColor(QPalette.ColorRole.Window, QColor(230, 230, 230))
        left_panel.setAutoFillBackground(True); left_panel.setPalette(left_palette)
        left_layout = QVBoxLayout(left_panel); left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Image Pre-processing Group ---
        image_group = QGroupBox("Image Pre-processing")
        image_layout = QVBoxLayout()
        self.import_button = QPushButton("Import Image"); self.import_button.clicked.connect(self.open_image_dialog)
        image_layout.addWidget(self.import_button)
        # Sliders using helper function
        self.brightness_label, self.brightness_slider = create_labeled_slider("Brightness", 0, 200, self.brightness_value, image_layout, self.trigger_processing_and_render, "Adjust brightness (100=original)")
        self.contrast_label, self.contrast_slider = create_labeled_slider("Contrast", 0, 200, self.contrast_value, image_layout, self.trigger_processing_and_render, "Adjust contrast (100=original)")
        self.saturation_label, self.saturation_slider = create_labeled_slider("Saturation", 0, 200, self.saturation_value, image_layout, self.trigger_processing_and_render, "Adjust color saturation (100=original)")
        self.grayscale_label, self.grayscale_slider = create_labeled_slider("Grayscale", 0, 100, self.grayscale_value, image_layout, self.trigger_processing_and_render, "Convert to grayscale (100=full)")
        # Toggles and Effects
        self.invert_checkbox = QCheckBox("Invert Colors"); self.invert_checkbox.setChecked(self.invert_enabled); self.invert_checkbox.stateChanged.connect(self.update_invert_enabled)
        image_layout.addWidget(self.invert_checkbox)
        self.sharpness_label, self.sharpness_slider = create_labeled_slider("Sharpness", 0, 300, self.sharpness_value, image_layout, self.trigger_processing_and_render, "Adjust sharpness (100=original)")
        # Threshold Controls
        threshold_hbox = QHBoxLayout(); self.threshold_checkbox = QCheckBox("Enable Threshold"); self.threshold_checkbox.setChecked(self.threshold_enabled); self.threshold_checkbox.stateChanged.connect(self.update_threshold_enabled)
        threshold_hbox.addWidget(self.threshold_checkbox); self.threshold_value_label = QLabel(f"Value: {self.threshold_value}"); self.threshold_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        threshold_hbox.addWidget(self.threshold_value_label); image_layout.addLayout(threshold_hbox)
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal); self.threshold_slider.setRange(0, 255); self.threshold_slider.setValue(self.threshold_value); self.threshold_slider.valueChanged.connect(self.update_threshold_value); self.threshold_slider.setEnabled(self.threshold_enabled)
        image_layout.addWidget(self.threshold_slider)
        # Edge Detection Controls
        edge_hbox = QHBoxLayout(); self.edge_checkbox = QCheckBox("Enable Edge Detect"); self.edge_checkbox.setChecked(self.edge_detect_enabled); self.edge_checkbox.stateChanged.connect(self.update_edge_detect_enabled)
        edge_hbox.addWidget(self.edge_checkbox); image_layout.addLayout(edge_hbox)
        image_group.setLayout(image_layout); left_layout.addWidget(image_group)

        # --- Word/Gradient Source Group ---
        source_group = QGroupBox("Gradient Source"); source_layout = QVBoxLayout()
        self.gradient_source_combo = QComboBox(); self.gradient_source_combo.addItem("Custom Word List"); self.gradient_source_combo.addItems(ASCII_GRADIENTS.keys()); self.gradient_source_combo.currentTextChanged.connect(self.update_gradient_source)
        source_layout.addWidget(self.gradient_source_combo); self.word_list_label = QLabel("Custom Words:"); source_layout.addWidget(self.word_list_label)
        self.word_list_edit = QTextEdit(); self.word_list_edit.setPlaceholderText("Enter words here..."); self.word_list_edit.setFixedHeight(80); self.word_list_edit.textChanged.connect(self.parse_word_list_from_text)
        source_layout.addWidget(self.word_list_edit); self.load_words_button = QPushButton("Load Words from File (.txt)"); self.load_words_button.clicked.connect(self.load_words_from_file)
        source_layout.addWidget(self.load_words_button); source_group.setLayout(source_layout); left_layout.addWidget(source_group)

        # --- Generation & Styling Group ---
        gen_style_group = QGroupBox("Generation & Styling"); gen_style_layout = QVBoxLayout()
        font_label = QLabel("Font:"); gen_style_layout.addWidget(font_label); self.font_combo = QFontComboBox(); self.font_combo.currentFontChanged.connect(self.update_selected_font); gen_style_layout.addWidget(self.font_combo)
        size_label = QLabel("Font Size:"); gen_style_layout.addWidget(size_label); self.font_size_spin = QSpinBox(); self.font_size_spin.setRange(6, 72); self.font_size_spin.setValue(self.selected_font_size); self.font_size_spin.valueChanged.connect(self.update_font_size); gen_style_layout.addWidget(self.font_size_spin)
        density_label = QLabel("Density:"); gen_style_layout.addWidget(density_label)
        self.density_spin = QSpinBox(); self.density_spin.setRange(1, MAX_DENSITY); self.density_spin.setValue(self.word_density); self.density_spin.setToolTip(f"Approx items per 100x100 area (Max: {MAX_DENSITY})"); self.density_spin.valueChanged.connect(self.update_density)
        gen_style_layout.addWidget(self.density_spin)
        self.import_font_button = QPushButton("Import Custom Font (.ttf/.otf)"); self.import_font_button.setEnabled(False); self.import_font_button.setToolTip("Feature not yet implemented"); gen_style_layout.addWidget(self.import_font_button)
        gen_style_group.setLayout(gen_style_layout); left_layout.addWidget(gen_style_group)

        left_layout.addStretch()
        self._update_word_list_controls_state()
        return left_panel

    def _create_right_panel(self):
        """Creates the right panel containing the three preview areas."""
        right_panel = QFrame(); right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        grid_layout = QGridLayout(right_panel); grid_layout.setSpacing(10)
        self.original_preview = PreviewLabel("Input Image") # Renamed Label
        self.processed_preview = PreviewLabel("Processed Image") # Renamed Label
        self.render_preview = PreviewLabel("Output Image") # Renamed Label
        grid_layout.addWidget(QLabel("<b>Input Image:</b>"), 0, 0, Qt.AlignmentFlag.AlignCenter) # Renamed Label Text
        grid_layout.addWidget(self.original_preview, 1, 0)
        grid_layout.addWidget(QLabel("<b>Processed Image:</b>"), 0, 1, Qt.AlignmentFlag.AlignCenter) # Renamed Label Text
        grid_layout.addWidget(self.processed_preview, 1, 1)
        grid_layout.addWidget(QLabel("<b>Output Image:</b>"), 0, 2, Qt.AlignmentFlag.AlignCenter) # Renamed Label Text
        grid_layout.addWidget(self.render_preview, 1, 2)
        grid_layout.setColumnStretch(0, 1); grid_layout.setColumnStretch(1, 1); grid_layout.setColumnStretch(2, 1); grid_layout.setRowStretch(1, 1)
        return right_panel

    # --- Slots and Event Handlers ---

    def _update_single_preview(self, label_widget, image_to_display):
        """Helper to update a specific PreviewLabel widget."""
        if image_to_display:
            try:
                display_image = image_to_display
                # Convert specific modes if needed for display, but keep L for processed
                temp_display_image = display_image
                if temp_display_image.mode not in ('RGB', 'L', 'RGBA'):
                    temp_display_image = temp_display_image.convert('RGB')
                # Ensure RGBA for QPixmap conversion
                if temp_display_image.mode != 'RGBA':
                    temp_display_image = temp_display_image.convert('RGBA')

                q_image = ImageQt(temp_display_image); pixmap = QPixmap.fromImage(q_image)
                label_widget.setPixmap(pixmap)
            except Exception as e: print(f"Error updating preview: {e}"); label_widget.setText(f"Error:\n{e}"); label_widget.setPixmap(QPixmap())
        else: label_widget.clear(); label_widget.setText("N/A")

    @Slot()
    def open_image_dialog(self):
        """Opens dialog, loads image, updates original preview, triggers processing & render."""
        file_dialog = QFileDialog(self); file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp)"); file_dialog.setViewMode(QFileDialog.ViewMode.Detail); file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                image_path = file_paths[0]; print(f"Selected image: {image_path}")
                try:
                    self.original_image = Image.open(image_path)
                    self._update_single_preview(self.original_preview, self.original_image)
                    self.trigger_processing_and_render()
                    print("Image loaded.")
                except Exception as e:
                    print(f"Error loading image: {e}")
                    self.original_image = None; self.processed_image = None; self.rendered_image = None
                    self.original_preview.clear(); self.processed_preview.clear(); self.render_preview.clear()
                    self.original_preview.setText(f"Error:\n{e}")

    # --- Image Processing Slots ---
    @Slot(int)
    def update_threshold_enabled(self, state):
        self.threshold_enabled = (state == Qt.CheckState.Checked.value)
        self.threshold_slider.setEnabled(self.threshold_enabled)
        print(f"Thresholding {'enabled' if self.threshold_enabled else 'disabled'}")
        if self.threshold_enabled and self.edge_detect_enabled: self.edge_checkbox.setChecked(False)
        else: self.trigger_processing_and_render()

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
        if self.edge_detect_enabled and self.threshold_enabled: self.threshold_checkbox.setChecked(False)
        else: self.trigger_processing_and_render()

    @Slot()
    def trigger_processing_and_render(self):
        """Slot connected to most processing sliders/checkboxes. Updates state and triggers processing/render."""
        # Update internal state from sliders/checkboxes first
        self.brightness_value = self.brightness_slider.value()
        self.contrast_value = self.contrast_slider.value()
        self.saturation_value = self.saturation_slider.value()
        self.grayscale_value = self.grayscale_slider.value()
        self.sharpness_value = self.sharpness_slider.value()
        # Checkbox states are updated directly via their specific slots

        # Call the external processing function
        processed_img = apply_image_processing( # Renamed result variable
            self.original_image,
            self.brightness_value,
            self.contrast_value,
            self.saturation_value,
            self.grayscale_value,
            self.invert_enabled,
            self.sharpness_value,
            self.threshold_enabled,
            self.threshold_value,
            self.edge_detect_enabled
        )

        # Store the single processed image
        self.processed_image = processed_img

        # Update the middle preview ("Processed Image") with the result
        self._update_single_preview(self.processed_preview, self.processed_image)

        # If processing was successful, trigger the final render
        if self.processed_image is not None:
            self.trigger_render()
        else:
            # Clear render preview if processing failed
            self.render_preview.clear()
            self.render_preview.setText("Processing Error")


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
        if self.gradient_source == "Custom Word List":
            self._update_brightness_map_state()
            self.trigger_render()

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
        self._update_word_list_controls_state()
        self._update_brightness_map_state()
        self.trigger_render()

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
        """Returns the list of items (words or chars) to use for the gradient."""
        if self.gradient_source == "Custom Word List": return self.word_list
        else: return list(self.selected_ascii_gradient)

    def _update_brightness_map_state(self):
        """Updates the internal brightness map state using the render_engine function."""
        gradient_items = self._get_current_gradient_list()
        self.brightness_map = update_brightness_map(gradient_items, self.gradient_source)

    def trigger_render(self):
        """Coordinates the steps needed generate and render the WordWeave. Assumes processing is done."""
        print("--- Triggering Render ---")
        self.rendered_image = None
        self.render_preview.clear(); self.render_preview.setText("Rendering...")
        QApplication.processEvents()

        # 1. Ensure processed_image exists (created by _apply_image_processing)
        if not self.processed_image:
             print("Render cancelled: No processed image available."); self.render_preview.setText("No Processed Image"); return

        # 2. Ensure brightness map is updated
        self._update_brightness_map_state()
        if not self.brightness_map: print("Render cancelled: Brightness map error."); self.render_preview.setText("No Map"); return

        # 3. Generate placement data using the processed_image
        self.grid_placement_data = generate_grid_placement(
            self.processed_image, # Use the single processed image
            self.brightness_map,
            self.word_density
        )

        # 4. Render the grid
        self.rendered_image = render_word_grid(
            self.original_image.size if self.original_image else (100,100),
            self.grid_placement_data,
            self.selected_font_name,
            self.selected_font_size
        )

        # 5. Update the "Output Image" preview
        if self.rendered_image:
            self._update_single_preview(self.render_preview, self.rendered_image)
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