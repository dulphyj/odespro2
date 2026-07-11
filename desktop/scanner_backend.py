from __future__ import annotations

from typing import Any


class ScannerBackend:
    """Unified scanner interface — prueba WIA primero, TWAIN como fallback."""

    _force_mock = False

    @staticmethod
    def force_mock(enable: bool = True):
        ScannerBackend._force_mock = enable

    @staticmethod
    def _get_backend() -> Any:
        if ScannerBackend._force_mock:
            from desktop.mock_scanner import MockScanner
            return MockScanner

        from desktop.wia_scanner import WiaScanner
        if WiaScanner.is_available():
            return WiaScanner

        from desktop.twain_scanner import TwainScanner
        if TwainScanner.is_available():
            return TwainScanner

        from desktop.mock_scanner import MockScanner
        return MockScanner

    @staticmethod
    def is_available() -> bool:
        return True

    @staticmethod
    def list_scanners() -> list[dict]:
        backend = ScannerBackend._get_backend()
        return backend.list_scanners()

    @staticmethod
    def scan(scanner_index: int = 0, show_ui: bool = True, dpi: int = 200, pages: int = 1) -> list[bytes]:
        backend = ScannerBackend._get_backend()
        return backend.scan(scanner_index=scanner_index, show_ui=show_ui and not ScannerBackend._force_mock, dpi=dpi, pages=pages)
