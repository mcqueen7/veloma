from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QGroupBox, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage, QFont, QCloseEvent
import cv2
import numpy as np
from typing import Optional, Callable
import time


class VelomaUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.window_width = 1400
        self.window_height = 900
        self.camera_width = 800
        self.camera_height = 600

        # Callbacks
        self.on_start_callback = None
        self.on_stop_callback = None
        self.on_settings_change_callback = None

        # UI state
        self.current_pitch = 60.0
        self.current_volume = 0.0
        self.hands_detected = 0
        self.frame_count = 0

        # UI elements
        self.camera_label: Optional[QLabel] = None
        self.camera_status_label: Optional[QLabel] = None
        self.hands_count_label: Optional[QLabel] = None
        self.frames_count_label: Optional[QLabel] = None
        self.last_update_label: Optional[QLabel] = None
        self.pitch_slider: Optional[QSlider] = None
        self.volume_slider: Optional[QSlider] = None
        self.pitch_min_slider: Optional[QSlider] = None
        self.pitch_max_slider: Optional[QSlider] = None
        self.smoothing_slider: Optional[QSlider] = None
        self.pitch_value_label: Optional[QLabel] = None
        self.volume_value_label: Optional[QLabel] = None
        self.pitch_min_value_label: Optional[QLabel] = None
        self.pitch_max_value_label: Optional[QLabel] = None
        self.smoothing_value_label: Optional[QLabel] = None

        self.setup()

    def setup(self):
        """Setup the main window and UI components."""
        self.setWindowTitle('Veloma - Virtual Theremin')
        self.setGeometry(100, 100, self.window_width, self.window_height)
        self.setMinimumSize(1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self._create_header(main_layout)
        self._create_control_buttons(main_layout)
        self._create_main_content(main_layout)

        self._setup_camera_display()


    def _create_header(self, parent_layout):
        """Create the header section."""
        title_label = QLabel("Veloma - Virtual Theremin")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #64C8FF; margin: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        parent_layout.addWidget(title_label)

    def _create_control_buttons(self, parent_layout):
        """Create control buttons section."""
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 5, 0, 10)

        exit_button = QPushButton("Exit")
        exit_button.setFixedSize(100, 40)
        exit_button.clicked.connect(self._on_exit_clicked)
        exit_button.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; }")

        button_layout.addStretch()
        button_layout.addWidget(exit_button)

        parent_layout.addLayout(button_layout)

    def _create_main_content(self, parent_layout):
        """Create the main content area."""
        content_layout = QHBoxLayout()

        # Left panel - Camera preview
        self._create_camera_panel(content_layout)

        # Right panel - Audio controls
        self._create_audio_panel(content_layout)

        parent_layout.addLayout(content_layout)

    def _create_camera_panel(self, parent_layout):
        """Create camera preview panel."""
        camera_group = QGroupBox("Camera Preview")
        camera_layout = QVBoxLayout(camera_group)

        # Camera display - make it larger
        self.camera_label = QLabel()
        self.camera_label.setFixedSize(self.camera_width, self.camera_height)
        self.camera_label.setStyleSheet("border: 2px solid #ccc; background-color: #000;")
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        camera_layout.addWidget(self.camera_label)

        camera_layout.addStretch()
        parent_layout.addWidget(camera_group)

    def _create_audio_panel(self, parent_layout):
        """Create audio control panel."""
        audio_group = QGroupBox("Audio Control")
        audio_layout = QVBoxLayout(audio_group)

        # Current parameters section
        params_group = QGroupBox("Current Parameters")
        params_layout = QGridLayout(params_group)

        # Pitch display
        params_layout.addWidget(QLabel("Pitch (MIDI):"), 0, 0)
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setRange(40, 80)
        self.pitch_slider.setValue(60)
        self.pitch_slider.setEnabled(False)
        self.pitch_value_label = QLabel("60.0")
        params_layout.addWidget(self.pitch_slider, 0, 1)
        params_layout.addWidget(self.pitch_value_label, 0, 2)

        # Volume display
        params_layout.addWidget(QLabel("Volume:"), 1, 0)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(0)
        self.volume_slider.setEnabled(False)
        self.volume_value_label = QLabel("0.0")
        params_layout.addWidget(self.volume_slider, 1, 1)
        params_layout.addWidget(self.volume_value_label, 1, 2)

        audio_layout.addWidget(params_group)

        # Settings section
        settings_group = QGroupBox("Settings")
        settings_layout = QGridLayout(settings_group)

        # Min pitch setting
        settings_layout.addWidget(QLabel("Min Pitch:"), 0, 0)
        self.pitch_min_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_min_slider.setRange(20, 60)
        self.pitch_min_slider.setValue(40)
        self.pitch_min_slider.valueChanged.connect(self._on_settings_changed)
        self.pitch_min_value_label = QLabel("40.0")
        settings_layout.addWidget(self.pitch_min_slider, 0, 1)
        settings_layout.addWidget(self.pitch_min_value_label, 0, 2)

        # Max pitch setting
        settings_layout.addWidget(QLabel("Max Pitch:"), 1, 0)
        self.pitch_max_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_max_slider.setRange(60, 100)
        self.pitch_max_slider.setValue(80)
        self.pitch_max_slider.valueChanged.connect(self._on_settings_changed)
        self.pitch_max_value_label = QLabel("80.0")
        settings_layout.addWidget(self.pitch_max_slider, 1, 1)
        settings_layout.addWidget(self.pitch_max_value_label, 1, 2)

        # Smoothing setting
        settings_layout.addWidget(QLabel("Smoothing:"), 2, 0)
        self.smoothing_slider = QSlider(Qt.Orientation.Horizontal)
        self.smoothing_slider.setRange(1, 50)
        self.smoothing_slider.setValue(10)  # 0.1 * 100
        self.smoothing_slider.valueChanged.connect(self._on_settings_changed)
        self.smoothing_value_label = QLabel("0.10")
        settings_layout.addWidget(self.smoothing_slider, 2, 1)
        settings_layout.addWidget(self.smoothing_value_label, 2, 2)

        audio_layout.addWidget(settings_group)

        # Instructions section
        instructions_group = QGroupBox("Instructions")
        instructions_layout = QVBoxLayout(instructions_group)

        instructions = [
            "• Application starts automatically",
            "• Move your hand up/down to control pitch",
            "• Move your hand left/right to control volume",
            "• Use two hands for advanced control"
        ]

        for instruction in instructions:
            label = QLabel(instruction)
            label.setWordWrap(True)
            instructions_layout.addWidget(label)

        audio_layout.addWidget(instructions_group)

        # Status section
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)

        self.camera_status_label = QLabel("Status: Running")
        self.hands_count_label = QLabel("Hands Detected: 0")
        self.frames_count_label = QLabel("Frames Processed: 0")
        self.last_update_label = QLabel("Last Update: Never")

        status_labels = [self.camera_status_label, self.hands_count_label,
                        self.frames_count_label, self.last_update_label]

        for label in status_labels:
            label.setStyleSheet("margin: 2px; font-family: monospace;")
            status_layout.addWidget(label)

        audio_layout.addWidget(status_group)
        audio_layout.addStretch()

        parent_layout.addWidget(audio_group)

    def _setup_camera_display(self):
        """Setup initial camera display with test pattern."""
        # Create test pattern
        test_image = np.zeros((self.camera_height, self.camera_width, 3), dtype=np.uint8)

        # Create checkerboard pattern
        for y in range(self.camera_height):
            for x in range(self.camera_width):
                if (x // 32 + y // 32) % 2:
                    test_image[y, x] = [100, 100, 100]  # Gray
                else:
                    test_image[y, x] = [50, 50, 50]   # Darker gray

        # Add border
        test_image[0:5, :] = [0, 255, 0]  # Green border
        test_image[-5:, :] = [0, 255, 0]
        test_image[:, 0:5] = [0, 255, 0]
        test_image[:, -5:] = [0, 255, 0]

        self._display_image(test_image)

    def _display_image(self, image):
        """Display an image in the camera label."""
        try:
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(self.camera_width, self.camera_height, Qt.AspectRatioMode.KeepAspectRatio)
            if self.camera_label:
                self.camera_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Error displaying image: {e}")
            self._show_error_pattern()

    def _show_error_pattern(self):
        """Show error pattern when image display fails."""
        error_image = np.zeros((self.camera_height, self.camera_width, 3), dtype=np.uint8)
        error_image[:, :] = [255, 0, 0]  # Red background

        # Add error stripes
        for y in range(100, 150):
            for x in range(100, 400):
                if (x + y) % 4 == 0:
                    error_image[y, x] = [255, 255, 255]  # White stripes

        self._display_image(error_image)

    def start_application(self):
        if self.on_start_callback:
            try:
                result = self.on_start_callback()
                print(f"Auto-start result: {result}")
            except Exception as e:
                print(f"Auto-start failed: {e}")

    def _on_exit_clicked(self):
        """Handle exit button click."""
        self.stop()

    def _on_settings_changed(self):
        """Handle settings slider changes."""
        # Update slider value labels
        if self.pitch_min_value_label and self.pitch_min_slider:
            self.pitch_min_value_label.setText(f"{self.pitch_min_slider.value()}.0")
        if self.pitch_max_value_label and self.pitch_max_slider:
            self.pitch_max_value_label.setText(f"{self.pitch_max_slider.value()}.0")
        if self.smoothing_value_label and self.smoothing_slider:
            self.smoothing_value_label.setText(f"{self.smoothing_slider.value() / 100:.2f}")

        if self.on_settings_change_callback and self.pitch_min_slider and self.pitch_max_slider and self.smoothing_slider:
            settings = {
                'pitch_range_min': float(self.pitch_min_slider.value()),
                'pitch_range_max': float(self.pitch_max_slider.value()),
                'smoothing': self.smoothing_slider.value() / 100.0
            }
            self.on_settings_change_callback(settings)

    def update_camera_frame(self, frame: Optional[np.ndarray]):
        """Update the camera preview with new frame."""
        if frame is None:
            return

        try:
            # Resize frame to match display size
            resized_frame = cv2.resize(frame, (self.camera_width, self.camera_height))

            # Convert BGR to RGB (OpenCV uses BGR by default)
            rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

            self._display_image(rgb_frame)

            self.frame_count += 1

            # Update UI status every n frames
            n = 30
            if self.frame_count % n == 0:
                current_time = time.strftime("%H:%M:%S")
                if self.frames_count_label:
                    self.frames_count_label.setText(f"Frames Processed: {self.frame_count}")
                if self.last_update_label:
                    self.last_update_label.setText(f"Last Update: {current_time}")

        except Exception as e:
            print(f"Camera frame update error: {e}")
            self._show_error_pattern()

    def update_audio_params(self, pitch: float, volume: float):
        """Update audio parameter displays."""
        self.current_pitch = pitch
        self.current_volume = volume

        if self.pitch_slider:
            self.pitch_slider.setValue(int(pitch))
        if self.pitch_value_label:
            self.pitch_value_label.setText(f"{pitch:.1f}")

        if self.volume_slider:
            self.volume_slider.setValue(int(volume * 100))
        if self.volume_value_label:
            self.volume_value_label.setText(f"{volume:.2f}")

    def update_hands_count(self, count: int):
        """Update hands detected count."""
        self.hands_detected = count
        if self.hands_count_label:
            self.hands_count_label.setText(f"Hands Detected: {count}")

    def set_callbacks(self,
                     on_start: Optional[Callable] = None,
                     on_stop: Optional[Callable] = None,
                     on_settings_change: Optional[Callable] = None):
        """Set callback functions for UI events."""
        self.on_start_callback = on_start
        self.on_stop_callback = on_stop
        self.on_settings_change_callback = on_settings_change

    def run(self):
        """Run the UI main loop."""
        self.is_running = True
        self.show()

        # Auto-start the application after UI is shown
        QTimer.singleShot(100, self.start_application)

    def stop(self):
        """Stop the UI."""
        self.is_running = False
        self.close()
        QApplication.quit()

    def cleanup(self):
        """Clean up resources."""
        self.stop()

    def closeEvent(self, a0: Optional[QCloseEvent]):
        """Handle window close event."""
        self.stop()
        if a0:
            a0.accept()
