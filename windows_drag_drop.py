"""Windows OLE Drag and Drop helper for exporting files from GUI to Windows Explorer / external apps.

Implements native IDropSource and IDataObject COM interfaces via ctypes so no external
third-party dependencies (like pywin32) are required. Fully supports CF_HDROP (standard
file drops for Explorer, Chromium, Electron, VS Code, Gemini, browsers, desktop, etc.)
as well as text and URL clipboard formats.
"""

from __future__ import annotations

import atexit
import os
from pathlib import Path
import re
import sys
from typing import List, Sequence, Union
import unicodedata

FilePathType = Union[str, Path]

# Platform check: only Windows supports OLE drag & drop through these APIs
IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import ctypes
    from ctypes import (
        HRESULT,
        POINTER,
        Structure,
        WINFUNCTYPE,
        byref,
        c_long,
        c_ubyte,
        c_ulong,
        c_ushort,
        c_void_p,
        cast,
        memmove,
        pointer,
        sizeof,
        wintypes,
    )

    class GUID(Structure):
        _fields_ = [
            ("Data1", c_ulong),
            ("Data2", c_ushort),
            ("Data3", c_ushort),
            ("Data4", c_ubyte * 8),
        ]

        def matches(self, other: GUID) -> bool:
            return (
                self.Data1 == other.Data1
                and self.Data2 == other.Data2
                and self.Data3 == other.Data3
                and bytes(self.Data4) == bytes(other.Data4)
            )

    # COM Interface IDs
    IID_IUnknown = GUID(
        0x00000000,
        0x0000,
        0x0000,
        (c_ubyte * 8)(0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46),
    )
    IID_IDataObject = GUID(
        0x0000010E,
        0x0000,
        0x0000,
        (c_ubyte * 8)(0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46),
    )
    IID_IDropSource = GUID(
        0x00000121,
        0x0000,
        0x0000,
        (c_ubyte * 8)(0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46),
    )

    # Memory and OLE Constants
    GHND = 0x0042  # GMEM_MOVEABLE | GMEM_ZEROINIT
    CF_TEXT = 1
    CF_UNICODETEXT = 13
    CF_HDROP = 15
    TYMED_HGLOBAL = 1

    DRAGDROP_S_DROP = 0x00040100
    DRAGDROP_S_CANCEL = 0x00040101
    DRAGDROP_S_USEDEFAULTCURSORS = 0x00040102

    MK_LBUTTON = 0x0001
    MK_RBUTTON = 0x0002

    DROPEFFECT_NONE = 0
    DROPEFFECT_COPY = 1
    DROPEFFECT_MOVE = 2
    DROPEFFECT_LINK = 4

    DV_E_FORMATETC = -2147221404  # 0x80040064
    DATA_S_SAMEFORMATETC = 0x00040130
    E_NOTIMPL = -2147467263  # 0x80004001
    E_NOINTERFACE = -2147467262  # 0x80004002
    OLE_E_ADVISENOTSUPPORTED = -2147221501  # 0x80040003

    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    shell32 = ctypes.windll.shell32
    ole32 = ctypes.windll.ole32

    # Initialize OLE subsystem
    ole32.OleInitialize(None)

    # Register additional Windows clipboard formats
    CF_FILENAME = user32.RegisterClipboardFormatW("FileName")
    CF_FILENAMEW = user32.RegisterClipboardFormatW("FileNameW")
    CF_URLW = user32.RegisterClipboardFormatW("UniformResourceLocatorW")

    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalLock.restype = c_void_p
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]

    kernel32.CreateHardLinkW.restype = wintypes.BOOL
    kernel32.CreateHardLinkW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, c_void_p]
    kernel32.DefineDosDeviceW.restype = wintypes.BOOL
    kernel32.DefineDosDeviceW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR]
    kernel32.GetLogicalDrives.restype = wintypes.DWORD
    kernel32.GetLogicalDrives.argtypes = []
    kernel32.SetFileAttributesW.restype = wintypes.BOOL
    kernel32.SetFileAttributesW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD]

    shell32.SHCreateStdEnumFmtEtc.restype = HRESULT
    shell32.SHCreateStdEnumFmtEtc.argtypes = [wintypes.UINT, c_void_p, POINTER(c_void_p)]

    shell32.DragQueryFileW.restype = wintypes.UINT
    shell32.DragQueryFileW.argtypes = [c_void_p, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]

    class POINT(Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

    user32.GetCursorPos.restype = wintypes.BOOL
    user32.GetCursorPos.argtypes = [POINTER(POINT)]
    user32.WindowFromPoint.restype = wintypes.HWND
    user32.WindowFromPoint.argtypes = [POINT]
    user32.GetAncestor.restype = wintypes.HWND
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetClassNameW.restype = ctypes.c_int
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.PostMessageW.restype = wintypes.BOOL
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.CloseClipboard.argtypes = []

    class DROPFILES(Structure):
        _fields_ = [
            ("pFiles", wintypes.DWORD),
            ("pt", POINT),
            ("fNC", wintypes.BOOL),
            ("fWide", wintypes.BOOL),
        ]

    class FORMATETC(Structure):
        _fields_ = [
            ("cfFormat", c_ushort),
            ("ptd", c_void_p),
            ("dwAspect", wintypes.DWORD),
            ("lindex", wintypes.LONG),
            ("tymed", wintypes.DWORD),
        ]

    class STGMEDIUM(Structure):
        _fields_ = [
            ("tymed", wintypes.DWORD),
            ("hGlobal", wintypes.HGLOBAL),
            ("pUnkForRelease", c_void_p),
        ]

    # Data builders for clipboard formats (pure UTF-16 Unicode to prevent lossy ANSI '??' replacement)
    def _create_hdrop_buffer(file_paths: List[str]) -> wintypes.HGLOBAL:
        header_size = sizeof(DROPFILES)
        encoded_paths = b"".join(p.encode("utf-16le") + b"\x00\x00" for p in file_paths) + b"\x00\x00"
        total_size = header_size + len(encoded_paths)
        hmem = kernel32.GlobalAlloc(GHND, total_size)
        ptr = kernel32.GlobalLock(hmem)
        try:
            df = DROPFILES()
            df.pFiles = header_size
            df.pt = POINT(0, 0)
            df.fNC = 0
            df.fWide = 1
            memmove(ptr, byref(df), header_size)
            memmove(ptr + header_size, encoded_paths, len(encoded_paths))
        finally:
            kernel32.GlobalUnlock(hmem)
        return hmem

    def _create_unicodetext_buffer(file_paths: List[str]) -> wintypes.HGLOBAL:
        text = "\r\n".join(file_paths)
        encoded = text.encode("utf-16le") + b"\x00\x00"
        hmem = kernel32.GlobalAlloc(GHND, len(encoded))
        ptr = kernel32.GlobalLock(hmem)
        try:
            memmove(ptr, encoded, len(encoded))
        finally:
            kernel32.GlobalUnlock(hmem)
        return hmem

    _active_dos_drives: dict[str, str] = {}
    _created_hard_links: List[str] = []

    def _cleanup_drag_resources():
        global _active_dos_drives, _created_hard_links
        for drive_letter in list(_active_dos_drives.values()):
            try:
                kernel32.DefineDosDeviceW(2, drive_letter, None)
            except Exception:
                pass
        _active_dos_drives.clear()
        for link in list(_created_hard_links):
            try:
                if os.path.exists(link):
                    os.remove(link)
            except Exception:
                pass
        _created_hard_links.clear()

    atexit.register(_cleanup_drag_resources)

    def _get_or_create_dos_drive_for_dir(target_dir: str) -> str:
        global _active_dos_drives
        target_norm = os.path.normpath(target_dir).lower()
        if target_norm in _active_dos_drives:
            return _active_dos_drives[target_norm]

        drives_mask = kernel32.GetLogicalDrives()
        for i in range(25, 3, -1):  # Z: down to D:
            if not (drives_mask & (1 << i)):
                drive_letter = f"{chr(ord('A') + i)}:"
                res = kernel32.DefineDosDeviceW(0, drive_letter, target_dir)
                if res:
                    _active_dos_drives[target_norm] = drive_letter
                    return drive_letter
        return ""

    def _get_ascii_safe_path(p: str) -> str:
        """Returns a path pointing to the file that can be cleanly decoded by ANSI-only media players like GOM Player."""
        # 1. Already encodable in the Windows ANSI code page (mbcs/ASCII)?
        try:
            p.encode("mbcs")
            return p
        except (UnicodeEncodeError, LookupError):
            pass

        # 2. Try Win32 8.3 short path
        buf = ctypes.create_unicode_buffer(1024)
        res = kernel32.GetShortPathNameW(p, buf, 1024)
        if res > 0 and buf.value:
            try:
                buf.value.encode("mbcs")
                return buf.value
            except (UnicodeEncodeError, LookupError):
                pass

        # 3. If on a drive with a root, try an NTFS hard link in a hidden cache directory on the same volume
        drive, _ = os.path.splitdrive(p)
        if drive and os.path.exists(drive + "\\"):
            cache_dir = os.path.join(drive + "\\", ".fsu_drag_cache")
            try:
                os.makedirs(cache_dir, exist_ok=True)
                kernel32.SetFileAttributesW(cache_dir, 0x02)  # FILE_ATTRIBUTE_HIDDEN
                filename = os.path.basename(p)
                try:
                    filename.encode("mbcs")
                    link_name = filename
                except (UnicodeEncodeError, LookupError):
                    name_no_ext, ext = os.path.splitext(filename)
                    norm = unicodedata.normalize("NFKD", name_no_ext)
                    ascii_name = norm.encode("ascii", errors="replace").decode("ascii").replace("?", "_")
                    ascii_name = re.sub(r"_+", "_", ascii_name).strip("._ ")
                    if not ascii_name:
                        ascii_name = f"media_{abs(hash(p)) % 10000000}"
                    link_name = f"{ascii_name}{ext}"
                link_path = os.path.join(cache_dir, link_name)
                if os.path.exists(link_path):
                    return link_path
                if kernel32.CreateHardLinkW(link_path, p, None):
                    _created_hard_links.append(link_path)
                    return link_path
            except Exception:
                pass

        # 4. Try DefineDosDeviceW to map a virtual drive to the directory if the filename itself is encodable
        dirname, filename = os.path.split(p)
        try:
            filename.encode("mbcs")
            dos_drive = _get_or_create_dos_drive_for_dir(dirname)
            if dos_drive:
                mapped_path = f"{dos_drive}\\{filename}"
                mapped_path.encode("mbcs")
                return mapped_path
        except Exception:
            pass

        # 5. Fallback: lossy mbcs replacement
        try:
            return p.encode("mbcs", errors="replace").decode("mbcs")
        except Exception:
            return p

    def _create_text_buffer(file_paths: List[str]) -> wintypes.HGLOBAL:
        safe_paths = [_get_ascii_safe_path(p) for p in file_paths]
        text = "\r\n".join(safe_paths)
        try:
            encoded = text.encode("mbcs") + b"\x00"
        except Exception:
            encoded = text.encode("utf-8", errors="replace") + b"\x00"

        hmem = kernel32.GlobalAlloc(GHND, len(encoded))
        ptr = kernel32.GlobalLock(hmem)
        try:
            memmove(ptr, encoded, len(encoded))
        finally:
            kernel32.GlobalUnlock(hmem)
        return hmem

    def _create_filename_buffer(file_paths: List[str]) -> wintypes.HGLOBAL:
        encoded = file_paths[0].encode("utf-16le") + b"\x00\x00"
        hmem = kernel32.GlobalAlloc(GHND, len(encoded))
        ptr = kernel32.GlobalLock(hmem)
        try:
            memmove(ptr, encoded, len(encoded))
        finally:
            kernel32.GlobalUnlock(hmem)
        return hmem

    def _create_filename_ansi_buffer(file_paths: List[str]) -> wintypes.HGLOBAL:
        safe_path = _get_ascii_safe_path(file_paths[0])
        try:
            encoded = safe_path.encode("mbcs") + b"\x00"
        except Exception:
            encoded = safe_path.encode("ascii", errors="replace") + b"\x00"
        hmem = kernel32.GlobalAlloc(GHND, len(encoded))
        ptr = kernel32.GlobalLock(hmem)
        try:
            memmove(ptr, encoded, len(encoded))
        finally:
            kernel32.GlobalUnlock(hmem)
        return hmem

    def _create_urlw_buffer(file_paths: List[str]) -> wintypes.HGLOBAL:
        uri = Path(file_paths[0]).as_uri()
        encoded = uri.encode("utf-16le") + b"\x00\x00"
        hmem = kernel32.GlobalAlloc(GHND, len(encoded))
        ptr = kernel32.GlobalLock(hmem)
        try:
            memmove(ptr, encoded, len(encoded))
        finally:
            kernel32.GlobalUnlock(hmem)
        return hmem

    # Full set of clipboard formats for maximum compatibility with Explorer, GOM Player,
    # browsers, text editors, and media players.
    SUPPORTED_FORMATS = [
        (CF_HDROP, _create_hdrop_buffer),
        (CF_UNICODETEXT, _create_unicodetext_buffer),
        (CF_TEXT, _create_text_buffer),
        (CF_FILENAMEW, _create_filename_buffer),
        (CF_FILENAME, _create_filename_ansi_buffer),
        (CF_URLW, _create_urlw_buffer),
    ]

    SUPPORTED_FMT_ARRAY = (FORMATETC * len(SUPPORTED_FORMATS))(
        *[FORMATETC(cf, None, 1, -1, TYMED_HGLOBAL) for cf, _ in SUPPORTED_FORMATS]
    )

    # ------------------ IDropSource Implementation ------------------
    QueryInterfaceProto = WINFUNCTYPE(HRESULT, c_void_p, c_void_p, c_void_p)
    AddRefProto = WINFUNCTYPE(c_ulong, c_void_p)
    ReleaseProto = WINFUNCTYPE(c_ulong, c_void_p)
    QueryContinueDragProto = WINFUNCTYPE(HRESULT, c_void_p, wintypes.BOOL, wintypes.DWORD)
    GiveFeedbackProto = WINFUNCTYPE(HRESULT, c_void_p, wintypes.DWORD)

    def _drop_source_qi(this, riid_ptr, ppv_ptr):
        if not riid_ptr or not ppv_ptr:
            return E_NOINTERFACE
        guid = cast(riid_ptr, POINTER(GUID)).contents
        if guid.matches(IID_IUnknown) or guid.matches(IID_IDropSource):
            cast(ppv_ptr, POINTER(c_void_p))[0] = this
            return 0
        cast(ppv_ptr, POINTER(c_void_p))[0] = None
        return E_NOINTERFACE

    def _drop_source_addref(this):
        return 1

    def _drop_source_release(this):
        return 1

    def _post_wm_dropfiles(hwnd: wintypes.HWND, file_paths: List[str]) -> bool:
        if not hwnd or not file_paths:
            return False
        encoded = ("\x00".join(file_paths) + "\x00\x00").encode("utf-16le")
        header_size = sizeof(DROPFILES)
        total_size = header_size + len(encoded)
        hmem = kernel32.GlobalAlloc(GHND, total_size)
        if not hmem:
            return False
        ptr = kernel32.GlobalLock(hmem)
        if not ptr:
            return False
        try:
            df = DROPFILES()
            df.pFiles = header_size
            df.pt = POINT(0, 0)
            df.fNC = 0
            df.fWide = 1
            memmove(ptr, byref(df), header_size)
            memmove(ptr + header_size, encoded, len(encoded))
        finally:
            kernel32.GlobalUnlock(hmem)
        return bool(user32.PostMessageW(hwnd, 0x0233, hmem, 0))

    def _drop_source_query_continue_drag(this, f_escape_pressed, grf_key_state):
        if f_escape_pressed:
            return DRAGDROP_S_CANCEL
        if not (grf_key_state & (MK_LBUTTON | MK_RBUTTON)):
            # Check if dropped over GOM Player window
            pt = POINT()
            if user32.GetCursorPos(byref(pt)):
                target = user32.WindowFromPoint(pt)
                if target:
                    root = user32.GetAncestor(target, 2) or target
                    cname = ctypes.create_unicode_buffer(256)
                    user32.GetClassNameW(root, cname, 256)
                    if cname.value == "GomPlayer1.x" or "gom" in cname.value.lower():
                        if _active_drag_files:
                            _post_wm_dropfiles(root, _active_drag_files)
                        return DRAGDROP_S_CANCEL
            return DRAGDROP_S_DROP
        return 0  # S_OK

    def _drop_source_give_feedback(this, dw_effect):
        return DRAGDROP_S_USEDEFAULTCURSORS

    class IDropSourceVtbl(Structure):
        _fields_ = [
            ("QueryInterface", QueryInterfaceProto),
            ("AddRef", AddRefProto),
            ("Release", ReleaseProto),
            ("QueryContinueDrag", QueryContinueDragProto),
            ("GiveFeedback", GiveFeedbackProto),
        ]

    _drop_source_vtbl = IDropSourceVtbl(
        QueryInterfaceProto(_drop_source_qi),
        AddRefProto(_drop_source_addref),
        ReleaseProto(_drop_source_release),
        QueryContinueDragProto(_drop_source_query_continue_drag),
        GiveFeedbackProto(_drop_source_give_feedback),
    )

    class DropSource(Structure):
        _fields_ = [("lpVtbl", POINTER(IDropSourceVtbl))]

    _drop_source_instance = DropSource(pointer(_drop_source_vtbl))

    # ------------------ IDataObject Implementation ------------------
    GetDataProto = WINFUNCTYPE(HRESULT, c_void_p, POINTER(FORMATETC), POINTER(STGMEDIUM))
    GetDataHereProto = WINFUNCTYPE(HRESULT, c_void_p, POINTER(FORMATETC), POINTER(STGMEDIUM))
    QueryGetDataProto = WINFUNCTYPE(HRESULT, c_void_p, POINTER(FORMATETC))
    GetCanonicalFormatEtcProto = WINFUNCTYPE(HRESULT, c_void_p, POINTER(FORMATETC), POINTER(FORMATETC))
    SetDataProto = WINFUNCTYPE(HRESULT, c_void_p, POINTER(FORMATETC), POINTER(STGMEDIUM), wintypes.BOOL)
    EnumFormatEtcProto = WINFUNCTYPE(HRESULT, c_void_p, wintypes.DWORD, POINTER(c_void_p))
    DAdviseProto = WINFUNCTYPE(HRESULT, c_void_p, POINTER(FORMATETC), wintypes.DWORD, c_void_p, POINTER(wintypes.DWORD))
    DUnadviseProto = WINFUNCTYPE(HRESULT, c_void_p, wintypes.DWORD)
    EnumDAdviseProto = WINFUNCTYPE(HRESULT, c_void_p, POINTER(c_void_p))

    _active_drag_files: List[str] = []

    def _dobj_qi(this, riid_ptr, ppv_ptr):
        if not riid_ptr or not ppv_ptr:
            return E_NOINTERFACE
        guid = cast(riid_ptr, POINTER(GUID)).contents
        if guid.matches(IID_IUnknown) or guid.matches(IID_IDataObject):
            cast(ppv_ptr, POINTER(c_void_p))[0] = this
            return 0
        cast(ppv_ptr, POINTER(c_void_p))[0] = None
        return E_NOINTERFACE

    def _dobj_addref(this):
        return 1

    def _dobj_release(this):
        return 1

    def _dobj_getdata(this, p_formatetc, p_medium):
        if not p_formatetc or not p_medium or not _active_drag_files:
            return DV_E_FORMATETC
        fetc = p_formatetc.contents
        if fetc.tymed != 0 and not (fetc.tymed & TYMED_HGLOBAL):
            return DV_E_FORMATETC
        cf_req = fetc.cfFormat & 0xFFFF
        for cf, builder in SUPPORTED_FORMATS:
            if (cf & 0xFFFF) == cf_req:
                p_medium.contents.tymed = TYMED_HGLOBAL
                p_medium.contents.hGlobal = builder(_active_drag_files)
                p_medium.contents.pUnkForRelease = None
                return 0
        return DV_E_FORMATETC

    def _dobj_getdatahere(this, p_formatetc, p_medium):
        return E_NOTIMPL

    def _dobj_querygetdata(this, p_formatetc):
        if not p_formatetc:
            return DV_E_FORMATETC
        fetc = p_formatetc.contents
        if fetc.tymed != 0 and not (fetc.tymed & TYMED_HGLOBAL):
            return DV_E_FORMATETC
        cf_req = fetc.cfFormat & 0xFFFF
        for cf, _ in SUPPORTED_FORMATS:
            if (cf & 0xFFFF) == cf_req:
                return 0
        return DV_E_FORMATETC

    def _dobj_getcanonicalformatetc(this, p_formatetc_in, p_formatetc_out):
        return DATA_S_SAMEFORMATETC

    def _dobj_setdata(this, p_formatetc, p_medium, f_release):
        return E_NOTIMPL

    def _dobj_enumformatetc(this, dw_direction, pp_enum_formatetc):
        if dw_direction == 1:  # DATADIR_GET
            return shell32.SHCreateStdEnumFmtEtc(
                len(SUPPORTED_FORMATS),
                cast(SUPPORTED_FMT_ARRAY, c_void_p),
                pp_enum_formatetc,
            )
        return E_NOTIMPL

    def _dobj_dadvise(this, p_formatetc, advf, p_adv_sink, pdw_connection):
        return OLE_E_ADVISENOTSUPPORTED

    def _dobj_dunadvise(this, dw_connection):
        return OLE_E_ADVISENOTSUPPORTED

    def _dobj_enumdadvise(this, pp_enum_advise):
        return OLE_E_ADVISENOTSUPPORTED

    class IDataObjectVtbl(Structure):
        _fields_ = [
            ("QueryInterface", QueryInterfaceProto),
            ("AddRef", AddRefProto),
            ("Release", ReleaseProto),
            ("GetData", GetDataProto),
            ("GetDataHere", GetDataHereProto),
            ("QueryGetData", QueryGetDataProto),
            ("GetCanonicalFormatEtc", GetCanonicalFormatEtcProto),
            ("SetData", SetDataProto),
            ("EnumFormatEtc", EnumFormatEtcProto),
            ("DAdvise", DAdviseProto),
            ("DUnadvise", DUnadviseProto),
            ("EnumDAdvise", EnumDAdviseProto),
        ]

    _dobj_vtbl = IDataObjectVtbl(
        QueryInterfaceProto(_dobj_qi),
        AddRefProto(_dobj_addref),
        ReleaseProto(_dobj_release),
        GetDataProto(_dobj_getdata),
        GetDataHereProto(_dobj_getdatahere),
        QueryGetDataProto(_dobj_querygetdata),
        GetCanonicalFormatEtcProto(_dobj_getcanonicalformatetc),
        SetDataProto(_dobj_setdata),
        EnumFormatEtcProto(_dobj_enumformatetc),
        DAdviseProto(_dobj_dadvise),
        DUnadviseProto(_dobj_dunadvise),
        EnumDAdviseProto(_dobj_enumdadvise),
    )

    class DataObject(Structure):
        _fields_ = [("lpVtbl", POINTER(IDataObjectVtbl))]

    _data_object_instance = DataObject(pointer(_dobj_vtbl))

    ole32.DoDragDrop.restype = c_long
    ole32.DoDragDrop.argtypes = [
        POINTER(DataObject),
        POINTER(DropSource),
        wintypes.DWORD,
        POINTER(wintypes.DWORD),
    ]


def get_unc_to_drive_map() -> dict[str, str]:
    """Returns a dictionary mapping lowercase UNC share roots (e.g. '\\\\server\\share')
    to their mapped drive letters (e.g. 'Z:')."""
    if not IS_WINDOWS:
        return {}
    mapping = {}
    try:
        mpr = ctypes.windll.mpr
        WNetGetConnectionW = mpr.WNetGetConnectionW
        WNetGetConnectionW.restype = wintypes.DWORD
        WNetGetConnectionW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, POINTER(wintypes.DWORD)]

        buf = ctypes.create_unicode_buffer(1024)
        buf_size = wintypes.DWORD(1024)
        for c in range(ord("A"), ord("Z") + 1):
            drive = f"{chr(c)}:"
            buf_size.value = 1024
            res = WNetGetConnectionW(drive, buf, byref(buf_size))
            if res == 0 and buf.value:
                unc = buf.value.rstrip("\\/").lower()
                mapping[unc] = drive
    except Exception:
        pass
    return mapping


def normalize_drag_path(fp: FilePathType) -> str:
    """Normalizes a file path for Windows drag-and-drop and shell execution.

    Preserves mapped network drive letters (e.g. X:\\, Z:\\) instead of resolving
    them to UNC paths (which cause 'File not found' errors in media players like GOM Player).
    If a UNC path is provided that corresponds to an existing mapped network drive,
    restores the mapped drive letter.
    """
    p_str = str(fp).strip()
    if not p_str:
        return ""

    # os.path.abspath resolves relative paths and standardizes slashes to backslashes
    # WITHOUT dereferencing mapped drive letters into UNC paths.
    abs_p = os.path.abspath(p_str)

    # If it is a UNC path (starts with \\), check if a mapped drive letter exists for it
    if IS_WINDOWS and abs_p.startswith(r"\\"):
        unc_map = get_unc_to_drive_map()
        lower_abs = abs_p.lower()
        for unc_prefix, drive_letter in sorted(unc_map.items(), key=lambda x: len(x[0]), reverse=True):
            if lower_abs == unc_prefix:
                return drive_letter + "\\"
            if lower_abs.startswith(unc_prefix + "\\"):
                return drive_letter + abs_p[len(unc_prefix):]

    return abs_p


def start_drag(file_paths: Sequence[FilePathType]) -> int:
    """Initiates a native Windows drag-and-drop operation for the given file paths.

    Args:
        file_paths: Sequence of file path strings or Path objects.

    Returns:
        int: The resulting DROPEFFECT (e.g. DROPEFFECT_COPY, DROPEFFECT_MOVE, DROPEFFECT_LINK,
             or 0 if cancelled / non-Windows).
    """
    global _active_drag_files
    if not IS_WINDOWS or not file_paths:
        return 0

    valid_paths: List[str] = []
    for fp in file_paths:
        norm_p = normalize_drag_path(fp)
        if norm_p and os.path.exists(norm_p):
            valid_paths.append(norm_p)

    if not valid_paths:
        return 0

    _active_drag_files = valid_paths
    try:
        dw_effect = wintypes.DWORD()
        ok_effects = DROPEFFECT_COPY | DROPEFFECT_MOVE | DROPEFFECT_LINK

        ole32.DoDragDrop(
            pointer(_data_object_instance),
            pointer(_drop_source_instance),
            ok_effects,
            byref(dw_effect),
        )
        return int(dw_effect.value)
    except Exception:
        return 0


def copy_files_to_clipboard(file_paths: Sequence[FilePathType]) -> bool:
    """Places files and/or folders onto the Windows clipboard in CF_HDROP and CF_UNICODETEXT formats.

    Allows pasting directly into Windows Explorer, Desktop, or other applications with Ctrl+V,
    as well as pasting file paths as text into text editors and terminals.

    Args:
        file_paths: Sequence of file path strings or Path objects.

    Returns:
        bool: True if files were successfully placed on clipboard, False otherwise.
    """
    if not IS_WINDOWS or not file_paths:
        return False

    valid_paths: List[str] = []
    for fp in file_paths:
        norm_p = normalize_drag_path(fp)
        if norm_p and os.path.exists(norm_p):
            valid_paths.append(norm_p)

    if not valid_paths:
        return False

    if not user32.OpenClipboard(0):
        return False

    try:
        user32.EmptyClipboard()

        # 1. CF_HDROP (15) for Explorer / Desktop file pasting
        h_drop = _create_hdrop_buffer(valid_paths)
        user32.SetClipboardData(CF_HDROP, h_drop)

        # 2. CF_UNICODETEXT (13) for text editors / terminals
        h_text = _create_unicodetext_buffer(valid_paths)
        user32.SetClipboardData(CF_UNICODETEXT, h_text)

        return True
    except Exception:
        return False
    finally:
        user32.CloseClipboard()

