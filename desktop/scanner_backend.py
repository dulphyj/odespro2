from __future__ import annotations

from typing import Any


class ScannerBackend:
    """Unified scanner interface — prueba WIA primero, TWAIN como fallback."""

    @staticmethod
    def _get_backend() -> Any:
        from desktop.wia_scanner import WiaScanner
        if WiaScanner.is_available():
            return WiaScanner

        from desktop.twain_scanner import TwainScanner
        if TwainScanner.is_available():
            return TwainScanner

        return None

    @staticmethod
    def is_available() -> bool:
        return ScannerBackend._get_backend() is not None

    @staticmethod
    def list_scanners() -> list[dict]:
        backend = ScannerBackend._get_backend()
        if not backend:
            return []
        return backend.list_scanners()

    @staticmethod
    def scan(scanner_index: int = 0, pages: int = 1) -> list[bytes]:
        backend = ScannerBackend._get_backend()
        if not backend:
            raise RuntimeError("No hay escáner disponible (WIA ni TWAIN)")
        return backend.scan(scanner_index=scanner_index, pages=pages)
