import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QPushButton,
    QSizePolicy, QFileDialog, QMenu, QDialog, QFormLayout,
    QSpinBox, QComboBox, QDialogButtonBox, QLabel, QFrame,
    QColorDialog, QPlainTextEdit, QCheckBox, QDoubleSpinBox
)
from PyQt6.QtGui import QAction, QPainter, QColor, QFont, QPixmap
from PyQt6.QtCore import Qt

from PIL import Image, ImageDraw, ImageFont


class GridSizeDialog(QDialog):
    def __init__(self, current_rows, current_cols, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Grid Size")
        layout = QFormLayout(self)

        self.row_spin = QSpinBox(self)
        self.row_spin.setRange(1, 1000)
        self.row_spin.setValue(current_rows)
        layout.addRow("Rows:", self.row_spin)

        self.col_spin = QSpinBox(self)
        self.col_spin.setRange(1, 1000)
        self.col_spin.setValue(current_cols)
        layout.addRow("Columns:", self.col_spin)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def getValues(self):
        return self.row_spin.value(), self.col_spin.value()


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
        self.format_combo.addItems(["Plain", "Formatted", "Colored"])
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


class RowLabel(QLabel):
    def __init__(self, text, row_index, main_window, parent=None):
        super().__init__(text, parent)
        self.row_index = row_index
        self.main_window = main_window
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedWidth(20)
        self.setStyleSheet("")

    def mousePressEvent(self, event):
        if self.row_index in self.main_window.selected_rows:
            self.main_window.selected_rows = []
            self.main_window.last_selected_row = None
            self.main_window.update_row_label_styles()
        else:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.main_window.select_row(self.row_index, shift=True)
            else:
                self.main_window.select_row(self.row_index, shift=False)
        super().mousePressEvent(event)


class ColumnLabel(QLabel):
    def __init__(self, text, col_index, main_window, parent=None):
        super().__init__(text, parent)
        self.col_index = col_index
        self.main_window = main_window
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("border: 1px solid gray;")
        self.setFixedHeight(20)

    def mousePressEvent(self, event):
        if self.col_index in self.main_window.selected_columns:
            self.main_window.selected_columns = []
            self.main_window.last_selected_column = None
            self.main_window.update_column_label_styles()
        else:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.main_window.select_column(self.col_index, shift=True)
            else:
                self.main_window.select_column(self.col_index, shift=False)
        super().mousePressEvent(event)


class CircleButton(QPushButton):
    def __init__(self, size=15, default_color=QColor("green"), on_toggle=None, main_window=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.colored = False
        self.cell_color = None
        self.default_color = default_color
        self.on_toggle = on_toggle
        self.main_window = main_window
        self.setStyleSheet("border: none;")

    def mousePressEvent(self, event):
        if self.main_window.uncolor_mode:
            target_color = self.cell_color if (self.colored and self.cell_color is not None) else QColor("black")
            self.main_window.record_undo()
            self.main_window.uncolor_all_cells_with_color(target_color)
            self.main_window.uncolor_mode = False
            return

        if self.main_window.eyedrop_mode:
            self.main_window.record_undo()
            sample_color = self.cell_color if (self.colored and self.cell_color is not None) else QColor("black")
            self.main_window.paint_color = sample_color
            self.main_window.picked_color = sample_color
            self.main_window.paint_mode = True
            self.main_window.eyedrop_mode = False
            return

        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            chosen_color = QColorDialog.getColor(self.default_color, self, "Select Color for This Cell")
            if chosen_color.isValid():
                self.main_window.record_undo()
                self.colored = True
                self.cell_color = chosen_color
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
            self.cell_color = self.main_window.paint_color
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

        self.bold_checkbox = QCheckBox("Bold", self)
        layout.addRow("Bold:", self.bold_checkbox)

        self.italic_checkbox = QCheckBox("Italic", self)
        layout.addRow("Italic:", self.italic_checkbox)

        self.font_combo = QComboBox(self)
        self.font_combo.addItems(["Arial", "Times New Roman", "Courier New"])
        layout.addRow("Font Family:", self.font_combo)

        self.font_size_spin = QSpinBox(self)
        self.font_size_spin.setRange(1, 200)
        self.font_size_spin.setValue(20)
        layout.addRow("Font Size:", self.font_size_spin)

        self.resize_spin = QDoubleSpinBox(self)
        self.resize_spin.setRange(0.1, 5.0)
        self.resize_spin.setSingleStep(0.1)
        self.resize_spin.setValue(1.0)
        layout.addRow("Image Resizing Factor:", self.resize_spin)

        self.text_color_button = QPushButton("Select Text Color", self)
        self.text_color = QColor("red")
        self.text_color_button.setStyleSheet("background-color: " + self.text_color.name())
        layout.addRow("Text Color:", self.text_color_button)

        self.text_edit.textChanged.connect(self.update_overlay)
        self.bold_checkbox.toggled.connect(self.update_overlay)
        self.italic_checkbox.toggled.connect(self.update_overlay)
        self.font_combo.currentIndexChanged.connect(self.update_overlay)
        self.font_size_spin.valueChanged.connect(self.update_overlay)
        self.resize_spin.valueChanged.connect(self.update_overlay)
        self.text_color_button.clicked.connect(self.choose_color)

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
            self.text_color_button.setStyleSheet("background-color: " + self.text_color.name())
            self.update_overlay()

    def update_overlay(self):
        self.main_window.apply_text_overlay(
            self.text_edit.toPlainText(),
            self.bold_checkbox.isChecked(),
            self.italic_checkbox.isChecked(),
            self.font_combo.currentText(),
            self.resize_spin.value(),
            self.text_color,
            self.font_size_spin.value()
        )

    def getValues(self):
        return (
            self.text_edit.toPlainText(),
            self.bold_checkbox.isChecked(),
            self.italic_checkbox.isChecked(),
            self.font_combo.currentText(),
            self.resize_spin.value(),
            self.text_color,
            self.font_size_spin.value()
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grid with Cell Painting, Text Overlay, and Eyedropper (P)")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAcceptDrops(True)
        self.undo_stack = []
        self.redo_stack = []
        self.default_color = QColor("green")
        self.paint_mode = False
        self.paint_color = QColor("green")
        self.eyedrop_mode = False
        self.uncolor_mode = False
        self.picked_color = None
        self.selected_rows = []  # Selected row indices.
        self.last_selected_row = None
        self.selected_columns = []  # Selected column indices.
        self.last_selected_column = None
        self.row_labels = []
        self.col_labels = []

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)
        grid_layout.setSpacing(0)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        grid_layout.addWidget(QLabel(""), 0, 0)

        self.num_rows = 32
        self.num_cols = 64
        cell_size = 15
        group_size = 8

        for c in range(self.num_cols):
            grid_col = 1 + c + (c // group_size)
            col_lbl = ColumnLabel(str(c % group_size), c, main_window=self)
            self.col_labels.append(col_lbl)
            grid_layout.addWidget(col_lbl, 0, grid_col)

        self.buttons = []
        for r in range(self.num_rows):
            row_lbl = RowLabel(str(r), r, main_window=self)
            self.row_labels.append(row_lbl)
            grid_layout.addWidget(row_lbl, r + 1, 0)
            row_buttons = []
            for c in range(self.num_cols):
                grid_col = 1 + c + (c // group_size)
                btn = CircleButton(size=cell_size, default_color=self.default_color,
                                   on_toggle=self.record_undo, main_window=self)
                grid_layout.addWidget(btn, r + 1, grid_col)
                row_buttons.append(btn)
            self.buttons.append(row_buttons)

        for i in range(1, self.num_cols // group_size):
            sep_col = i * (group_size + 1)
            separator = QFrame(self)
            separator.setFrameShape(QFrame.Shape.VLine)
            separator.setLineWidth(1)
            separator.setFixedWidth(1)
            separator.setStyleSheet("background-color: #cccccc;")
            grid_layout.addWidget(separator, 1, sep_col, self.num_rows, 1)

        self.setup_menu()

    def change_grid_size(self):
        dialog = GridSizeDialog(self.num_rows, self.num_cols, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_rows, new_cols = dialog.getValues()
            self.num_rows = new_rows
            self.num_cols = new_cols
            self.rebuild_grid()

    def rebuild_grid(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)
        grid_layout.setSpacing(0)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        group_size = 8

        self.col_labels = []
        grid_layout.addWidget(QLabel(""), 0, 0)
        for c in range(self.num_cols):
            grid_col = 1 + c + (c // group_size)
            col_lbl = ColumnLabel(str(c % group_size), c, main_window=self)
            self.col_labels.append(col_lbl)
            grid_layout.addWidget(col_lbl, 0, grid_col)

        self.row_labels = []
        self.buttons = []
        for r in range(self.num_rows):
            row_lbl = RowLabel(str(r), r, main_window=self)
            self.row_labels.append(row_lbl)
            grid_layout.addWidget(row_lbl, r + 1, 0)
            row_buttons = []
            for c in range(self.num_cols):
                grid_col = 1 + c + (c // group_size)
                btn = CircleButton(size=15, default_color=self.default_color,
                                   on_toggle=self.record_undo, main_window=self)
                grid_layout.addWidget(btn, r + 1, grid_col)
                row_buttons.append(btn)
            self.buttons.append(row_buttons)

        for i in range(1, self.num_cols // group_size):
            sep_col = i * (group_size + 1)
            separator = QFrame(self)
            separator.setFrameShape(QFrame.Shape.VLine)
            separator.setLineWidth(1)
            separator.setFixedWidth(1)
            separator.setStyleSheet("background-color: #cccccc;")
            grid_layout.addWidget(separator, 1, sep_col, self.num_rows, 1)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                self.load_image_from_file(file_path)
        event.acceptProposedAction()

    def load_image_from_file(self, filename: str):
        try:
            img = Image.open(filename)
            img = img.convert("RGB")
            target_width, target_height = self.num_cols, self.num_rows
            original_width, original_height = img.size
            scale_factor = min(target_width / original_width, target_height / original_height)
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            resized_img = img.resize((new_width, new_height), Image.NEAREST)
            new_img = Image.new("RGB", (target_width, target_height), "white")
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            new_img.paste(resized_img, (x_offset, y_offset))
            new_state = []
            for y in range(self.num_rows):
                row_state = []
                for x in range(self.num_cols):
                    pixel = new_img.getpixel((x, y))
                    if pixel == (255, 255, 255) or pixel == (0, 0, 0):
                        row_state.append((False, (0, 0, 0)))
                    else:
                        row_state.append((True, pixel))
                new_state.append(row_state)
            self.record_undo()
            self.set_grid_state(new_state)
        except Exception as e:
            print(f"Error loading image from file: {e}")

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
        open_png_action = QAction("Open PNG", self)
        open_png_action.setShortcut("Ctrl+U")
        open_png_action.triggered.connect(self.import_png_state)
        file_menu.addAction(open_png_action)
        text_overlay_action = QAction("Text Overlay", self)
        text_overlay_action.setShortcut("Ctrl+I")
        text_overlay_action.triggered.connect(self.open_text_overlay_dialog)
        file_menu.addAction(text_overlay_action)
        copy_formatted_action = QAction("Copy (Formatted)", self)
        copy_formatted_action.setShortcut("Ctrl+C")
        copy_formatted_action.triggered.connect(self.copy_formatted_to_clipboard)
        file_menu.addAction(copy_formatted_action)

        edit_menu = menu_bar.addMenu("Edit")
        undo_action = QAction("Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        redo_action = QAction("Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        global_paint_color_action = QAction("Set Global Paint Color", self)
        global_paint_color_action.setShortcut("Ctrl+W")
        global_paint_color_action.triggered.connect(self.choose_global_paint_color)
        edit_menu.addAction(global_paint_color_action)
        all_cells_color_action = QAction("Set All Colored Cells Color", self)
        all_cells_color_action.setShortcut("Ctrl+F")
        all_cells_color_action.triggered.connect(self.set_all_colored_cells_color)
        edit_menu.addAction(all_cells_color_action)
        change_picked_color_action = QAction("Change Picked Cells Color", self)
        change_picked_color_action.setShortcut("Ctrl+E")
        change_picked_color_action.triggered.connect(self.change_all_picked_cells_color)
        edit_menu.addAction(change_picked_color_action)
        change_all_allowed_action = QAction("Change All to Allowed Colors", self)
        change_all_allowed_action.setShortcut("Ctrl+X")
        change_all_allowed_action.triggered.connect(self.change_all_cells_to_allowed_colors)
        edit_menu.addAction(change_all_allowed_action)
        shift_menu = edit_menu.addMenu("Shift Grid")
        shift_left_action = QAction("Shift Left", self)
        shift_left_action.setShortcut("Ctrl+Left")
        shift_left_action.triggered.connect(lambda: self.shift_grid("left"))
        shift_menu.addAction(shift_left_action)
        shift_right_action = QAction("Shift Right", self)
        shift_right_action.setShortcut("Ctrl+Right")
        shift_right_action.triggered.connect(lambda: self.shift_grid("right"))
        shift_menu.addAction(shift_right_action)
        shift_up_action = QAction("Shift Up", self)
        shift_up_action.setShortcut("Ctrl+Up")
        shift_up_action.triggered.connect(lambda: self.shift_grid("up"))
        shift_menu.addAction(shift_up_action)
        shift_down_action = QAction("Shift Down", self)
        shift_down_action.setShortcut("Ctrl+Down")
        shift_down_action.triggered.connect(lambda: self.shift_grid("down"))
        shift_menu.addAction(shift_down_action)

        options_menu = menu_bar.addMenu("Options")
        grid_size_action = QAction("Grid Size", self)
        grid_size_action.triggered.connect(self.change_grid_size)
        options_menu.addAction(grid_size_action)

    def update_row_label_styles(self):
        for lbl in self.row_labels:
            if lbl.row_index in self.selected_rows:
                lbl.setStyleSheet("background-color: lightblue;")
            else:
                lbl.setStyleSheet("")

    def update_column_label_styles(self):
        for lbl in self.col_labels:
            if lbl.col_index in self.selected_columns:
                lbl.setStyleSheet("background-color: lightblue; border: 1px solid gray;")
            else:
                lbl.setStyleSheet("border: 1px solid gray;")

    def select_row(self, row_index, shift=False):
        self.update_column_label_styles()
        if shift and self.last_selected_row is not None:
            start = min(self.last_selected_row, row_index)
            end = max(self.last_selected_row, row_index)
            self.selected_rows = list(range(start, end + 1))
        else:
            self.selected_rows = [row_index]
            self.last_selected_row = row_index
        self.update_row_label_styles()

    def select_column(self, col_index, shift=False):
        self.update_row_label_styles()
        if shift and self.last_selected_column is not None:
            start = min(self.last_selected_column, col_index)
            end = max(self.last_selected_column, col_index)
            self.selected_columns = list(range(start, end + 1))
        else:
            self.selected_columns = [col_index]
            self.last_selected_column = col_index
        self.update_column_label_styles()

    def move_selected_rows_up(self):
        if not self.selected_rows:
            return
        start = min(self.selected_rows)
        end = max(self.selected_rows)
        if start == 0:
            return
        state = self.get_grid_state()
        state[start - 1:end + 1] = state[start:end + 1] + [state[start - 1]]
        self.record_undo()
        self.set_grid_state(state)
        self.selected_rows = [r - 1 for r in self.selected_rows]
        self.update_row_label_styles()
        self.last_selected_row = self.selected_rows[0]

    def move_selected_rows_down(self):
        if not self.selected_rows:
            return
        start = min(self.selected_rows)
        end = max(self.selected_rows)
        if end == self.num_rows - 1:
            return
        state = self.get_grid_state()
        state[start:end + 2] = [state[end + 1]] + state[start:end + 1]
        self.record_undo()
        self.set_grid_state(state)
        self.selected_rows = [r + 1 for r in self.selected_rows]
        self.update_row_label_styles()
        self.last_selected_row = self.selected_rows[-1]

    def shift_selected_rows_left(self):
        if not self.selected_rows:
            return
        state = self.get_grid_state()
        for r in self.selected_rows:
            row = state[r]
            state[r] = row[1:] + row[0:1]
        self.record_undo()
        self.set_grid_state(state)

    def shift_selected_rows_right(self):
        if not self.selected_rows:
            return
        state = self.get_grid_state()
        for r in self.selected_rows:
            row = state[r]
            state[r] = row[-1:] + row[:-1]
        self.record_undo()
        self.set_grid_state(state)

    def move_selected_columns_left(self):
        if not self.selected_columns:
            return
        start = min(self.selected_columns)
        end = max(self.selected_columns)
        if start == 0:
            return
        state = self.get_grid_state()
        for r in range(self.num_rows):
            row = state[r]
            row[start - 1:end + 1] = row[start:end + 1] + [row[start - 1]]
        self.record_undo()
        self.set_grid_state(state)
        self.selected_columns = [c - 1 for c in self.selected_columns]
        self.update_column_label_styles()
        self.last_selected_column = self.selected_columns[0]

    def move_selected_columns_right(self):
        if not self.selected_columns:
            return
        start = min(self.selected_columns)
        end = max(self.selected_columns)
        if end == self.num_cols - 1:
            return
        state = self.get_grid_state()
        for r in range(self.num_rows):
            row = state[r]
            row[start:end + 2] = [row[end + 1]] + row[start:end + 1]
        self.record_undo()
        self.set_grid_state(state)
        self.selected_columns = [c + 1 for c in self.selected_columns]
        self.update_column_label_styles()
        self.last_selected_column = self.selected_columns[-1]

    def shift_selected_columns_up(self):
        if not self.selected_columns:
            return
        state = self.get_grid_state()
        for c in sorted(self.selected_columns):
            col_vals = [state[r][c] for r in range(self.num_rows)]
            new_col = col_vals[1:] + [col_vals[0]]
            for r in range(self.num_rows):
                state[r][c] = new_col[r]
        self.record_undo()
        self.set_grid_state(state)

    def shift_selected_columns_down(self):
        if not self.selected_columns:
            return
        state = self.get_grid_state()
        for c in sorted(self.selected_columns):
            col_vals = [state[r][c] for r in range(self.num_rows)]
            new_col = [col_vals[-1]] + col_vals[:-1]
            for r in range(self.num_rows):
                state[r][c] = new_col[r]
        self.record_undo()
        self.set_grid_state(state)

    def shift_intersection_horizontal(self, left=True):
        state = self.get_grid_state()
        for r in sorted(self.selected_rows):
            cols = sorted(self.selected_columns)
            sub = [state[r][c] for c in cols]
            new_sub = sub[1:] + [sub[0]] if left else [sub[-1]] + sub[:-1]
            for i, c in enumerate(cols):
                state[r][c] = new_sub[i]
        self.record_undo()
        self.set_grid_state(state)

    def shift_intersection_vertical(self, up=True):
        state = self.get_grid_state()
        for c in sorted(self.selected_columns):
            rows = sorted(self.selected_rows)
            sub = [state[r][c] for r in rows]
            new_sub = sub[1:] + [sub[0]] if up else [sub[-1]] + sub[:-1]
            for i, r in enumerate(rows):
                state[r][c] = new_sub[i]
        self.record_undo()
        self.set_grid_state(state)

    def keyPressEvent(self, event):
        if self.selected_rows and self.selected_columns and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            if event.key() == Qt.Key.Key_Left:
                self.shift_intersection_horizontal(left=True)
                return
            elif event.key() == Qt.Key.Key_Right:
                self.shift_intersection_horizontal(left=False)
                return
            elif event.key() == Qt.Key.Key_Up:
                self.shift_intersection_vertical(up=True)
                return
            elif event.key() == Qt.Key.Key_Down:
                self.shift_intersection_vertical(up=False)
                return

        if self.selected_columns and not self.selected_rows and event.modifiers() == Qt.KeyboardModifier.NoModifier and event.key() in (
        Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
            if event.key() == Qt.Key.Key_Left:
                self.move_selected_columns_left()
            elif event.key() == Qt.Key.Key_Right:
                self.move_selected_columns_right()
            elif event.key() == Qt.Key.Key_Up:
                self.shift_selected_columns_up()
            elif event.key() == Qt.Key.Key_Down:
                self.shift_selected_columns_down()
            return

        if self.selected_rows and not self.selected_columns and event.modifiers() == Qt.KeyboardModifier.NoModifier and event.key() in (
        Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right):
            if event.key() == Qt.Key.Key_Up:
                self.move_selected_rows_up()
            elif event.key() == Qt.Key.Key_Down:
                self.move_selected_rows_down()
            elif event.key() == Qt.Key.Key_Left:
                self.shift_selected_rows_left()
            elif event.key() == Qt.Key.Key_Right:
                self.shift_selected_rows_right()
            return

        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_I:
            self.open_text_overlay_dialog()
            return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_W:
            self.choose_global_paint_color()
            return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_F:
            self.set_all_colored_cells_color()
            return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_U:
            self.import_png_state()
            return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_E:
            self.change_all_picked_cells_color()
            return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_C:
            self.copy_formatted_to_clipboard()
            return
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_X:
            self.change_all_cells_to_allowed_colors()
            return
        if (event.modifiers() == Qt.KeyboardModifier.ControlModifier and
                event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down)):
            if not event.isAutoRepeat():
                self.record_undo()
            if event.key() == Qt.Key.Key_Left:
                self.shift_grid("left", record_undo=False)
            elif event.key() == Qt.Key.Key_Right:
                self.shift_grid("right", record_undo=False)
            elif event.key() == Qt.Key.Key_Up:
                self.shift_grid("up", record_undo=False)
            elif event.key() == Qt.Key.Key_Down:
                self.shift_grid("down", record_undo=False)
            return
        if event.key() == Qt.Key.Key_P:
            self.eyedrop_mode = True
            return
        if event.key() == Qt.Key.Key_Escape:
            self.paint_mode = False
            self.paint_color = None
            self.eyedrop_mode = False
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_P:
            self.eyedrop_mode = False
        if event.key() == Qt.Key.Key_U and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            self.uncolor_mode = False
        else:
            super().keyReleaseEvent(event)

    def open_text_overlay_dialog(self):
        dialog = TextOverlayDialog(self, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            pass

    def apply_text_overlay(self, text, bold, italic, font_family, resize_factor, text_color, font_size):
        width = int(self.num_cols * resize_factor)
        height = int(self.num_rows * resize_factor)
        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)
        try:
            calculated_font_size = int(font_size * resize_factor)
            if font_family.lower() == "arial":
                if bold and italic:
                    font_path = "arialbi.ttf"
                elif bold:
                    font_path = "arialbd.ttf"
                elif italic:
                    font_path = "ariali.ttf"
                else:
                    font_path = "arial.ttf"
            elif font_family.lower() == "times new roman":
                if bold and italic:
                    font_path = "timesbi.ttf"
                elif bold:
                    font_path = "timesbd.ttf"
                elif italic:
                    font_path = "timesi.ttf"
                else:
                    font_path = "times.ttf"
            elif font_family.lower() == "courier new":
                if bold and italic:
                    font_path = "courbi.ttf"
                elif bold:
                    font_path = "courbd.ttf"
                elif italic:
                    font_path = "couri.ttf"
                else:
                    font_path = "cour.ttf"
            else:
                font_path = "arial.ttf"
            font = ImageFont.truetype(font_path, calculated_font_size)
        except Exception as e:
            font = ImageFont.load_default()
        tc = (text_color.red(), text_color.green(), text_color.blue())
        draw.text((0, 0), text, fill=tc, font=font)
        self.apply_generated_image(img)

    def apply_generated_image(self, img):
        img_resized = img.resize((self.num_cols, self.num_rows), Image.NEAREST)
        new_state = []
        for y in range(self.num_rows):
            row_state = []
            for x in range(self.num_cols):
                pixel = img_resized.getpixel((x, y))
                if pixel != (255, 255, 255):
                    row_state.append((True, pixel))
                else:
                    row_state.append((False, (0, 0, 0)))
            new_state.append(row_state)
        self.record_undo()
        self.set_grid_state(new_state)

    def import_png_state(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Import PNG File", "", "PNG Files (*.png)")
        if not filename:
            return
        self.load_image_from_file(filename)

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
                    btn.cell_color = QColor(*rgb) if colored else None
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

    def shift_grid(self, direction, record_undo=True):
        if record_undo:
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

    def map_color_to_index(self, color: QColor) -> int:
        allowed_colors = {
            0: QColor("black"),
            1: QColor("red"),
            2: QColor("green"),
            3: QColor("blue"),
            4: QColor("yellow"),
            5: QColor("cyan"),
            6: QColor("pink"),
            7: QColor("white")
        }
        r, g, b, _ = color.getRgb()
        best_index = 0
        best_distance = float("inf")
        for idx, allowed in allowed_colors.items():
            ar, ag, ab, _ = allowed.getRgb()
            dist = (r - ar) ** 2 + (g - ag) ** 2 + (b - ab) ** 2
            if dist < best_distance:
                best_distance = dist
                best_index = idx
        return best_index

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
                f.write(f"#export_format:{mode}\n")
                if mode == "Colored":
                    for row in self.buttons[start_row:end_row + 1]:
                        line = ",".join(
                            str(self.map_color_to_index(btn.cell_color if (btn.colored and btn.cell_color is not None)
                                                        else QColor("black")))
                            for btn in row
                        )
                        f.write(line + "\n")
                elif mode == "Plain":
                    for row in self.buttons[start_row:end_row + 1]:
                        line = " ".join("1" if (
                                    btn.colored and btn.cell_color is not None and btn.cell_color.name() != "#000000") else "0"
                                        for btn in row)
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
                else:
                    for row in self.buttons[start_row:end_row + 1]:
                        row_values = ["1" if (
                                    btn.colored and btn.cell_color is not None and btn.cell_color.name() != "#000000") else "0"
                                      for btn in row]
                        groups = []
                        group_size = 8
                        for i in range(0, len(row_values), group_size):
                            group = "".join(row_values[i:i + group_size])
                            groups.append("0b" + group)
                        line = ", ".join(groups) + ","
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
                lines = [line.rstrip("\r\n") for line in f]
            export_mode = "Plain"
            if lines and lines[0].startswith("#export_format:"):
                export_mode = lines[0].split(":", 1)[1].strip()
                lines = lines[1:]
            if export_mode == "Colored":
                imported_state = []
                for line in lines:
                    if not line.strip():
                        continue
                    parts = [p for p in line.split(",") if p != ""]
                    row_state = [int(val) for val in parts]
                    imported_state.append(row_state)
                color_mapping = {
                    0: QColor("black"),
                    1: QColor("red"),
                    2: QColor("green"),
                    3: QColor("blue"),
                    4: QColor("yellow"),
                    5: QColor("cyan"),
                    6: QColor("pink"),
                    7: QColor("white")
                }
                self.record_undo()
                for r in range(min(len(imported_state), self.num_rows)):
                    for c in range(min(len(imported_state[r]), self.num_cols)):
                        btn = self.buttons[r][c]
                        val = imported_state[r][c]
                        btn.colored = True
                        btn.cell_color = color_mapping.get(val, self.default_color)
                        btn.update()
            elif export_mode == "Formatted":
                imported_state = []
                for line in lines:
                    if not line.strip():
                        continue
                    groups = [grp.strip() for grp in line.split(",") if grp.strip()]
                    row_str = ""
                    for grp in groups:
                        if grp.startswith("0b"):
                            row_str += grp[2:]
                    row_bool = [True if ch == "1" else False for ch in row_str]
                    imported_state.append(row_bool)
                self.record_undo()
                for r in range(min(len(imported_state), self.num_rows)):
                    for c in range(min(len(imported_state[r]), self.num_cols)):
                        btn = self.buttons[r][c]
                        if imported_state[r][c]:
                            btn.colored = True
                            btn.cell_color = self.default_color
                        else:
                            btn.colored = False
                            btn.cell_color = None
                        btn.update()
                if "#colors" in lines:
                    index = lines.index("#colors")
                    color_data = lines[index + 1:]
                    for r in range(min(len(color_data), self.num_rows)):
                        parts = color_data[r].split()
                        for c in range(min(len(parts), self.num_cols)):
                            rgb_parts = parts[c].split(",")
                            if len(rgb_parts) >= 3:
                                r_val = int(rgb_parts[0])
                                g_val = int(rgb_parts[1])
                                b_val = int(rgb_parts[2])
                                btn = self.buttons[r][c]
                                btn.cell_color = QColor(r_val, g_val, b_val)
                                btn.colored = True
                                btn.update()
            else:
                main_data = lines
                color_data = []
                if "#colors" in lines:
                    index = lines.index("#colors")
                    main_data = lines[:index]
                    color_data = lines[index + 1:]
                imported_state = []
                for line in main_data:
                    if not line.strip():
                        continue
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
                lines = [line.rstrip("\r\n") for line in f]
            export_mode = "Plain"
            if lines and lines[0].startswith("#export_format:"):
                export_mode = lines[0].split(":", 1)[1].strip()
                lines = lines[1:]
            if export_mode == "Colored":
                imported_state = []
                for line in lines:
                    if not line.strip():
                        continue
                    parts = [p for p in line.split(",") if p != ""]
                    row_state = [int(val) for val in parts]
                    imported_state.append(row_state)
                color_mapping = {
                    0: QColor("black"),
                    1: QColor("red"),
                    2: QColor("green"),
                    3: QColor("blue"),
                    4: QColor("yellow"),
                    5: QColor("cyan"),
                    6: QColor("pink"),
                    7: QColor("white")
                }
                current_state = self.get_grid_state()
                new_state = []
                for r in range(min(len(current_state), len(imported_state))):
                    new_row = []
                    for c in range(min(len(current_state[r]), len(imported_state[r]))):
                        val = imported_state[r][c]
                        new_row.append((True, (
                            color_mapping.get(val, self.default_color).red(),
                            color_mapping.get(val, self.default_color).green(),
                            color_mapping.get(val, self.default_color).blue())))
                    new_state.append(new_row)
                self.record_undo()
                self.set_grid_state(new_state)
            elif export_mode == "Formatted":
                imported_state = []
                for line in lines:
                    if not line.strip():
                        continue
                    groups = [grp.strip() for grp in line.split(",") if grp.strip()]
                    row_str = ""
                    for grp in groups:
                        if grp.startswith("0b"):
                            row_str += grp[2:]
                    row_bool = [True if ch == "1" else False for ch in row_str]
                    imported_state.append(row_bool)
                current_state = self.get_grid_state()
                new_state = []
                for r in range(min(len(current_state), len(imported_state))):
                    new_row = []
                    for c in range(min(len(current_state[r]), len(imported_state[r]))):
                        if imported_state[r][c]:
                            new_row.append((True, (
                            self.default_color.red(), self.default_color.green(), self.default_color.blue())))
                        else:
                            new_row.append(current_state[r][c])
                    new_state.append(new_row)
                self.record_undo()
                self.set_grid_state(new_state)
                if "#colors" in lines:
                    index = lines.index("#colors")
                    color_data = lines[index + 1:]
                    for r in range(min(len(color_data), self.num_rows)):
                        parts = color_data[r].split()
                        for c in range(min(len(parts), self.num_cols)):
                            rgb_parts = parts[c].split(",")
                            if len(rgb_parts) >= 3:
                                r_val = int(rgb_parts[0])
                                g_val = int(rgb_parts[1])
                                b_val = int(rgb_parts[2])
                                btn = self.buttons[r][c]
                                btn.cell_color = QColor(r_val, g_val, b_val)
                                btn.colored = True
                                btn.update()
            else:
                main_data = lines
                color_data = []
                if "#colors" in lines:
                    index = lines.index("#colors")
                    main_data = lines[:index]
                    color_data = lines[index + 1:]
                imported_state = []
                for line in main_data:
                    if not line.strip():
                        continue
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

    def copy_formatted_to_clipboard(self):
        max_rows = self.num_rows
        dialog = ExportSettingsDialog(max_rows, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        start_row, end_row, mode = dialog.getValues()
        if start_row > end_row:
            start_row, end_row = end_row, start_row
        output = ""
        if mode == "Colored":
            for row in self.buttons[start_row:end_row + 1]:
                line = ",".join(
                    str(self.map_color_to_index(btn.cell_color if (btn.colored and btn.cell_color is not None)
                                                else QColor("black")))
                    for btn in row
                )
                output += line + "\n"
        elif mode == "Plain":
            for row in self.buttons[start_row:end_row + 1]:
                line = " ".join(
                    "1" if (btn.colored and btn.cell_color is not None and btn.cell_color.name() != "#000000") else "0"
                    for btn in row)
                output += line + "\n"
        else:
            for row in self.buttons[start_row:end_row + 1]:
                row_values = [
                    "1" if (btn.colored and btn.cell_color is not None and btn.cell_color.name() != "#000000") else "0"
                    for btn in row]
                groups = []
                group_size = 8
                for i in range(0, len(row_values), group_size):
                    group = "".join(row_values[i:i + group_size])
                    groups.append("0b" + group)
                line = ", ".join(groups) + ","
                output += line + "\n"
        clipboard = QApplication.clipboard()
        clipboard.setText(output)

    def choose_global_paint_color(self):
        chosen = QColorDialog.getColor(self.default_color, self, "Select Paint Mode Color")
        if chosen.isValid():
            self.paint_color = chosen
            self.paint_mode = True

    def set_all_colored_cells_color(self):
        chosen = QColorDialog.getColor(self.default_color, self, "Select new color for all colored cells")
        if not chosen.isValid():
            return
        self.record_undo()
        for row in self.buttons:
            for btn in row:
                if btn.colored:
                    btn.cell_color = chosen
                    btn.update()

    def change_all_picked_cells_color(self):
        if self.picked_color is None:
            return
        chosen = QColorDialog.getColor(self.default_color, self, "Select New Color for Picked Cells")
        if chosen.isValid():
            self.record_undo()
            for row in self.buttons:
                for btn in row:
                    if btn.colored and btn.cell_color == self.picked_color:
                        btn.cell_color = chosen
                        btn.update()

    def change_all_cells_to_allowed_colors(self):
        self.record_undo()
        allowed_colors = {
            0: QColor("black"),
            1: QColor("red"),
            2: QColor("green"),
            3: QColor("blue"),
            4: QColor("yellow"),
            5: QColor("cyan"),
            6: QColor("pink"),
            7: QColor("white")
        }
        for row in self.buttons:
            for btn in row:
                if btn.colored and btn.cell_color is not None:
                    index = self.map_color_to_index(btn.cell_color)
                    btn.cell_color = allowed_colors[index]
                    btn.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
