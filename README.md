# LED Grid Display App

## Overview

The LED Grid Display App is a Python-based application that simulates an LED display. It presents a grid of fixed-size cells (32 rows x 64 columns) where each cell displays a circle that can be toggled on (colored) or off (black). The app offers a variety of interactive features including:

- Custom cell painting (individual and global color selection)
- Eyedropper functionality to sample a cell’s color
- Batch update of all colored cells with a new color
- Text overlay rendering with customizable font, size, spacing, and color (with font type selection)
- File operations (Export, Import, Merge Import) that save and restore per-cell color data
- Undo/Redo support

**Designed for Embedded Developers:**  
This program is written specifically for embedded developers. It allows you to easily find the right appearance for static display images without having to rebuild and run code on your microcontroller every time. You can export the result and then copy-paste the generated data into your microcontroller code, streamlining your development workflow.

## Features & Use Cases

### Grid Interaction

- **Toggle Cell State:**  
  Left-click a cell to toggle its state between off (black) and on (colored; default is green).

- **Individual Cell Color Selection:**  
  Hold **Ctrl** and click a cell to open a color dialog and set a custom color for that cell.

- **Global Paint Mode (Ctrl+W):**  
  Press **Ctrl+W** to select a global paint color. In this mode, subsequent clicks will paint cells with the chosen color.

- **Eyedropper Mode (P):**  
  Hold the **P** key and click on a cell to sample its color and set it as the global paint color.

- **Batch Color Update (Ctrl+F):**  
  Press **Ctrl+F** to open a color dialog that updates all currently colored cells to a new color.

### Text Overlay

- **Text Overlay Dialog (Ctrl+I):**  
  Press **Ctrl+I** to open a dialog for inserting plain text (Unicode supported) onto the grid.  
  In this dialog, you can adjust:
  - **Font Size (cells):** The pixel height for each character.
  - **Line Spacing (rows):** Extra vertical pixels between lines.
  - **Empty Cols (cols):** Extra horizontal pixels between characters.
  - **Text Color:** The color used to render the text.
  - **Font Type:** Use the **Select Font** button to choose a font type (e.g., Minecraft or Pixel Unicode font) for rendering the text overlay.  
  The grid updates in real time as you modify these parameters.

### File Operations

- **Export (Ctrl+S):**  
  Save the current grid state to a file. The export includes:
  - Main grid data (each cell marked "1" for colored, "0" for off) in either Plain or Formatted mode.
  - A separate section with per-cell RGB color information (after a `#colors` header).

- **Import (Ctrl+O):**  
  Load a grid state from a file.

- **Merge Import (Ctrl+M):**  
  Import grid data from a file and merge it with the current state—cells turned on in the imported file override the current state.

- **Reset (Ctrl+R):**  
  Clear the grid (all cells off).

- **Undo (Ctrl+Z) & Redo (Ctrl+Y):**  
  Step backward or forward through changes.

## Hotkeys Summary

- **Left Click:** Toggle cell state.
- **Ctrl+Click:** Open a color dialog for the clicked cell.
- **Ctrl+W:** Activate global paint mode to set a color for future cell clicks.
- **P:** Hold to enter eyedropper mode; click a cell to sample its color.
- **Ctrl+F:** Open a color dialog to update all colored cells with a new color.
- **Ctrl+I:** Open the text overlay dialog (includes font type selection).
- **Ctrl+S:** Export the current grid state to a file.
- **Ctrl+O:** Import a grid state from a file.
- **Ctrl+M:** Merge import grid state with the current grid.
- **Ctrl+R:** Reset the grid.
- **Ctrl+Z:** Undo the last change.
- **Ctrl+Y:** Redo the change.
- **Escape:** Cancel global paint/eyedropper mode.

## Dependencies

- **Python 3.12**
- **PyQt6** – For the graphical user interface.
- **NumPy** – For processing image data.
- **Pillow** – For text rendering in the text overlay feature.
- **freetype‑py** (optional) – For an alternative advanced text rendering implementation.

Install dependencies using:

```bash
pip install PyQt6 numpy pillow
