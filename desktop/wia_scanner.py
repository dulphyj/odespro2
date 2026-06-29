from __future__ import annotations

import io
import threading
from typing import Optional

from PIL import Image

_WIA_AVAILABLE = False
try:
    import comtypes.client
    _WIA_AVAILABLE = True
except ImportError:
    pass


def _init_com_sta():
    """Inicializa COM en modo STA para el hilo actual (ignora si ya iniciado)."""
    import ctypes
    hr = ctypes.windll.ole32.CoInitializeEx(None, 2)  # COINIT_APARTMENTTHREADED
    return hr  # 0 = OK, 1 = S_FALSE (ya iniciado)


class WiaScanner:
    """Scanner via WIA (Windows Image Acquisition) — funciona con Python 64-bit."""

    @staticmethod
    def is_available() -> bool:
        if not _WIA_AVAILABLE:
            return False
        try:
            _init_com_sta()
            wia = comtypes.client.CreateObject("WIA.DeviceManager")
            return wia.DeviceInfos.Count > 0
        except Exception:
            return False

    @staticmethod
    def list_scanners() -> list[dict]:
        if not _WIA_AVAILABLE:
            return []
        try:
            _init_com_sta()
            wia = comtypes.client.CreateObject("WIA.DeviceManager")
            result = []
            for i in range(1, wia.DeviceInfos.Count + 1):
                info = wia.DeviceInfos.Item(i)
                name = ""
                try:
                    name = info.Properties("Name").Value
                except Exception:
                    name = f"Escáner {i}"
                result.append({"index": i - 1, "name": name})
            return result
        except Exception:
            return []

    @staticmethod
    def scan(scanner_index: int = 0, show_ui: bool = True) -> bytes:
        if not _WIA_AVAILABLE:
            raise RuntimeError("WIA no disponible (instala comtypes: pip install comtypes)")

        if show_ui:
            result = [None]
            error = [None]

            def _scan_sta():
                try:
                    _init_com_sta()
                    dialog = comtypes.client.CreateObject("WIA.CommonDialog")
                    image = dialog.ShowAcquireImage(
                        1, 1, 0, 0, 0, 0,
                    )
                    if image:
                        buf = io.BytesIO()
                        for i in range(1, image.FileData.Count + 1):
                            buf.write(image.FileData.Item(i))
                        data = buf.getvalue()
                        if data:
                            pil_img = Image.open(io.BytesIO(data))
                            out = io.BytesIO()
                            pil_img.save(out, format="PNG")
                            result[0] = out.getvalue()
                        else:
                            error[0] = RuntimeError("No se recibieron datos")
                    else:
                        error[0] = RuntimeError("El usuario canceló")
                except Exception as e:
                    error[0] = e

            t = threading.Thread(target=_scan_sta, daemon=True)
            t.start()
            t.join(timeout=120)
            if error[0]:
                raise error[0]
            if result[0]:
                return result[0]
            raise RuntimeError("No se obtuvo imagen")

        _init_com_sta()
        wia = comtypes.client.CreateObject("WIA.DeviceManager")
        count = wia.DeviceInfos.Count
        if count == 0:
            raise RuntimeError("No se encontraron escáneres")
        if scanner_index >= count:
            raise RuntimeError(f"Escáner índice {scanner_index} no encontrado (hay {count})")

        info = wia.DeviceInfos.Item(scanner_index + 1)
        device = info.Connect()
        try:
            item = device.Items.Item(1)
            fmt = "{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}"
            image_file = item.Transfer(fmt)
            buf = io.BytesIO()
            for i in range(1, image_file.FileData.Count + 1):
                buf.write(image_file.FileData.Item(i))
            data = buf.getvalue()
            if not data:
                raise RuntimeError("No se recibieron datos del escáner")
            pil_img = Image.open(io.BytesIO(data))
            out = io.BytesIO()
            pil_img.save(out, format="PNG")
            return out.getvalue()
        finally:
            try:
                device.Close()
            except Exception:
                pass
