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
    import ctypes
    ctypes.windll.ole32.CoInitializeEx(None, 2)


class WiaScanner:

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
    def scan(scanner_index: int = 0, show_ui: bool = True, dpi: int = 200, pages: int = 1) -> list[bytes]:
        """
        pages == 0: modo automático (activa alimentador ADF, escanea hasta vaciar)
        pages  > 0: modo manual, número exacto de páginas
        """
        if not _WIA_AVAILABLE:
            raise RuntimeError("WIA no disponible (pip install comtypes)")

        if pages == 0:
            return WiaScanner._scan_auto(scanner_index, dpi)
        results = []
        for _ in range(pages):
            result = WiaScanner._scan_single(scanner_index, show_ui, dpi)
            results.append(result)
        return results

    @staticmethod
    def _set_dpi(item, dpi: int):
        """Intenta setear DPI en el ítem WIA (property 6147=X_RES, 6148=Y_RES)."""
        try:
            item.Properties.Item(6147).Value = dpi  # WIA_IPS_X_RES
            item.Properties.Item(6148).Value = dpi  # WIA_IPS_Y_RES
        except Exception:
            pass

    @staticmethod
    def _scan_auto(scanner_index: int, dpi: int = 200) -> list[bytes]:
        _init_com_sta()
        wia = comtypes.client.CreateObject("WIA.DeviceManager")
        info = wia.DeviceInfos.Item(scanner_index + 1)
        device = info.Connect()
        try:
            item = device.Items.Item(1)
            WiaScanner._set_dpi(item, dpi)

            # Activar modo alimentador (ADF) si el escáner lo soporta
            try:
                item.Properties.Item(3088).Value = 1  # FEEDER
            except Exception:
                pass
            # Escanear todas las páginas del alimentador
            try:
                item.Properties.Item(3090).Value = 0  # 0 = todas
            except Exception:
                pass

            fmt = "{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}"
            results = []
            while True:
                try:
                    image_file = item.Transfer(fmt)
                    buf = io.BytesIO()
                    for i in range(1, image_file.FileData.Count + 1):
                        buf.write(image_file.FileData.Item(i))
                    data = buf.getvalue()
                    if data:
                        pil_img = Image.open(io.BytesIO(data))
                        out = io.BytesIO()
                        pil_img.save(out, format="PNG")
                        results.append(out.getvalue())
                except Exception:
                    break
            if not results:
                raise RuntimeError("No se obtuvieron imágenes del escáner")
            return results
        finally:
            try:
                device.Close()
            except Exception:
                pass

    @staticmethod
    def _scan_single(scanner_index: int, show_ui: bool, dpi: int = 200) -> bytes:
        if show_ui:
            result = [None]
            error = [None]

            def _dialog():
                try:
                    _init_com_sta()
                    dialog = comtypes.client.CreateObject("WIA.CommonDialog")
                    image = dialog.ShowAcquireImage(1, 1, 0, "{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}", 0, 0)
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

            t = threading.Thread(target=_dialog, daemon=True)
            t.start()
            t.join(timeout=120)
            if error[0]:
                raise error[0]
            if result[0]:
                return result[0]
            raise RuntimeError("No se obtuvo imagen")

        _init_com_sta()
        wia = comtypes.client.CreateObject("WIA.DeviceManager")
        if wia.DeviceInfos.Count == 0:
            raise RuntimeError("No se encontraron escáneres")
        if scanner_index >= wia.DeviceInfos.Count:
            raise RuntimeError(f"Escáner índice {scanner_index} no encontrado")

        info = wia.DeviceInfos.Item(scanner_index + 1)
        device = info.Connect()
        try:
            item = device.Items.Item(1)
            WiaScanner._set_dpi(item, dpi)
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
