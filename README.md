# FileSearch Pro (FileSearchUtil)

<img width="1175" height="824" alt="image" src="https://github.com/user-attachments/assets/cc627953-0851-4349-8430-9527a8fef8b8" />

A modern, fast, and responsive Desktop File Search & Sort utility built with **CustomTkinter** and **Python 3.13**.

---

## Features

- ⚡ **Fast & Progressive Search**: Real-time results streaming with live progress bar and status indicator.
- 🔍 **Rich Query & Pattern Matching**:
  - `|` (OR Operator): Search for multiple alternative terms (e.g. `ai agent|agents`).
  - `NOT` (Exclusion Operator): Exclude single or multiple keywords (e.g. `ai * pattern NOT apress and addison`, `ai agent NOT agents`, or `ai * pattern NOT apress NOT addison`).
  - `*` : Matches zero or more characters (e.g. `java * pattern` matches `Java 17 Design Patterns`).
  - `?` : Matches any single character (e.g. `python?` matches `python3`).
- 📄 **Extension Inclusion & Exclusion**:
  - Target specific extensions: `pdf, epub, txt`
  - Exclude unwanted extensions using `-` or `NOT`: `pdf, epub, -java` (matches PDF and EPUB files while excluding `.java` files), or `-tmp, -log` (matches all extensions except `.tmp` and `.log`).
- 🛑 **Instant Search Control**:
  - Press <kbd>Enter</kbd> in the search pattern field to instantly clear previous results and run a fresh search.
  - Press <kbd>Esc</kbd> anywhere in the window to halt an active search in real time.
- 🏢 **Publisher & Year Detection**: Automatically detects recognized publishers (O'Reilly, Manning, Wiley, etc.) and release years from file names.
- 📊 **Multi-Criteria Sorting**: Sort by **Published Year**, **Publisher**, **Date Modified**, **Size**, or **File Name**.
- 📐 **Optimized Layout**: Proportional table layout with 65% width allocated to File Name for optimal readability.
- 🎯 **Live Filter Box**: Instant in-memory filtering of search results with wildcard support.
- 🖱️ **Windows Integration**:
  - Double-click any row to open the file in its default system viewer.
  - Right-click context menu: **Open File**, **Open Containing Folder in Explorer** (with file selected), **Copy Full Path**, **Copy File Name**.
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

Run the test suite to verify search logic, boolean expressions, pattern compilation, and metadata extraction:

```powershell
.\.venv\Scripts\python.exe -m unittest test_file_search_util.py
```

---

## 4. Building a Standalone `.exe` File

You can build a standalone Windows executable (`.exe`) that runs on any Windows machine **without requiring Python to be installed**.

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

- Python 3.10+ (tested on Python 3.13)
- `customtkinter>=5.2.0`
- `pillow>=10.0.0`
- `pyinstaller>=6.0.0` (for building `.exe`)
