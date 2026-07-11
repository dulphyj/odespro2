from __future__ import annotations

import io
import threading

from PIL import Image

_WIA_AVAILABLE = False
try:
    import comtypes.client
    _WIA_AVAILABLE = True
except ImportError:
    pass


class WiaScanner:

    @staticmethod
    def _try_init_com() -> bool:
        """Intenta inicializar COM en STA o MTA. Retorna True si ok."""
        try:
            import ctypes
            hr = ctypes.windll.ole32.CoInitializeEx(None, 2)
            if hr == -2147417850:
                ctypes.windll.ole32.CoUninitialize()
                hr = ctypes.windll.ole32.CoInitializeEx(None, 0)
            return hr >= 0 or hr == 1
        except Exception:
            return False

    @staticmethod
    def is_available() -> bool:
        if not _WIA_AVAILABLE:
            return False
        if not WiaScanner._try_init_com():
            return False
        try:
            wia = comtypes.client.CreateObject("WIA.DeviceManager")
            return wia.DeviceInfos.Count > 0
        except Exception:
            return False

    @staticmethod
    def list_scanners() -> list[dict]:
        if not _WIA_AVAILABLE:
            return []
        WiaScanner._try_init_com()
        try:
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
    def scan(scanner_index: int = 0, pages: int = 1) -> list[bytes]:
        """
        pages == 0: modo ADF — abre el diálogo UNA VEZ, seleccionás
                     Alimentador, y escanea TODAS las hojas automáticamente.
        pages  > 0: modo flatbed — abre el diálogo N veces, una por hoja.
        """
        if not _WIA_AVAILABLE:
            raise RuntimeError("WIA no disponible (pip install comtypes)")

        if pages == 0:
            return WiaScanner._scan_with_dialog(scanner_index, scan_count=999)
        results = []
        for _ in range(pages):
            result = WiaScanner._scan_with_dialog(scanner_index, scan_count=1)
            results.extend(result)
        return results

    @staticmethod
    def _scan_with_dialog(scanner_index: int, scan_count: int = 1) -> list[bytes]:
        """
        Abre el diálogo WIA con formato TIFF (soporta multipágina del ADF).
        Extrae cada frame como PNG individual.
        scan_count=999 → ADF (escanea hasta 999 páginas)
        scan_count=1   → flatbed (1 página)
        """
        result_pages: list[bytes] = []
        error: list[Exception | None] = [None]

        def _dialog():
            try:
                WiaScanner._try_init_com()
                dialog = comtypes.client.CreateObject("WIA.CommonDialog")
                fmt_tiff = "{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}"
                image = dialog.ShowAcquireImage(1, 1, 0, fmt_tiff, scan_count, 0)
                if image:
                    buf = io.BytesIO()
                    for i in range(1, image.FileData.Count + 1):
                        buf.write(image.FileData.Item(i))
                    data = buf.getvalue()
                    if data:
                        pil_img = Image.open(io.BytesIO(data))
                        n_frames = getattr(pil_img, "n_frames", 1)
                        for frame in range(n_frames):
                            pil_img.seek(frame)
                            out = io.BytesIO()
                            pil_img.save(out, format="PNG")
                            result_pages.append(out.getvalue())
                    else:
                        error[0] = RuntimeError("No se recibieron datos")
                else:
                    error[0] = RuntimeError("El usuario canceló")
            except Exception as e:
                error[0] = e

        t = threading.Thread(target=_dialog, daemon=True)
        t.start()
        t.join(timeout=300)
        if error[0]:
            raise error[0]
        if result_pages:
            return result_pages
        raise RuntimeError("No se obtuvo imagen")
