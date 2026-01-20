# MDViewer-AGL

A high-fidelity, standalone Markdown Viewer built with Python and `pywebview`. It leverages the native Windows Edge (WebView2) engine to provide a premium, GitHub-like reading experience for local Markdown files.

![MDViewer Icon](app_icon.ico)

## 🚀 Features

- **Native Fidelity**: Uses the Edge Chromium engine for perfect rendering of tables, task lists, and code blocks.
- **Base64 Image Embedding**: Automatically converts local images to Base64 data URIs to bypass browser security restrictions. Relative paths like `![alt](assets/image.png)` just work.
- **Modern UI**:
    -   Clean landing page with a "Browse File" button.
    -   Drag-and-drop support for quick previews.
    -   Custom GitHub-mimicking CSS for a familiar feel.
- **Standalone Executable**: Packaged with PyInstaller into a single `.exe` with a custom YouTube-themed icon.
- **CLI & File Association**: Designed to work as a default "Open With" handler for `.md` files.

## 🛠 Architecture

- **Backend**: Python 3.13
- **Frontend Engine**: `pywebview` (using Edge WebView2/Chromium)
- **Converter**: `markdown` library with extensions (fenced code, tables, nl2br).
- **Styling**: Embedded GitHub-style CSS via a custom Python template.

## 📖 Usage

### Using the Executable
The easiest way to use the viewer is the pre-built executable:
1. Navigate to `dist/MDViewer.exe`.
2. Double-click to launch the landing page.
3. Or, right-click any `.md` file -> **Open with...** -> Choose `MDViewer.exe`.

### Command Line
You can launch the viewer directly with a file path:
```ps1
.\dist\MDViewer.exe "C:\path\to\your\document.md"
```

## 💻 Development

### Setup
1. Clone the repository.
2. Create a virtual environment:
   ```ps1
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
3. Install dependencies:
   ```ps1
   pip install -r requirements.txt
   ```

### Running from Source
```ps1
python mdviewer.py
```

### Building the Executable
To rebuild the standalone `.exe` with the custom icon:
```ps1
pyinstaller --noconsole --onefile --icon "app_icon.ico" --name "MDViewer" mdviewer.py
```

## 📂 Project Structure
- `mdviewer.py`: The core application logic and UI template.
- `app_icon.ico`: The YouTube-themed application icon.
- `requirements.txt`: Python dependencies.
- `.venv/`: Local virtual environment (ignored by Git).
- `dist/MDViewer.exe`: The final distributable binary.

## ⚖ License
Apache License 2.0
