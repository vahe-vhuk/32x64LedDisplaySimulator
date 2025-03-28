import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QPushButton,
    QSizePolicy, QFileDialog, QMenu, QDialog, QFormLayout,
    QSpinBox, QComboBox, QDialogButtonBox, QLabel, QFrame,
    QColorDialog, QPlainTextEdit
)
from PyQt6.QtGui import QAction, QPainter, QColor, QFont, QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFontDialog


class ExportSettingsDialog(QDialog):
    def __init__(self, max_rows, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Settings")
        layout = QFormLayout(self)

        self.start_spin = QSpinBox(self)
        self.start_spin.setRange(0, max_rows - 1)
        self.start_spin.setValue(0)
        layout.addRow("Start Row:", self.start_spin)

        self.end_spin = QSpinBox(self)
        self.end_spin.setRange(0, max_rows - 1)
        self.end_spin.setValue(max_rows - 1)
        layout.addRow("End Row:", self.end_spin)

        self.format_combo = QComboBox(self)
        self.format_combo.addItems(["Plain", "Formatted"])
        index = self.format_combo.findText("Formatted")
        if index >= 0:
            self.format_combo.setCurrentIndex(index)
        layout.addRow("Export Format:", self.format_combo)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def getValues(self):
        return (self.start_spin.value(),
                self.end_spin.value(),
                self.format_combo.currentText())


class CircleButton(QPushButton):
    def __init__(self, size=15, default_color=QColor("green"), on_toggle=None, main_window=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # Each cell starts uncolored (black).
        self.colored = False
        self.cell_color = None
        self.default_color = default_color
        self.on_toggle = on_toggle
        self.main_window = main_window
        self.setStyleSheet("border: none;")

    def mousePressEvent(self, event):
        # If P key is held down (eyedrop mode), sample the cell's color.
        if self.main_window.eyedrop_mode:
            # Do not change the cell's state; just sample its color.
            self.main_window.record_undo()
            # If the cell is colored, use its color; otherwise, use black.
            sample_color = self.cell_color if self.colored and self.cell_color is not None else QColor("black")
            self.main_window.paint_color = sample_color
            # Optionally, enable global paint mode so subsequent clicks paint with this color.
            self.main_window.paint_mode = True
            # Exit eyedrop mode after one sample.
            self.main_window.eyedrop_mode = False
            return
        # Ctrl+Click still opens the color dialog for that cell.
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            chosen_color = QColorDialog.getColor(self.default_color, self, "Select Color for This Cell")
            if chosen_color.isValid():
                self.main_window.record_undo()
                self.colored = True
                self.cell_color = chosen_color
            self.update()
            return
        # If global paint mode is active (set via Ctrl+W), paint with that color.
        elif self.main_window.paint_mode:
            self.main_window.record_undo()
            self.colored = True
            self.cell_color = self.main_window.paint_color
            self.update()
            return
        else:
            if self.on_toggle:
                self.on_toggle()
            self.toggle_color()
            super().mousePressEvent(event)

    def toggle_color(self):
        if not self.colored:
            self.colored = True
            self.cell_color = self.default_color
        else:
            self.colored = False
            self.cell_color = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        margin = 2
        diameter = min(self.width(), self.height()) - 2 * margin
        color = self.cell_color if (self.colored and self.cell_color is not None) else QColor("black")
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(margin, margin, diameter, diameter)


class TextOverlayDialog(QDialog):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setWindowTitle("Text Overlay Settings")

        layout = QFormLayout(self)

        self.text_edit = QPlainTextEdit(self)
        self.text_edit.setPlainText("Hello, 世界")
        layout.addRow("Text:", self.text_edit)

        self.font_size_spin = QSpinBox(self)
        self.font_size_spin.setRange(1, 32)
        self.font_size_spin.setValue(8)
        layout.addRow("Font Size (cells):", self.font_size_spin)

        self.line_spacing_spin = QSpinBox(self)
        self.line_spacing_spin.setRange(0, 10)
        self.line_spacing_spin.setValue(1)
        layout.addRow("Line Spacing (rows):", self.line_spacing_spin)

        self.empty_cols_spin = QSpinBox(self)
        self.empty_cols_spin.setRange(0, 10)
        self.empty_cols_spin.setValue(1)
        layout.addRow("Empty Cols (cols):", self.empty_cols_spin)

        self.color_button = QPushButton("Select Text Color", self)
        self.text_color = QColor("red")
        self.color_button.setStyleSheet("background-color: " + self.text_color.name())
        layout.addRow("Text Color:", self.color_button)

        # NEW: Font selection
        self.font_button = QPushButton("Select Font", self)
        self.selected_font = QFont("Monospace")  # default font
        self.font_button.setText(self.selected_font.family())
        layout.addRow("Font:", self.font_button)

        # Connect signals for real-time updates.
        self.text_edit.textChanged.connect(self.update_overlay)
        self.font_size_spin.valueChanged.connect(self.update_overlay)
        self.line_spacing_spin.valueChanged.connect(self.update_overlay)
        self.empty_cols_spin.valueChanged.connect(self.update_overlay)
        self.color_button.clicked.connect(self.choose_color)
        self.font_button.clicked.connect(self.choose_font)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                      QDialogButtonBox.StandardButton.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.update_overlay()

    def choose_color(self):
        chosen = QColorDialog.getColor(self.text_color, self, "Select Text Color")
        if chosen.isValid():
            self.text_color = chosen
            self.color_button.setStyleSheet("background-color: " + self.text_color.name())
            self.update_overlay()

    def choose_font(self):
        font, ok = QFontDialog.getFont(self.selected_font, self, "Select Font")
        if ok:
            self.selected_font = font
            self.font_button.setText(self.selected_font.family())
            self.update_overlay()

    def update_overlay(self):
        text = self.text_edit.toPlainText()
        font_size = self.font_size_spin.value()
        line_spacing = self.line_spacing_spin.value()
        empty_cols = self.empty_cols_spin.value()
        text_color = self.text_color
        font_family = self.selected_font.family()
        self.main_window.apply_text_overlay(text, font_size, line_spacing, empty_cols, text_color, font_family)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grid with Cell Painting, Text Overlay, and Eyedropper (P)")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.undo_stack = []
        self.redo_stack = []
        self.default_color = QColor("green")
        self.paint_mode = False
        self.paint_color = None
        # New flag for eyedropper mode (activated by holding P)
        self.eyedrop_mode = False

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)
        grid_layout.setSpacing(0)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        self.num_rows = 32
        self.num_cols = 64
        cell_size = 15
        group_size = 8

        self.buttons = []
        for r in range(self.num_rows):
            row_label = QLabel(str(r), self)
            row_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row_label.setFixedWidth(20)
            grid_layout.addWidget(row_label, r, 0)
            row_buttons = []
            for c in range(self.num_cols):
                grid_col = 1 + c + (c // group_size)
                button = CircleButton(size=cell_size, default_color=self.default_color,
                                      on_toggle=self.record_undo, main_window=self)
                grid_layout.addWidget(button, r, grid_col)
                row_buttons.append(button)
            self.buttons.append(row_buttons)

        num_groups = self.num_cols // group_size
        for i in range(1, num_groups):
            sep_col = i * (group_size + 1)
            separator = QFrame(self)
            separator.setFrameShape(QFrame.Shape.VLine)
            separator.setLineWidth(1)
            separator.setFixedWidth(1)
            separator.setStyleSheet("background-color: #cccccc;")
            grid_layout.addWidget(separator, 0, sep_col, self.num_rows, 1)

        self.setup_menu()

    def setup_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        export_action = QAction("Export", self)
        export_action.setShortcut("Ctrl+S")
        export_action.triggered.connect(self.export_grid_state)
        file_menu.addAction(export_action)

        import_action = QAction("Import", self)
        import_action.setShortcut("Ctrl+O")
        import_action.triggered.connect(self.import_grid_state)
        file_menu.addAction(import_action)

        merge_import_action = QAction("Merge Import", self)
        merge_import_action.setShortcut("Ctrl+M")
        merge_import_action.triggered.connect(self.merge_import_grid_state)
        file_menu.addAction(merge_import_action)

        reset_action = QAction("Reset", self)
        reset_action.setShortcut("Ctrl+R")
        reset_action.triggered.connect(self.reset_grid)
        file_menu.addAction(reset_action)

        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo)
        file_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo)
        file_menu.addAction(redo_action)

    def set_all_colored_cells_color(self):
        """Opens a color dialog and then applies the chosen color to all colored cells."""
        chosen = QColorDialog.getColor(self.default_color, self, "Select new color for all colored cells")
        if not chosen.isValid():
            return
        self.record_undo()  # record state before changing colors
        for row in self.buttons:
            for btn in row:
                if btn.colored:
                    btn.cell_color = chosen
                    btn.update()

    def keyPressEvent(self, event):
        # Ctrl+I: open text overlay dialog.
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_I:
            self.open_text_overlay_dialog()
            return
        # Ctrl+W: choose a global paint color.
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_W:
            chosen = QColorDialog.getColor(self.default_color, self, "Select Paint Mode Color")
            if chosen.isValid():
                self.paint_color = chosen
                self.paint_mode = True
            return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_F:
            self.set_all_colored_cells_color()
            return
        # If user presses P, enable eyedrop mode.
        if event.key() == Qt.Key.Key_P:
            self.eyedrop_mode = True
            return
        # Escape: cancel global paint mode and eyedrop mode.
        if event.key() == Qt.Key.Key_Escape:
            self.paint_mode = False
            self.paint_color = None
            self.eyedrop_mode = False
            return
        # Shift+Arrow keys: shift cells.
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            if event.key() == Qt.Key.Key_Left:
                self.shift_grid("left")
            elif event.key() == Qt.Key.Key_Right:
                self.shift_grid("right")
            elif event.key() == Qt.Key.Key_Up:
                self.shift_grid("up")
            elif event.key() == Qt.Key.Key_Down:
                self.shift_grid("down")
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        # When P is released, exit eyedrop mode.
        if event.key() == Qt.Key.Key_P:
            self.eyedrop_mode = False
        else:
            super().keyReleaseEvent(event)

    def open_text_overlay_dialog(self):
        dialog = TextOverlayDialog(self, self)
        dialog.exec()

    def apply_text_overlay(self, text, font_size, line_spacing, empty_cols, text_color, font):
        """
        Render the given text into a QPixmap using Pillow, drawing each character individually.
        Letter spacing is controlled by the empty_cols parameter (interpreted as raw pixels).
        Then, update the grid state from the rendered image.

        :param text:         The multiline text to render.
        :param font_size:    The pixel height for the font.
        :param line_spacing: Extra vertical pixels between lines.
        :param empty_cols:   Extra horizontal pixels between characters.
        :param text_color:   A QColor for the text.
        """
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np

        # Grid dimensions (match your grid)
        width = self.num_cols
        height = self.num_rows

        # Create a new RGB image with a white background.
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        # Load the font – update the font_path to a valid pixel font (e.g., a Minecraft font).
        font_path=font
        # font_path = "/Users/picsartacademy/Downloads/pixel_unicode/Pixel-UniCode.ttf"  # <-- CHANGE THIS to your font file path.
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception as e:
            print(f"Error loading font at {font_path}: {e}")
            font = ImageFont.load_default()

        # Determine line height using getbbox.
        bbox = font.getbbox("Ay")
        line_height = bbox[3] - bbox[1]

        # Use empty_cols directly as extra pixel spacing between characters.
        letter_spacing = empty_cols  # interpret empty_cols as raw pixel spacing

        # Start drawing at the top.
        y = 0
        for line in text.splitlines():
            x = 0
            for ch in line:
                # Draw each character at (x, y) using the specified text color.
                draw.text((x, y), ch, fill=text_color.name(), font=font)
                # Measure the width of the character.
                ch_bbox = font.getbbox(ch)
                ch_width = ch_bbox[2] - ch_bbox[0]
                x += ch_width + letter_spacing
                if x >= width:
                    break
            y += line_height + line_spacing
            if y >= height:
                break

        # Convert the rendered image to a NumPy array.
        arr = np.array(image)
        new_state = []
        # For each pixel, if it is not white then mark the cell as "on"
        for row in range(height):
            row_state = []
            for col in range(width):
                pixel = arr[row, col]  # RGB tuple
                brightness = (int(pixel[0]) + int(pixel[1]) + int(pixel[2])) / 3.0
                if brightness < 240:  # threshold for "on"
                    row_state.append((True, (text_color.red(), text_color.green(), text_color.blue())))
                else:
                    row_state.append((False, (0, 0, 0)))
            new_state.append(row_state)

        self.record_undo()
        self.set_grid_state(new_state)

    def get_grid_state(self):
        state = []
        for row in self.buttons:
            row_state = []
            for btn in row:
                if btn.colored and btn.cell_color is not None:
                    rgb = (btn.cell_color.red(), btn.cell_color.green(), btn.cell_color.blue())
                    row_state.append((True, rgb))
                else:
                    row_state.append((False, (0, 0, 0)))
            state.append(row_state)
        return state

    def set_grid_state(self, state):
        for r, row in enumerate(state):
            for c, cell_state in enumerate(row):
                if r < len(self.buttons) and c < len(self.buttons[r]):
                    btn = self.buttons[r][c]
                    colored, rgb = cell_state
                    btn.colored = colored
                    if colored:
                        btn.cell_color = QColor(*rgb)
                    else:
                        btn.cell_color = None
                    btn.update()

    def record_undo(self):
        current_state = self.get_grid_state()
        self.undo_stack.append(current_state)
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            current_state = self.get_grid_state()
            self.redo_stack.append(current_state)
            previous_state = self.undo_stack.pop()
            self.set_grid_state(previous_state)

    def redo(self):
        if self.redo_stack:
            current_state = self.get_grid_state()
            self.undo_stack.append(current_state)
            next_state = self.redo_stack.pop()
            self.set_grid_state(next_state)

    def shift_grid(self, direction):
        self.record_undo()
        rows = self.num_rows
        cols = self.num_cols
        new_state = [[(False, (0, 0, 0)) for _ in range(cols)] for _ in range(rows)]
        curr_state = self.get_grid_state()
        for r in range(rows):
            for c in range(cols):
                if curr_state[r][c][0]:
                    if direction == "left":
                        new_c = c - 1
                        if new_c >= 0:
                            new_state[r][new_c] = curr_state[r][c]
                    elif direction == "right":
                        new_c = c + 1
                        if new_c < cols:
                            new_state[r][new_c] = curr_state[r][c]
                    elif direction == "up":
                        new_r = r - 1
                        if new_r >= 0:
                            new_state[new_r][c] = curr_state[r][c]
                    elif direction == "down":
                        new_r = r + 1
                        if new_r < rows:
                            new_state[new_r][c] = curr_state[r][c]
        self.set_grid_state(new_state)

    def export_grid_state(self):
        max_rows = self.num_rows
        dialog = ExportSettingsDialog(max_rows, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        start_row, end_row, mode = dialog.getValues()
        if start_row > end_row:
            start_row, end_row = end_row, start_row
        filename, _ = QFileDialog.getSaveFileName(self, "Export Grid State", "", "Text Files (*.txt)")
        if not filename:
            return
        try:
            with open(filename, "w") as f:
                for row in self.buttons[start_row:end_row + 1]:
                    if mode == "Plain":
                        line = " ".join("1" if btn.colored else "0" for btn in row)
                    else:
                        row_values = ["1" if btn.colored else "0" for btn in row]
                        groups = []
                        group_size = 8
                        for i in range(0, len(row_values), group_size):
                            group = "".join(row_values[i:i + group_size])
                            groups.append("2b" + group)
                        line = ", ".join(groups)
                    f.write(line + "\n")
                f.write("\n#colors\n")
                for row in self.buttons[start_row:end_row + 1]:
                    line_parts = []
                    for btn in row:
                        if btn.colored and btn.cell_color is not None:
                            r_val, g_val, b_val, _ = btn.cell_color.getRgb()
                            line_parts.append(f"{r_val},{g_val},{b_val}")
                        else:
                            line_parts.append("0,0,0")
                    f.write(" ".join(line_parts) + "\n")
        except Exception as e:
            print(f"Error exporting grid state: {e}")

    def import_grid_state(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Import Grid State", "", "Text Files (*.txt)")
        if not filename:
            return
        try:
            with open(filename, "r") as f:
                lines = [line.rstrip("\n") for line in f]
            if "#colors" in lines:
                index = lines.index("#colors")
                main_data = lines[:index]
                color_data = lines[index + 1:]
            else:
                main_data = lines
                color_data = []
            imported_state = []
            if main_data and main_data[0].startswith("2b"):
                for line in main_data:
                    groups = [grp.strip() for grp in line.split(",")]
                    row_str = ""
                    for grp in groups:
                        if grp.startswith("2b"):
                            row_str += grp[2:]
                    row_bool = [True if ch == "1" else False for ch in row_str]
                    imported_state.append(row_bool)
            else:
                for line in main_data:
                    row_bool = [True if val == "1" else False for val in line.split()]
                    imported_state.append(row_bool)
            self.record_undo()
            for r in range(min(len(imported_state), self.num_rows)):
                for c in range(min(len(imported_state[r]), self.num_cols)):
                    btn = self.buttons[r][c]
                    if imported_state[r][c]:
                        btn.colored = True
                        if color_data and r < len(color_data):
                            parts = color_data[r].split()
                            if c < len(parts):
                                rgb_parts = parts[c].split(",")
                                if len(rgb_parts) >= 3:
                                    r_val = int(rgb_parts[0])
                                    g_val = int(rgb_parts[1])
                                    b_val = int(rgb_parts[2])
                                    btn.cell_color = QColor(r_val, g_val, b_val)
                                else:
                                    btn.cell_color = self.default_color
                        else:
                            btn.cell_color = self.default_color
                    else:
                        btn.colored = False
                        btn.cell_color = None
                    btn.update()
        except Exception as e:
            print(f"Error importing grid state: {e}")

    def merge_import_grid_state(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Merge Import Grid State", "", "Text Files (*.txt)")
        if not filename:
            return
        try:
            with open(filename, "r") as f:
                lines = [line.rstrip("\n") for line in f]
            if "#colors" in lines:
                index = lines.index("#colors")
                main_data = lines[:index]
                color_data = lines[index + 1:]
            else:
                main_data = lines
                color_data = []
            imported_state = []
            if main_data and main_data[0].startswith("2b"):
                for line in main_data:
                    groups = [grp.strip() for grp in line.split(",")]
                    row_str = ""
                    for grp in groups:
                        if grp.startswith("2b"):
                            row_str += grp[2:]
                    row_bool = [True if ch == "1" else False for ch in row_str]
                    imported_state.append(row_bool)
            else:
                for line in main_data:
                    row_bool = [True if val == "1" else False for val in line.split()]
                    imported_state.append(row_bool)
            current_state = self.get_grid_state()
            new_state = []
            for r in range(min(len(current_state), len(imported_state))):
                new_row = []
                for c in range(min(len(current_state[r]), len(imported_state[r]))):
                    if imported_state[r][c]:
                        if color_data and r < len(color_data):
                            parts = color_data[r].split()
                            if c < len(parts):
                                rgb_parts = parts[c].split(",")
                                if len(rgb_parts) >= 3:
                                    r_val = int(rgb_parts[0])
                                    g_val = int(rgb_parts[1])
                                    b_val = int(rgb_parts[2])
                                    new_row.append((True, (r_val, g_val, b_val)))
                                else:
                                    new_row.append(current_state[r][c])
                            else:
                                new_row.append(current_state[r][c])
                        else:
                            new_row.append((True, (
                            self.default_color.red(), self.default_color.green(), self.default_color.blue())))
                    else:
                        new_row.append(current_state[r][c])
                new_state.append(new_row)
            self.record_undo()
            self.set_grid_state(new_state)
        except Exception as e:
            print(f"Error merging imported grid state: {e}")

    def reset_grid(self):
        self.record_undo()
        for row in self.buttons:
            for btn in row:
                btn.colored = False
                btn.cell_color = None
                btn.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
