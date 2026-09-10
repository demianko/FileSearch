# FileSearch Pro — User Manual

Welcome to the **FileSearch Pro (FileSearchUtil)** User Manual. This guide provides comprehensive, step-by-step instructions on using all the features of FileSearch Pro, from basic file searching and folder browsing to advanced query syntax, native Windows drag-and-drop, and keyboard shortcuts.

---

## Table of Contents

1. [Introduction & Overview](#1-introduction--overview)
2. [Interface Layout](#2-interface-layout)
3. [File Explorer & Navigation Panel (Left Pane)](#3-file-explorer--navigation-panel-left-pane)
4. [Search Controls & Query Syntax (Right Pane)](#4-search-controls--query-syntax-right-pane)
   - [Directory Selection](#directory-selection)
   - [Pattern Matching Syntax (`*`, `?`, `,`, `|`, `NOT`)](#pattern-matching-syntax)
   - [Extension Inclusion & Exclusion](#extension-inclusion--exclusion)
   - [Publisher & Year Detection](#publisher--year-detection)
   - [Result Limits](#result-limits)
   - [Sorting Options](#sorting-options)
   - [Stopping an Active Search](#stopping-an-active-search)
5. [Search Results Table](#5-search-results-table)
   - [Folder & File Distinctions](#folder--file-distinctions)
   - [Two-Way Navigation Sync](#two-way-navigation-sync)
   - [Opening Files & Folders](#opening-files--folders)
   - [Live In-Memory Filter](#live-in-memory-filter)
6. [Windows Explorer Integration & File Operations](#6-windows-explorer-integration--file-operations)
   - [Copying Files & Folders (`Ctrl+C`)](#copying-files--folders-ctrlc)
   - [Renaming Files & Folders (`F2`)](#renaming-files--folders-f2)
   - [Universal Drag-and-Drop (OLE/COM)](#universal-drag-and-drop-olecom)
   - [GOM Player & Media Player Unicode Support](#gom-player--media-player-unicode-support)
   - [Right-Click Context Menu](#right-click-context-menu)
7. [Keyboard Shortcuts Reference](#7-keyboard-shortcuts-reference)
8. [Configuration & Automatic Persistence](#8-configuration--automatic-persistence)
9. [Frequently Asked Questions & Troubleshooting](#9-frequently-asked-questions--troubleshooting)

---

## 1. Introduction & Overview

**FileSearch Pro** is a high-performance desktop file navigation, search, and management tool designed for Windows. It combines the rapid search capabilities of modern indexing tools with the tactile organization of the classic Windows File Explorer.

### Key Highlights
- **Instant Folder Browsing**: Browse drive roots, network shares, and nested directories without waiting for slow search indexing.
- **Deep Pattern Searching**: Expressive search queries supporting wildcards, OR logic, and multi-term exclusions.
- **Native Windows Drag & Drop**: Drag files directly from your search results into Windows Explorer, GOM Player, VLC, browser upload forms, or code editors.
- **Full Clipboard Integration**: Native `CF_HDROP` copy support allows pasting physical files into File Explorer (<kbd>Ctrl+V</kbd>) or file paths into text editors.
- **In-Place File Renaming**: Quick <kbd>F2</kbd> rename dialog with filename pre-selection and collision safeguards.
- **Unicode Resilient**: Full UTF-16 compatibility supporting Korean, Japanese, Chinese, accented characters, emojis, and Roman numerals (e.g. `Ⅲ`).
- **Zero-Install Portable Executable**: Runs as a single standalone `.exe` without requiring Python, administrative rights, or external dependencies.

---

## 2. Interface Layout

The application window is organized into two primary workspaces separated by an adjustable vertical divider (sash):

```
+-----------------------------------------------------------------------------------------+
| FileSearch Pro                                                                 -  [ ]  X|
+--------------------------+--------------------------------------------------------------+
| 📁 File Explorer         | 📁 Directory:  [ E:\ztemp\download                 ] [Browse]|
| [↻] Refresh              | 🔍 Patterns:   [ *.mp4, *.mkv NOT sample          ] [Search]|
+--------------------------+ 📄 Extensions: [ mp4, mkv                         ] [Stop]  |
| 🖴 Local Disk (C:)       | Limit: [ 500 ]  Publisher: [ All ]  Sort: [ Date Modified ↓ ] |
| 🖴 Data (D:)             +--------------------------------------------------------------+
| 🖴 Media (E:)            | 📁 Name           | 📅 Date Modified | 💾 Size  | 📂 Full Path |
|   ├── music              +-------------------+------------------+----------+--------------+
|   └── download           | 📁 classical      | 2026-09-08 14:10 | Folder   | E:\ztemp\... |
|       ├── classical      | 📁 movies         | 2026-09-08 11:22 | Folder   | E:\ztemp\... |
|       └── movies         | 🎬 The.Godfather..| 2026-09-07 19:45 | 2.14 GB  | E:\ztemp\... |
|                          | 🎵 Hornpipe.mp3   | 2026-09-06 08:30 | 8.42 MB  | E:\ztemp\... |
|                          +--------------------------------------------------------------+
|                          | Filter results: [ search within results...       ] 4 items   |
+--------------------------+--------------------------------------------------------------+
```

1. **Left Pane (File Explorer & Navigation)**:
   - Displays all local drives, external drives, and mapped network shares.
   - Provides an expandable tree hierarchy for fast, non-recursive directory browsing.
2. **Right Pane (Search Workspace & Results)**:
   - **Search Controls Card**: Specify directory, search patterns, file extensions, result limits, and sorting criteria.
   - **Results Table**: Displays matching files and subfolders with metadata (Date Modified, Publisher, Year, Size, Path).
   - **Status & Live Filter Bar**: Real-time progress feedback, active result counts, and an instant filter input.

> [!TIP]
> **Resize the Divider**: Hover your mouse over the vertical border between the left explorer pane and the right search panel. Click and drag the sash left or right to customize your workspace layout.

---

## 3. File Explorer & Navigation Panel (Left Pane)

The left navigation panel functions like the Windows Explorer sidebar:

### Drive & Network Share Discovery
- When FileSearch Pro launches, it automatically detects all mounted system drives (`C:\`, `D:\`, `E:\`, etc.) and mapped network drives (`Z:\`, etc.).
- Drives display their volume labels (e.g. `Local Disk (C:)`, `Backup (D:)`, `Media (E:)`).
- Special protected system folders (`$RECYCLE.BIN`, `System Volume Information`) are filtered out automatically to keep your tree clean.

### Expanding & Browsing Folders
- Click the **`>`** arrow next to any drive or folder to expand its subdirectories.
- Subdirectories are loaded **lazily** on demand, ensuring lightning-fast performance even across massive file systems or network shares.
- Click the **`↻` (Refresh)** button at the top of the left pane anytime to re-scan drives and folders without losing your current selection.

### Selecting a Folder
- Click any folder in the left pane:
  1. The folder's path is immediately loaded into the **"📁 Directory:"** input on the right.
  2. The search results table on the right instantly displays all **direct subfolders** (marked with `📁 `) and **direct files** inside that folder.
  3. This browsing mode is strictly **non-recursive**, providing instant, clean directory contents without digging into hundreds of subfolders.

---

## 4. Search Controls & Query Syntax (Right Pane)

The top card of the right pane provides search parameters.

### Directory Selection
- **Text Box**: Displays the active target directory. You can edit or paste a path directly.
- **`Browse...` Button**: Opens the standard Windows folder picker dialog.
- Selecting a folder in the left tree or clicking a folder row in search results updates this field automatically.

---

### Pattern Matching Syntax

The **"🔍 Patterns:"** input supports query syntax:

#### 1. Basic Substring Search
- `report` — Matches any file containing "report" anywhere in its name (case-insensitive).

#### 2. Wildcards (`*` and `?`)
- `*` : Matches zero or more characters.
  - `java * pattern` — Matches `Java 17 Design Patterns.pdf` or `java_advanced_patterns.epub`.
  - `*.mp4` — Matches any file ending with `.mp4`.
- `?` : Matches exactly one single character.
  - `test?` — Matches `test1`, `testA`, but not `test12`.

#### 3. Comma `,` (OR Operator across Patterns)
Use commas to match files meeting **any** of multiple search terms:
- `python, rust, golang` — Finds all files containing "python" **OR** "rust" **OR** "golang".
- `*.pdf, *.epub, *.mobi` — Finds documents in any of the three formats.

#### 4. Pipe `|` (OR Operator within a Pattern)
Use pipe characters to specify alternate terms inside a pattern:
- `ai agent|agents` — Matches both `ai agent` and `ai agents`.
- `docker|kubernetes guide` — Matches `docker guide` or `kubernetes guide`.

#### 5. `NOT` (Exclusion Operator)
Exclude files that match unwanted terms. You can chain multiple `NOT` conditions:
- `machine learning NOT deep` — Matches files with "machine learning", but excludes any containing "deep".
- `ai * pattern NOT apress and addison` — Matches "ai * pattern" while excluding files mentioning "apress" or "addison".
- `tutorial NOT video NOT draft` — Matches "tutorial" but excludes any file mentioning "video" or "draft".

---

### Extension Inclusion & Exclusion

The **"📄 Extensions:"** input allows filtering by file types regardless of what you type in the search patterns field:

- **Target Specific Extensions**:
  - `pdf, epub` — Only returns `.pdf` and `.epub` files.
  - `mp4, mkv, avi` — Only returns video files.
- **Exclude Extensions (`-` or `NOT`)**:
  - `pdf, epub, -mobi` — Returns PDF and EPUB files, explicitly excluding MOBI files.
  - `-tmp, -log, -bak` — Returns all file types **except** `.tmp`, `.log`, and `.bak` files.

---

### Publisher & Year Detection

FileSearch Pro includes an automated metadata extractor that parses file names:
- **Recognized Publishers**: Automatically tags recognized publishers including:
  - *O'Reilly*, *Manning*, *Wiley*, *Packt*, *Addison-Wesley*, *Apress*, *No Starch Press*, *McGraw-Hill*, *Pragmatic Bookshelf*, *Microsoft Press*, and more.
- **Publisher Dropdown**: Select a specific publisher from the dropdown to restrict results to books or materials from that publisher.
- **Year Detection**: Automatically extracts publication or release years (e.g. `2024`, `1990`) from file titles.

---

### Result Limits
- **`Limit:` Field**: Restricts the maximum number of results returned (e.g. `100`, `500`, `1000`).
- Leave the limit field blank to search without any limit.

---

### Sorting Options

Use the **"Sort By:"** dropdown to reorder results instantly:
- **Date Modified (Newest First / Oldest First)**: Ideal for finding recent downloads or projects.
- **Published Year (Newest First / Oldest First)**: Groups books and media by release year.
- **Publisher**: Sorts alphabetically by publishing house.
- **File Name (A-Z / Z-A)**: Alphabetical sort.
- **Size (Largest First / Smallest First)**: Ideal for identifying large video files or freeing up disk space.

> [!NOTE]
> When sorting, **subfolders always remain grouped at the top** of the list (sorted alphabetically), followed by files sorted by your chosen criteria.

---

### Stopping an Active Search

Deep recursive searches across large drives can be stopped at any moment:
- Click the **`Stop`** button next to Search.
- Or press the <kbd>Esc</kbd> key anywhere in the application.
- All results found up to the moment you stopped remain visible in the table.

---

## 5. Search Results Table

The results table displays matching items in clear, resizable columns:

| Column | Description |
| :--- | :--- |
| **📁 Name** | The file or folder name. Folders are highlighted with a `📁 ` prefix. |
| **📅 Date Modified** | Last modification timestamp (`YYYY-MM-DD HH:MM`). |
| **🏢 Publisher** | Detected publisher (e.g. `O'Reilly`, `Manning`, or `Folder` for directories). |
| **📆 Year** | Extracted release/publication year (or `-` for folders). |
| **💾 Size** | Human-readable size (e.g. `14.2 MB`, `2.14 GB`, or `Folder`). |
| **📂 Full Path** | The absolute path on your storage drive. |

### Folder & File Distinctions
- **Subfolders** appear first with a folder icon: `📁 download`.
- **Files** appear below the folder section, showing their individual file sizes and extensions.

### Two-Way Navigation Sync
- **Single-Clicking a Folder**:
  - Automatically updates the **"📁 Directory:"** input box.
  - Automatically expands and reveals the folder in the left **File Explorer tree**.
- **Double-Clicking or Pressing <kbd>Enter</kbd> on a Folder**:
  - Navigates directly inside the folder, instantly updating the search results to show that folder's contents.

### Opening Files & Folders
- **Double-Click** or press <kbd>Enter</kbd> on any file to launch it in your default Windows application (e.g. PDF viewer, media player, or text editor).
- Select multiple files and press <kbd>Enter</kbd> to open all selected files simultaneously.

### Live In-Memory Filter
At the bottom of the window, the **"Filter results..."** input allows you to filter the current table without re-running a disk search:
- Type any word, extension, or wildcard pattern.
- The table filters rows in real time as you type.
- The badge on the right shows how many items match (e.g. `12 / 150 items`).

---

## 6. Windows Explorer Integration & File Operations

FileSearch Pro integrates with the Windows shell.

### Copying Files & Folders (`Ctrl+C`)

You can copy items directly out of the search results table:
1. Select one or more files or folders in the table (use <kbd>Ctrl+Click</kbd> or <kbd>Shift+Click</kbd> for multi-select, or <kbd>Ctrl+A</kbd> for all).
2. Press <kbd>Ctrl+C</kbd> or right-click and choose **"📄 Copy"**.
3. **What happens under the hood**:
   - **Native File Drop (`CF_HDROP`)**: The actual physical files and folders are placed onto the Windows clipboard. You can switch to **Windows File Explorer**, your **Desktop**, or a folder on a flash drive and press <kbd>Ctrl+V</kbd> to paste the files.
   - **Text Clipboard (`CF_UNICODETEXT`)**: At the same time, the full file paths are stored as text. If you switch to **Notepad**, **VS Code**, an email, or chat application and press <kbd>Ctrl+V</kbd>, the path strings will paste cleanly.

---

### Renaming Files & Folders (`F2`)

Renaming items directly in place:
1. Select the file or folder you wish to rename.
2. Press <kbd>F2</kbd> or right-click and select **"✏️ Rename"**.
3. A modal rename dialog appears:
   - For **files**, the base name is automatically highlighted while preserving the extension (e.g. in `document.pdf`, only `document` is selected).
   - For **folders**, the entire folder name is selected.
4. Type the new name and press <kbd>Enter</kbd> (or click **Rename**).
5. **Safety Features**:
   - Blocks illegal Windows characters (`\ / : * ? " < > |`).
   - Prevents accidental overwrites if a file with the target name already exists.
   - Automatically refreshes the table row, internal cache, and the left File Explorer tree.

---

### Universal Drag-and-Drop (OLE/COM)

Drag files directly from FileSearch Pro into other applications:
- **How to use**: Click and hold the left mouse button on any file or group of selected files in the results table, drag your cursor over the target window, and release.
- **Supported Drop Targets**:
  - **Windows File Explorer & Desktop** (copies or moves files).
  - **Web Browsers** (Chrome, Firefox, Edge file upload zones, Gmail attachments, Google Drive).
  - **Code Editors & IDEs** (VS Code, JetBrains, Sublime Text).
  - **Chat Applications** (Slack, Discord, Microsoft Teams, Telegram).

---

### GOM Player & Media Player Unicode Support

Many media players (notably GOM Player) suffer from a known Windows bug where dropping files with non-ASCII characters (such as Korean syllables, Chinese characters, or Roman numerals like `Ⅲ`) causes a `"File Not Found"` error or garbled Mojibake characters.

FileSearch Pro resolves this through an internal **Win32 `WM_DROPFILES` bridge**:
- Detects the target media player window under the cursor upon release.
- Automatically constructs a native UTF-16 wide-character structure (`fWide = 1`).
- Delivers the exact Unicode path directly to the player.
- **Result**: Files with titles such as:
  - `The.Godfather.Part.Ⅲ.1990.1080p.mp4` (Roman numeral `Ⅲ`)
  - `Water Music Suite ('수상음악' 중 호른파이프).mp3` (Korean syllables)
  - `완벽한_폼을_위한_코치_가이드.mp4`
  play seamlessly upon drag-and-drop.

---

### Right-Click Context Menu

Right-clicking any selected item in the search results table opens the context menu:

| Context Menu Item | Shortcut | Description |
| :--- | :--- | :--- |
| **📂 Open Folder** / **▶ Open File** | <kbd>Enter</kbd> | Navigates into folder or opens file with default application. |
| **Open File With...** | — | Opens the standard Windows "How do you want to open this file?" dialog. |
| **Open in Explorer** | — | Opens Windows File Explorer with the specific item highlighted. |
| **📄 Copy** | <kbd>Ctrl+C</kbd> | Copies items as `CF_HDROP` files and plain text paths. |
| **✏️ Rename** | <kbd>F2</kbd> | Opens the in-place rename dialog. |
| **Copy Full Path** | — | Copies the absolute path (e.g. `D:\docs\manual.pdf`) to clipboard. |
| **Copy Name** | — | Copies just the file or folder name (e.g. `manual.pdf`). |
| **Copy Folder Path** | — | Copies the parent folder path (e.g. `D:\docs`). |
| **Select All** | <kbd>Ctrl+A</kbd> | Highlights all items in the results table. |

---

## 7. Keyboard Shortcuts Reference

| Shortcut | Context | Action |
| :--- | :--- | :--- |
| <kbd>F2</kbd> | Results Table | **Rename** selected file or folder. |
| <kbd>Ctrl+C</kbd> | Results Table | **Copy** selected item(s) to Windows Clipboard (as files and text). |
| <kbd>Ctrl+A</kbd> | Results Table | **Select All** items in the results table. |
| <kbd>Enter</kbd> | Search / Extension Fields | Immediately execute a fresh search. |
| <kbd>Enter</kbd> | Results Table | **Open file** or **navigate into folder**. |
| <kbd>Double-Click</kbd> | Results Table | **Open file** or **navigate into folder**. |
| <kbd>Esc</kbd> | Anywhere | **Stop** an in-progress search immediately. |
| <kbd>Ctrl+Click</kbd> | Results Table | Add/remove individual items to/from selection. |
| <kbd>Shift+Click</kbd> | Results Table | Select a contiguous range of items. |

---

## 8. Configuration & Automatic Persistence

FileSearch Pro remembers your preferred settings across sessions:

- **Saved Settings**:
  - Last-used root directory
  - Search patterns & query history
  - Extension filters
  - Max results limit
  - Selected publisher filter
  - Sort order and column direction
  - Left/right pane split ratio
- **Storage Location**:
  - Settings are saved automatically upon exit to:
    ```
    %USERPROFILE%\.filesearch\config
    ```
  - Settings are stored in a standard JSON format that can be inspected or backed up.

---

## 9. Frequently Asked Questions & Troubleshooting

### Q: Why do subfolders stay at the top when I sort by size or date?
**A:** This mirrors standard operating system behavior (like Windows File Explorer and macOS Finder). Keeping subfolders anchored at the top ensures you can continue navigating directory structures without folder rows getting scattered throughout thousands of sorted files.

### Q: Can I search across an entire drive like `C:\` or `D:\`?
**A:** Yes! Select the root drive (e.g. `C:\`) in the left navigation panel or browse to it. Enter your search pattern and press <kbd>Enter</kbd>. If you wish to halt the search at any point, simply press <kbd>Esc</kbd>.

### Q: Dragging into an application running as Administrator doesn't respond. Why?
**A:** Windows security (User Interface Privilege Isolation / UIPI) prevents non-elevated applications from sending drag-and-drop window messages to elevated (Administrator) windows. If your target app (e.g. an elevated text editor or command prompt) is running as Administrator, run FileSearch Pro as Administrator as well.

### Q: How do I exclude multiple terms at once?
**A:** You can combine terms using `NOT`:
- `ai * pattern NOT apress NOT wiley`
- `music NOT live and acoustic`

### Q: Does FileSearch Pro modify or delete my files?
**A:** FileSearch Pro only reads your files for indexing, opening, and copying. The only modifying action is the explicit **Rename (<kbd>F2</kbd>)** command, which requests your direct input and checks for name conflicts before executing.

---

*FileSearch Pro — Built with Python 3.13, CustomTkinter, and Windows Win32 API.*
