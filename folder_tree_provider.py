"""Module for enumerating system drives and directories for the file explorer navigation tree."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple

IS_WINDOWS = sys.platform == "win32"


def get_unc_to_drive_map() -> Dict[str, str]:
    """Returns mapping of lowercase UNC share roots to their mapped drive letters."""
    if not IS_WINDOWS:
        return {}
    mapping: Dict[str, str] = {}
    try:
        mpr = ctypes.windll.mpr
        WNetGetConnectionW = mpr.WNetGetConnectionW
        WNetGetConnectionW.restype = wintypes.DWORD
        WNetGetConnectionW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]

        buf = ctypes.create_unicode_buffer(1024)
        buf_size = wintypes.DWORD(1024)
        for c in range(ord("A"), ord("Z") + 1):
            drive = f"{chr(c)}:"
            buf_size.value = 1024
            res = WNetGetConnectionW(drive, buf, ctypes.byref(buf_size))
            if res == 0 and buf.value:
                unc = buf.value.rstrip("\\/").lower()
                mapping[unc] = drive
    except Exception:
        pass
    return mapping


def get_system_drives() -> List[Tuple[str, str]]:
    """Returns a list of (drive_root_path, display_name) for all available logical drives.

    Example output:
        [
            ("C:\\", "OSDISK (C:)"),
            ("D:\\", "Dev (\\\\desktop-5g7gkun\\d) (D:)"),
            ("E:\\", "Data (\\\\desktop-5g7gkun\\e) (E:)"),
            ("G:\\", "USB Drive (G:)"),
        ]
    """
    if not IS_WINDOWS:
        return [("/", "Root (/)")]

    kernel32 = ctypes.windll.kernel32
    drives_mask = kernel32.GetLogicalDrives()
    unc_map = get_unc_to_drive_map()

    drive_types = {
        0: "Drive",
        1: "No Root",
        2: "USB Drive",
        3: "Local Disk",
        4: "Network Drive",
        5: "CD-ROM",
        6: "RAMDisk",
    }

    results: List[Tuple[str, str]] = []

    for i in range(26):
        if drives_mask & (1 << i):
            letter = f"{chr(65 + i)}:"
            root = f"{letter}\\"

            dtype = kernel32.GetDriveTypeW(root)

            vol_buf = ctypes.create_unicode_buffer(260)
            fs_buf = ctypes.create_unicode_buffer(260)
            serial = wintypes.DWORD()
            maxlen = wintypes.DWORD()
            flags = wintypes.DWORD()
            res = kernel32.GetVolumeInformationW(
                root, vol_buf, 260,
                ctypes.byref(serial), ctypes.byref(maxlen), ctypes.byref(flags),
                fs_buf, 260
            )
            vol_name = vol_buf.value.strip() if res else ""

            # Check UNC connection if mapped
            unc: Optional[str] = None
            for u, d in unc_map.items():
                if d.upper() == letter.upper():
                    unc = u
                    break

            label_parts: List[str] = []
            if vol_name:
                label_parts.append(vol_name)
            elif dtype in drive_types:
                label_parts.append(drive_types[dtype])

            if unc:
                label_parts.append(f"({unc})")

            desc = " ".join(label_parts) if label_parts else "Drive"
            display_name = f"{desc} ({letter})"
            results.append((root, display_name))

    return results


def has_subdirectories(folder_path: str) -> bool:
    """Checks if a directory contains at least one accessible subdirectory."""
    try:
        with os.scandir(folder_path) as it:
            for entry in it:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        name = entry.name
                        if not name.startswith("$") and name != "System Volume Information":
                            return True
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError):
        pass
    return False


def list_subdirectories(folder_path: str) -> List[Tuple[str, str, bool]]:
    """Enumerates immediate subdirectories for a given folder path.

    Returns:
        List of (dir_name, full_path, has_children) tuples, sorted alphabetically.
    """
    subdirs: List[Tuple[str, str, bool]] = []
    try:
        with os.scandir(folder_path) as it:
            for entry in it:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        name = entry.name
                        if name.startswith("$") or name == "System Volume Information":
                            continue
                        full_p = entry.path
                        has_kids = has_subdirectories(full_p)
                        subdirs.append((name, full_p, has_kids))
                except (OSError, PermissionError):
                    continue
    except (OSError, PermissionError):
        pass

    subdirs.sort(key=lambda x: x[0].lower())
    return subdirs
