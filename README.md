# FileSearch Pro (FileSearchUtil)

A modern, fast, and responsive Desktop File Search & Sort utility built with **CustomTkinter** and **Python 3.13**.

---

## Features

- 📁 **File Explorer & Navigation Panel (Left Pane)**:
  - **Drive & Share Discovery**: Automatically enumerates all system drives and mapped network shares (`C:\`, `D:\`, `E:\`, `G:\`, etc.) with friendly labels (e.g. `Dev (\\desktop-5g7gkun\d) (D:)`, `Local Disk (C:)`, `USB Drive (G:)`).
  - **Folder & File Browsing in Results**: Selecting any folder in the left pane displays both direct subfolders (`📁 ` icon) and direct files located in that folder.
  - **Two-Way Navigation Sync**: Clicking a folder row in the search results table updates the **"📁 Directory:"** input box and expands/reveals that folder in the left navigation tree. Double-clicking (or pressing <kbd>Enter</kbd>) on a folder navigates directly into it.
  - **Resizable Layout**: Separated from the right search workspace by an adjustable `ttk.PanedWindow` divider sash.
  - **Tree Refresh (`↻`)**: Refresh drive and directory hierarchies with a single click while preserving active selection.
- ⚡ **Fast & Progressive Search**: Real-time results streaming ordered by **Date Modified (Newest to Oldest)** with live progress bar and status indicator.
- 🔍 **Rich Query & Pattern Matching**:
  - `,` (Comma OR Operator): Combine multiple search patterns as **OR** (e.g. `java, j2ee` finds files matching "java" OR "j2ee").
  - `|` (Pipe OR Operator): Search for alternative terms within a single pattern (e.g. `ai agent|agents`).
  - `NOT` (Exclusion Operator): Exclude single or multiple keywords (e.g. `ai * pattern NOT apress and addison`, `ai agent NOT agents`, or `ai * pattern NOT apress NOT addison`).
  - `*` : Matches zero or more characters (e.g. `java * pattern` matches `Java 17 Design Patterns`).
  - `?` : Matches any single character (e.g. `python?` matches `python3`).
- 📄 **Extension Inclusion & Exclusion**:
  - Target specific extensions: `pdf, epub, txt`
  - Exclude unwanted extensions using `-` or `NOT`: `pdf, epub, -java` (matches PDF and EPUB files while excluding `.java` files), or `-tmp, -log` (matches all extensions except `.tmp` and `.log`).
- 🛑 **Instant Search Control**:
  - Press <kbd>Enter</kbd> in the search pattern field to instantly clear previous results and run a fresh search.
  - Press <kbd>Esc</kbd> anywhere in the window to halt an active search in real time.
- 🏢 **Publisher & Year Detection**: Automatically detects recognized publishers (O'Reilly, Manning, Wiley, Packt, etc.) and release years from file names.
- 📊 **Multi-Criteria Sorting**: Sort by **Published Year**, **Publisher**, **Date Modified**, **Size**, or **File Name**.
- 🎯 **Live Filter Box**: Instant in-memory filtering of search results with wildcard support.
- 🖱️ **Windows Integration & Drag and Drop**:
  - **Universal Drag & Drop**: Click and drag any single file or multiple selected files directly from the search results table into Windows Explorer, Desktop, browser upload areas, VS Code, or any other application.
  - **GOM Player & Media Player Support**: Built-in native `WM_DROPFILES` bridge with full UTF-16 Unicode support, preventing file-not-found errors or Mojibake when dragging files with Korean characters or Roman numerals (`Ⅲ`) into GOM Player.
  - **Double-Click**: Open the file in its default system viewer.
  - **Right-Click Context Menu**: **Open File**, **Open File With...**, **Open Containing Folder in Explorer** (with file pre-selected), **Copy Full Path**, **Copy File Name**, **Copy Folder Path**, and **Select All**.
- 💾 **Persistent User Configuration**: Automatically saves the user's last-used folder, search patterns, extensions, sort order, publisher filters, limit, and live filter query in `~/.filesearch/config` and reloads them on application launch.
- 🎨 **Modern 2026 Dark UI**: Sleek aesthetic with rounded cards, Segoe UI typography, and responsive controls.

---

## 1. Environment Setup

### Activate Virtual Environment

**PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Command Prompt (cmd):**
```cmd
.\.venv\Scripts\activate.bat
```

### Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## 2. Running the Application

Launch directly with Python:

```powershell
.\.venv\Scripts\python.exe FileSearchUtil.py
```
*or (with venv activated)*
```powershell
python FileSearchUtil.py
```

---

## 3. Running Unit Tests

Run all unit tests automatically with test discovery:

```powershell
python -m unittest discover -p "test_*.py"
```

Or run individual test modules:

```powershell
python -m unittest test_app_config.py
python -m unittest test_search_rule.py
python -m unittest test_query_parser.py
python -m unittest test_query_matcher.py
python -m unittest test_extension_filter.py
python -m unittest test_file_item.py
python -m unittest test_metadata_extractor.py
python -m unittest test_file_search_engine.py
python -m unittest test_folder_tree_provider.py
python -m unittest test_windows_drag_drop.py
python -m unittest test_file_search_app.py
```

---

## 4. Project Architecture

The codebase follows the **Single Responsibility Principle (SRP)** with modular OOP classes:

| Source File | Test File | Responsibility |
| :--- | :--- | :--- |
| [`app_config.py`](file:///d:/AProjects/non.work/file.search/app_config.py) | [`test_app_config.py`](file:///d:/AProjects/non.work/file.search/test_app_config.py) | User configuration model & persistence in `~/.filesearch/config` |
| [`folder_tree_provider.py`](file:///d:/AProjects/non.work/file.search/folder_tree_provider.py) | [`test_folder_tree_provider.py`](file:///d:/AProjects/non.work/file.search/test_folder_tree_provider.py) | System & network drive discovery, volume labels, lazy directory listing |
| [`file_explorer_nav.py`](file:///d:/AProjects/non.work/file.search/file_explorer_nav.py) | Integration / App tests | Left-panel File Explorer Treeview component with lazy folder expansion |
| [`search_rule.py`](file:///d:/AProjects/non.work/file.search/search_rule.py) | [`test_search_rule.py`](file:///d:/AProjects/non.work/file.search/test_search_rule.py) | Include/exclude regex rule evaluation |
| [`query_parser.py`](file:///d:/AProjects/non.work/file.search/query_parser.py) | [`test_query_parser.py`](file:///d:/AProjects/non.work/file.search/test_query_parser.py) | Parsing syntax (`*`, `?`, `\|`, `NOT`, `AND`, `,`) |
| [`query_matcher.py`](file:///d:/AProjects/non.work/file.search/query_matcher.py) | [`test_query_matcher.py`](file:///d:/AProjects/non.work/file.search/test_query_matcher.py) | Query rule & exclusion matching against text |
| [`extension_filter.py`](file:///d:/AProjects/non.work/file.search/extension_filter.py) | [`test_extension_filter.py`](file:///d:/AProjects/non.work/file.search/test_extension_filter.py) | Extension parsing & filtering (`+` / `-` / `NOT`) |
| [`file_item.py`](file:///d:/AProjects/non.work/file.search/file_item.py) | [`test_file_item.py`](file:///d:/AProjects/non.work/file.search/test_file_item.py) | Discovered file domain data model |
| [`metadata_extractor.py`](file:///d:/AProjects/non.work/file.search/metadata_extractor.py) | [`test_metadata_extractor.py`](file:///d:/AProjects/non.work/file.search/test_metadata_extractor.py) | Extraction of publication year & publisher |
| [`file_search_engine.py`](file:///d:/AProjects/non.work/file.search/file_search_engine.py) | [`test_file_search_engine.py`](file:///d:/AProjects/non.work/file.search/test_file_search_engine.py) | Recursive directory search & direct folder file listing |
| [`windows_drag_drop.py`](file:///d:/AProjects/non.work/file.search/windows_drag_drop.py) | [`test_windows_drag_drop.py`](file:///d:/AProjects/non.work/file.search/test_windows_drag_drop.py) | Native Windows OLE drag-drop & `WM_DROPFILES` bridge (`ctypes`) |
| [`file_search_app.py`](file:///d:/AProjects/non.work/file.search/file_search_app.py) | [`test_file_search_app.py`](file:///d:/AProjects/non.work/file.search/test_file_search_app.py) | CustomTkinter GUI presentation layer & PanedWindow layout |
| [`FileSearchUtil.py`](file:///d:/AProjects/non.work/file.search/FileSearchUtil.py) | [`test_file_search_util.py`](file:///d:/AProjects/non.work/file.search/test_file_search_util.py) | Application entrypoint & master test suite |

---

## 5. Building a Standalone `.exe` File

You can build a standalone Windows executable (`.exe`) that runs on any Windows machine **without requiring Python to be installed**.

### Pre-Built Binaries
Ready-to-use binaries are located in the `dist/` directory:
- [`dist/FileSearchUtil.exe`](file:///d:/AProjects/non.work/file.search/dist/FileSearchUtil.exe) (Latest release)
- [`dist/FileSearchUtil-20.exe`](file:///d:/AProjects/non.work/file.search/dist/FileSearchUtil-20.exe)

### Quick Build Scripts
- Double-click or run [`build_exe.bat`](file:///d:/AProjects/non.work/file.search/build_exe.bat) (cmd)
- Or run [`build_exe.ps1`](file:///d:/AProjects/non.work/file.search/build_exe.ps1) (PowerShell)

### Manual PyInstaller Build

```powershell
pyinstaller --noconsole --onefile --collect-all customtkinter --name "FileSearchUtil" FileSearchUtil.py
```

### PyInstaller Flags

| Flag | Description |
| :--- | :--- |
| `--noconsole` (or `-w`) | Hides the terminal window so only the GUI appears. |
| `--onefile` (or `-F`) | Bundles everything into a **single `.exe` file**. |
| `--collect-all customtkinter` | **Required**: Bundles CustomTkinter theme assets, fonts, and images. |
| `--name "FileSearchUtil"` | Sets the output executable name. |

---

## Requirements

- Windows 10 / 11 (64-bit)
- Python 3.10+ (tested on Python 3.13)
- `customtkinter>=5.2.0`
- `pillow>=10.0.0`
- `pyinstaller>=6.0.0` (for building `.exe`)
