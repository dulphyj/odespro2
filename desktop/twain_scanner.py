from __future__ import annotations

import ctypes
import ctypes.wintypes
import io
import os
import struct
from typing import Optional

from PIL import Image

TW_UINT16 = ctypes.c_uint16
TW_UINT32 = ctypes.c_uint32
TW_BOOL = TW_UINT16
TW_STR32 = ctypes.c_char * 34
TW_HANDLE = ctypes.c_void_p
TW_MEMREF = ctypes.c_void_p
HWND = ctypes.wintypes.HWND
HGLOBAL = ctypes.c_void_p

# --- TWAIN Constants ---
DG_CONTROL = 0x0001
DG_IMAGE = 0x0002

DAT_PARENT = 0x0001
DAT_IDENTITY = 0x0002
DAT_USERINTERFACE = 0x0004
DAT_IMAGEINFO = 0x0101
DAT_IMAGENATIVE = 0x0104
DAT_PENDINGXFERS = 0x0108

MSG_OPENDSM = 0x0301
MSG_CLOSEDSM = 0x0302
MSG_OPENDS = 0x0304
MSG_CLOSEDS = 0x0305
MSG_USERSELECT = 0x0306
MSG_GET = 0x0307
MSG_GETDEFAULT = 0x0309
MSG_ENABLEDS = 0x030B
MSG_DISABLEDS = 0x030C
MSG_XFERREADY = 0x030E
MSG_ENDXFER = 0x030F
MSG_CLOSEDSOK = 0x0310

TWRC_SUCCESS = 0
TWRC_FAILURE = 1
TWRC_CHECKSTATUS = 2
TWRC_CANCEL = 3
TWRC_XFERDONE = 5

TWCC_SUCCESS = 0
TWCC_BUMMER = 1
TWCC_CAPBADOPERATION = 23


class TW_VERSION(ctypes.Structure):
    _pack_ = 2
    _fields_ = [
        ("MajorNum", TW_UINT16),
        ("MinorNum", TW_UINT16),
        ("Language", TW_UINT16),
        ("Country", TW_UINT16),
        ("Info", TW_STR32),
    ]


class TW_IDENTITY(ctypes.Structure):
    _pack_ = 2
    _fields_ = [
        ("Id", TW_UINT32),
        ("Version", TW_VERSION),
        ("ProtocolMajor", TW_UINT16),
        ("ProtocolMinor", TW_UINT16),
        ("SupportedGroups", TW_UINT32),
        ("Manufacturer", TW_STR32),
        ("ProductFamily", TW_STR32),
        ("ProductName", TW_STR32),
    ]


class TW_USERINTERFACE(ctypes.Structure):
    _pack_ = 2
    _fields_ = [
        ("ShowUI", TW_BOOL),
        ("ModalUI", TW_BOOL),
        ("hParent", TW_HANDLE),
    ]


class TW_PENDINGXFERS(ctypes.Structure):
    _pack_ = 2
    _fields_ = [
        ("Count", TW_UINT16),
        ("EOJ", TW_UINT32),
    ]


DSM_ENTRY_TYPE = ctypes.WINFUNCTYPE(
    TW_UINT16,
    TW_MEMREF,  # pOrigin
    TW_MEMREF,  # pDest
    TW_UINT32,  # DG
    TW_UINT16,  # DAT
    TW_UINT16,  # MSG
    TW_MEMREF,  # pData
)


class TwainScanner:
    _dll: Optional[ctypes.WinDLL] = None
    _entry: Optional[ctypes.WINFUNCTYPE] = None
    _app_id: Optional[TW_IDENTITY] = None
    _source_id: Optional[TW_IDENTITY] = None
    _hwnd: Optional[int] = None

    # --- DLL Loading ---

    @classmethod
    def _load_dll(cls) -> bool:
        if cls._dll is not None:
            return True
        candidates = ["TWAINDSM.dll", "TWAIN_32.dll"]
        for name in candidates:
            try:
                cls._dll = ctypes.windll.LoadLibrary(name)
                cls._entry = cls._dll["DSM_Entry"]
                cls._entry.restype = TW_UINT16
                cls._entry.argtypes = [
                    TW_MEMREF, TW_MEMREF,
                    TW_UINT32, TW_UINT16, TW_UINT16,
                    TW_MEMREF,
                ]
                return True
            except Exception:
                continue
        return False

    @classmethod
    def _call(
        cls,
        dest: Optional[ctypes.Structure],
        dg: int,
        dat: int,
        msg: int,
        data: ctypes.Structure | None,
    ) -> tuple[int, ctypes.Structure | None]:
        if not cls._load_dll():
            raise RuntimeError("TWAIN no disponible en este equipo")

        p_origin = ctypes.byref(cls._app_id) if cls._app_id else None
        p_dest = ctypes.byref(dest) if dest else None
        p_data = ctypes.byref(data) if data else None

        rc = cls._entry(p_origin, p_dest, TW_UINT32(dg), TW_UINT16(dat), TW_UINT16(msg), p_data)
        return rc, data

    # --- Public API ---

    @classmethod
    def list_scanners(cls) -> list[dict]:
        result = []
        if not cls._load_dll():
            return result

        app = TW_IDENTITY()
        app.Version.MajorNum = 1
        app.Version.MinorNum = 0
        app.Version.Language = 9
        app.Version.Country = 1
        app.Version.Info = b"DocApp Scanner"
        app.ProtocolMajor = 2
        app.ProtocolMinor = 4
        app.SupportedGroups = DG_CONTROL | DG_IMAGE
        app.Manufacturer = b"DocApp"
        app.ProductFamily = b"Scanner"
        app.ProductName = b"DocApp"
        cls._app_id = app

        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        cls._hwnd = hwnd

        parent = ctypes.c_int(hwnd)
        rc, _ = cls._call(None, DG_CONTROL, DAT_PARENT, MSG_OPENDSM, parent)
        if rc != TWRC_SUCCESS:
            return result

        source = TW_IDENTITY()
        source.Id = 0
        source.Version.MajorNum = 1
        source.Version.MinorNum = 0
        source.Version.Language = 9
        source.Version.Country = 1
        source.Version.Info = b""
        source.ProtocolMajor = 2
        source.ProtocolMinor = 4
        source.SupportedGroups = DG_CONTROL | DG_IMAGE
        source.Manufacturer = b""
        source.ProductFamily = b""
        source.ProductName = b""

        i = 0
        while True:
            source.Id = 0
            rc, source = cls._call(app, DG_CONTROL, DAT_IDENTITY, MSG_GET, source)
            if rc != TWRC_SUCCESS:
                break
            result.append({
                "index": i,
                "name": source.ProductName.decode("latin-1").strip("\x00 "),
                "manufacturer": source.Manufacturer.decode("latin-1").strip("\x00 "),
                "family": source.ProductFamily.decode("latin-1").strip("\x00 "),
            })
            i += 1

        cls._call(None, DG_CONTROL, DAT_PARENT, MSG_CLOSEDSM, parent)
        return result

    @classmethod
    def scan(
        cls,
        scanner_index: int = 0,
        show_ui: bool = True,
        dpi: int = 200,
    ) -> bytes:
        app = TW_IDENTITY()
        app.Version.MajorNum = 1
        app.Version.MinorNum = 0
        app.Version.Language = 9
        app.Version.Country = 1
        app.Version.Info = b"DocApp Scanner"
        app.ProtocolMajor = 2
        app.ProtocolMinor = 4
        app.SupportedGroups = DG_CONTROL | DG_IMAGE
        app.Manufacturer = b"DocApp"
        app.ProductFamily = b"Scanner"
        app.ProductName = b"DocApp"
        cls._app_id = app

        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        cls._hwnd = hwnd

        parent = ctypes.c_int(hwnd)
        rc, _ = cls._call(None, DG_CONTROL, DAT_PARENT, MSG_OPENDSM, parent)
        if rc != TWRC_SUCCESS:
            raise RuntimeError("No se pudo abrir el gestor de escáneres TWAIN")

        try:
            source = TW_IDENTITY()
            source.Id = 0
            source.Version.MajorNum = 1
            source.Version.MinorNum = 0
            source.Version.Language = 9
            source.Version.Country = 1
            source.Version.Info = b""
            source.ProtocolMajor = 2
            source.ProtocolMinor = 4
            source.SupportedGroups = DG_CONTROL | DG_IMAGE
            source.Manufacturer = b""
            source.ProductFamily = b""
            source.ProductName = b""

            for _ in range(scanner_index + 1):
                source.Id = 0
                rc, source = cls._call(app, DG_CONTROL, DAT_IDENTITY, MSG_GET, source)
                if rc != TWRC_SUCCESS:
                    raise RuntimeError(f"Escáner índice {scanner_index} no encontrado")

            rc, source = cls._call(app, DG_CONTROL, DAT_IDENTITY, MSG_OPENDS, source)
            if rc != TWRC_SUCCESS:
                raise RuntimeError("No se pudo abrir el escáner")
            cls._source_id = source

            ui = TW_USERINTERFACE()
            ui.ShowUI = 1 if show_ui else 0
            ui.ModalUI = 1
            ui.hParent = ctypes.c_void_p(hwnd)

            rc, ui = cls._call(source, DG_CONTROL, DAT_USERINTERFACE, MSG_ENABLEDS, ui)
            if rc not in (TWRC_SUCCESS, TWRC_XFERDONE):
                cls._call(source, DG_CONTROL, DAT_IDENTITY, MSG_CLOSEDS, None)
                raise RuntimeError("El usuario canceló o no se pudo escanear")

            image_bytes = cls._transfer_image(source)

            cls._call(source, DG_CONTROL, DAT_IDENTITY, MSG_CLOSEDS, None)
            return image_bytes
        finally:
            cls._call(None, DG_CONTROL, DAT_PARENT, MSG_CLOSEDSM, parent)

    @classmethod
    def _transfer_image(cls, source: TW_IDENTITY) -> bytes:
        hbmp = ctypes.c_void_p(0)
        rc, hbmp = cls._call(source, DG_IMAGE, DAT_IMAGENATIVE, MSG_GET, hbmp)
        if rc != TWRC_XFERDONE:
            pf = TW_PENDINGXFERS()
            cls._call(source, DG_CONTROL, DAT_PENDINGXFERS, MSG_ENDXFER, pf)
            raise RuntimeError("Error al recibir la imagen del escáner")

        try:
            handle = hbmp.value if hasattr(hbmp, 'value') else hbmp
            if not handle:
                raise RuntimeError("Handle de imagen vacío")

            p_locked = ctypes.windll.kernel32.GlobalLock(handle)
            if not p_locked:
                raise RuntimeError("No se pudo bloquear la memoria de la imagen")

            try:
                data = ctypes.string_at(p_locked, 1024 * 1024 * 50)
            finally:
                ctypes.windll.kernel32.GlobalUnlock(handle)
            ctypes.windll.kernel32.GlobalFree(handle)

            img = _dib_to_pil(data)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return buf.getvalue()
        finally:
            pf = TW_PENDINGXFERS()
            cls._call(source, DG_CONTROL, DAT_PENDINGXFERS, MSG_ENDXFER, pf)

    @classmethod
    def is_available(cls) -> bool:
        try:
            return cls._load_dll()
        except Exception:
            return False


def _dib_to_pil(data: bytes) -> Image.Image:
    bfType = struct.unpack_from("<H", data, 0)[0]
    offset = 14
    if bfType == 0x4D42:
        offset = struct.unpack_from("<I", data, 10)[0]
    header_size = struct.unpack_from("<I", data, offset)[0]

    if header_size >= 40:
        width = struct.unpack_from("<i", data, offset + 4)[0]
        height = struct.unpack_from("<i", data, offset + 8)[0]
        planes = struct.unpack_from("<H", data, offset + 12)[0]
        bit_count = struct.unpack_from("<H", data, offset + 14)[0]
        compression = struct.unpack_from("<I", data, offset + 16)[0]

        row_size = ((width * bit_count + 31) // 32) * 4
        pixel_data = data[offset + header_size:]

        if bit_count == 24:
            img = Image.frombytes("RGB", (width, abs(height)), pixel_data, "raw", "BGR", row_size)
        elif bit_count == 8:
            palette_offset = offset + header_size
            colors = struct.unpack_from("<256I", data, palette_offset)

            import numpy as np
            arr = np.frombuffer(pixel_data, dtype=np.uint8).reshape((abs(height), width))
            palette_arr = np.zeros((256, 3), dtype=np.uint8)
            for i in range(256):
                palette_arr[i] = [(colors[i] >> 16) & 0xFF, (colors[i] >> 8) & 0xFF, colors[i] & 0xFF]
            img = Image.fromarray(arr, mode="L")
            img = img.convert("RGB")
            return img
        else:
            from PIL import ImageOps
            img = Image.frombytes("RGB", (width, abs(height)), pixel_data, "raw", "BGR", row_size)
            return img

    if height < 0:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
    return img
