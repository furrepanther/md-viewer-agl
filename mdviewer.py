import sys
import os
import webview
import markdown
import traceback
import base64
import mimetypes
import re
from pathlib import Path
from time import sleep

# Setup Logging
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")
def log(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except:
        pass

log("--- App Starting ---")
log(f"Args: {sys.argv}")

MARKDOWN_CSS = """
<style>
/* Reset and Base */
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
    font-size: 16px;
    line-height: 1.5;
    word-wrap: break-word;
    color: #24292e;
    padding: 32px;
    background-color: #ffffff;
    max-width: 980px;
    margin: 0 auto;
}
h1, h2, h3, h4, h5, h6 { margin-top: 24px; margin-bottom: 16px; font-weight: 600; line-height: 1.25; }
h1 { font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
h2 { font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }
strong, b { font-weight: 700; color: #24292e; }

code { background-color: #f6f8fa; border-radius: 6px; font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace; font-size: 85%; padding: 0.2em 0.4em; }
pre { background-color: #f6f8fa; border-radius: 6px; font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace; font-size: 85%; line-height: 1.45; overflow: auto; padding: 16px; }
pre code { background-color: transparent; border: 0; padding: 0; margin: 0; overflow: visible; word-wrap: normal; display: inline; }

table { border-spacing: 0; border-collapse: collapse; margin-bottom: 16px; margin-top: 0; width: 100%; }
table th, table td { padding: 6px 13px; border: 1px solid #dfe2e5; }
table th { font-weight: 600; }
table tr:nth-child(2n) { background-color: #f6f8fa; }

img { max-width: 100%; box-sizing: content-box; background-color: #fff; }
blockquote { border-left: 0.25em solid #dfe2e5; color: #6a737d; padding: 0 1em; margin: 0; }
a { color: #0969da; text-decoration: none; }
a:hover { text-decoration: underline; }
hr { height: 0.25em; padding: 0; margin: 24px 0; background-color: #e1e4e8; border: 0; }
</style>
"""

class MarkdownViewerApi:
    def __init__(self):
        self._window = None

    def set_window(self, window):
        self._window = window

    def open_file_dialog(self):
        file_types = ('Markdown Files (*.md;*.markdown;*.txt)', 'All files (*.*)')
        try:
            result = self._window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
            if result:
                self.load_file(result[0])
        except Exception as e:
            log(f"Dialog Error: {e}")

    def embed_local_images(self, html_content, base_path):
        """
        Encodes local images in base64 to bypass browser security restrictions.
        """
        def replace_match(match):
            prefix = match.group(1)
            src = match.group(2)
            suffix = match.group(3)

            if src.startswith(('http://', 'https://', 'data:')):
                return match.group(0)

            try:
                img_path = (Path(base_path) / src).resolve()
                if not img_path.exists():
                    log(f"Image not found: {img_path}")
                    return match.group(0)
                
                mime_type, _ = mimetypes.guess_type(img_path)
                if not mime_type:
                    mime_type = 'image/png'
                
                with open(img_path, "rb") as img_f:
                    encoded_string = base64.b64encode(img_f.read()).decode('utf-8')
                    
                new_src = f"data:{mime_type};base64,{encoded_string}"
                log(f"Embedded image: {src}")
                return f'{prefix}{new_src}{suffix}'
            except Exception as e:
                log(f"Failed to embed image {src}: {e}")
                return match.group(0)

        pattern = r'(<img\s+[^>]*?src=")([^"]+)("[^>]*>)'
        return re.sub(pattern, replace_match, html_content)

    def handle_drop(self, content, filename):
        log(f"Dropped content from {filename}")
        try:
            html_content = markdown.markdown(content, extensions=['fenced_code', 'tables', 'nl2br', 'sane_lists'])
            
            full_html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                {MARKDOWN_CSS}
                <script>
                    function setupDragDrop() {{
                        document.addEventListener('dragover', function(e) {{ e.preventDefault(); }});
                        document.addEventListener('drop', function(e) {{
                            e.preventDefault();
                            var file = e.dataTransfer.files[0];
                            if (file) {{
                                var reader = new FileReader();
                                reader.onload = function(e) {{
                                    window.pywebview.api.handle_drop(e.target.result, file.name);
                                }};
                                reader.readAsText(file);
                            }}
                        }});
                    }}
                    window.onload = setupDragDrop;
                </script>
            </head>
            <body>
                <div style="background: #fff3cd; color: #856404; padding: 10px; margin-bottom: 20px; border: 1px solid #ffeeba;">
                    <strong>Note:</strong> Drag & Drop preview does not support local images. Use <b>Open File</b> for full support.
                </div>
                {html_content}
            </body>
            </html>
            """
            self._window.load_html(full_html)
            self._window.set_title(f"Markdown Viewer - {filename} (Preview)")
        except Exception as e:
            log(f"Drop Error: {e}")

    def load_file(self, file_path):
        log(f"Loading file: {file_path}")
        try:
            if not os.path.exists(file_path):
                log("File does not exist")
                return

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            base_dir = os.path.dirname(os.path.abspath(file_path))
            html_content = markdown.markdown(content, extensions=['fenced_code', 'tables', 'nl2br', 'sane_lists'])
            html_content = self.embed_local_images(html_content, base_dir)
            
            full_html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                {MARKDOWN_CSS}
                <script>
                    function setupDragDrop() {{
                        document.addEventListener('dragover', function(e) {{ e.preventDefault(); }});
                        document.addEventListener('drop', function(e) {{
                            e.preventDefault();
                            var file = e.dataTransfer.files[0];
                            if (file) {{
                                var reader = new FileReader();
                                reader.onload = function(e) {{
                                    window.pywebview.api.handle_drop(e.target.result, file.name);
                                }};
                                reader.readAsText(file);
                            }}
                        }});
                    }}
                    window.onload = setupDragDrop;
                </script>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            self._window.load_html(full_html)
            self._window.set_title(f"Markdown Viewer - {os.path.basename(file_path)}")
            log("load_html called successfully")
        except Exception as e:
            log(f"Load Error: {e}")
            self._window.load_html(f"<h1>Error</h1><p>{traceback.format_exc()}</p>")

def main():
    api = MarkdownViewerApi()
    
    landing_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    display: flex; flex-direction: column; align-items: center; justify-content: center;
                    height: 100vh; margin: 0; background-color: #f6f8fa; color: #24292e;
                }
                .container {
                    text-align: center; padding: 40px; background: white; border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 500px;
                }
                h1 { margin-bottom: 24px; font-weight: normal; }
                p { margin-bottom: 32px; color: #586069; }
                button {
                    background-color: #2ea44f; color: white; border: none; padding: 12px 24px;
                    font-size: 16px; border-radius: 6px; cursor: pointer; font-weight: 600;
                    transition: background-color 0.2s;
                }
                button:hover { background-color: #2c974b; }
                .drop-zone {
                    border: 2px dashed #e1e4e8; padding: 20px; margin-top: 30px;
                    border-radius: 6px; color: #586069; font-size: 14px;
                }
            </style>
            <script>
                function setupDragDrop() {
                    document.addEventListener('dragover', function(e) { e.preventDefault(); });
                    document.addEventListener('drop', function(e) {
                        e.preventDefault();
                        var file = e.dataTransfer.files[0];
                        if (file) {
                            var reader = new FileReader();
                            reader.onload = function(e) {
                                window.pywebview.api.handle_drop(e.target.result, file.name);
                            };
                            reader.readAsText(file);
                        }
                    });
                }
                window.onload = setupDragDrop;
            </script>
        </head>
        <body>
            <div class="container">
                <h1>Markdown Viewer</h1>
                <p>Please select a Markdown file to view.</p>
                <button onclick="window.pywebview.api.open_file_dialog()">Browse File...</button>
                <div class="drop-zone"> Or drag and drop a file anywhere here </div>
            </div>
        </body>
        </html>
    """

    window = webview.create_window(
        "Markdown Viewer", 
        html=landing_html,
        js_api=api,
        width=1200,
        height=900,
        resizable=True
    )
    api.set_window(window)

    def on_loaded():
        log("Window loading process started...")
        try:
            # Handle both single and multiple (split) arguments
            argv = sys.argv
            target_file = None
            if len(argv) > 1:
                # Try to find a valid file in the arguments
                for i in range(1, len(argv)):
                    path_candidate = " ".join(argv[1:i+1]).strip().strip('"').strip("'")
                    if os.path.exists(path_candidate) and os.path.isfile(path_candidate):
                        target_file = path_candidate
                        break
                
                if not target_file:
                    # Fallback to checking each arg individually if join fails
                    for arg in argv[1:]:
                        clean_arg = arg.strip().strip('"').strip("'")
                        if os.path.exists(clean_arg) and os.path.isfile(clean_arg):
                            target_file = clean_arg
                            break
            
            if target_file:
                log(f"Automatically loading: {target_file}")
                # Wait a bit longer to ensure the window's main loop is fully settled
                sleep(1.0)
                api.load_file(target_file)
            else:
                log("No file specified in arguments.")
        except Exception as e:
            log(f"Error in on_loaded: {e}")

    webview.start(on_loaded, debug=False)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"Fatal startup error: {e}")
        traceback.print_exc()
