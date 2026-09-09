"""Windows OLE Drag and Drop helper for exporting files from GUI to Windows Explorer / external apps.

Implements native IDropSource and IDataObject COM interfaces via ctypes so no external
third-party dependencies (like pywin32) are required. Fully supports CF_HDROP (standard
file drops for Explorer, Chromium, Electron, VS Code, Gemini, browsers, desktop, etc.)
as well as text and URL clipboard formats.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import List, Sequence, Union

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
    CF_FILENAMEW = user32.RegisterClipboardFormatW("FileNameW")
    CF_FILENAMEA = user32.RegisterClipboardFormatW("FileName")
    CF_URLW = user32.RegisterClipboardFormatW("UniformResourceLocatorW")

    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalLock.restype = c_void_p
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]

    shell32.SHCreateStdEnumFmtEtc.restype = HRESULT
    shell32.SHCreateStdEnumFmtEtc.argtypes = [wintypes.UINT, c_void_p, POINTER(c_void_p)]

    shell32.DragQueryFileW.restype = wintypes.UINT
    shell32.DragQueryFileW.argtypes = [c_void_p, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]

    class POINT(Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

    class DROPFILES(Structure):
        _fields_ = [
            ("pFiles", wintypes.DWORD),
            ("pt", POINT),
            ("fNC", wintypes.BOOL),
            ("fWide", wintypes.BOOL),
        ]

    class FORMATETC(Structure):
        _fields_ = [
            ("cfFormat", wintypes.UINT),
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

    # Data builders for clipboard formats
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

    def _create_text_buffer(file_paths: List[str]) -> wintypes.HGLOBAL:
        text = "\r\n".join(file_paths)
        encoded = text.encode("mbcs", errors="replace") + b"\x00"
        hmem = kernel32.GlobalAlloc(GHND, len(encoded))
        ptr = kernel32.GlobalLock(hmem)
        try:
            memmove(ptr, encoded, len(encoded))
        finally:
            kernel32.GlobalUnlock(hmem)
        return hmem

    def _create_filenamew_buffer(file_paths: List[str]) -> wintypes.HGLOBAL:
        encoded = file_paths[0].encode("utf-16le") + b"\x00\x00"
        hmem = kernel32.GlobalAlloc(GHND, len(encoded))
        ptr = kernel32.GlobalLock(hmem)
        try:
            memmove(ptr, encoded, len(encoded))
        finally:
            kernel32.GlobalUnlock(hmem)
        return hmem

    def _create_filenamea_buffer(file_paths: List[str]) -> wintypes.HGLOBAL:
        encoded = file_paths[0].encode("mbcs", errors="replace") + b"\x00"
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

    SUPPORTED_FORMATS = [
        (CF_HDROP, _create_hdrop_buffer),
        (CF_UNICODETEXT, _create_unicodetext_buffer),
        (CF_TEXT, _create_text_buffer),
        (CF_FILENAMEW, _create_filenamew_buffer),
        (CF_FILENAMEA, _create_filenamea_buffer),
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

    def _drop_source_query_continue_drag(this, f_escape_pressed, grf_key_state):
        if f_escape_pressed:
            return DRAGDROP_S_CANCEL
        if not (grf_key_state & (MK_LBUTTON | MK_RBUTTON)):
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
        if not (fetc.tymed & TYMED_HGLOBAL):
            return DV_E_FORMATETC
        for cf, builder in SUPPORTED_FORMATS:
            if fetc.cfFormat == cf:
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
        if not (fetc.tymed & TYMED_HGLOBAL):
            return DV_E_FORMATETC
        for cf, _ in SUPPORTED_FORMATS:
            if fetc.cfFormat == cf:
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
        abs_p = str(Path(fp).resolve())
        if os.path.exists(abs_p):
            valid_paths.append(abs_p)

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
    finally:
        _active_drag_files = []
