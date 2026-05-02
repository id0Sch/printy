"""Connect to the MIAOBAO 58Printer over USB."""
from __future__ import annotations

import os
import platform
from contextlib import contextmanager

import usb.backend.libusb1
from escpos.printer import Usb

VENDOR_ID = 0x0483
PRODUCT_ID = 0x5840
OUT_ENDPOINT = 0x04
IN_ENDPOINT = 0x82

# 384 dots ÷ 12 dots/char (Font A) = 32 cols.
_MEDIA_WIDTH = {"pixels": 384, "mm": 48}


def _libusb_backend():
    if platform.system() != "Darwin":
        return None
    candidates = [
        os.environ.get("LIBUSB_PATH"),
        "/opt/homebrew/lib/libusb-1.0.0.dylib",
        "/usr/local/lib/libusb-1.0.0.dylib",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return usb.backend.libusb1.get_backend(find_library=lambda _p=path: _p)
    return None


@contextmanager
def open_printer():
    kwargs = {
        "profile": "default",
        "in_ep": IN_ENDPOINT,
        "out_ep": OUT_ENDPOINT,
    }
    backend = _libusb_backend()
    if backend is not None:
        kwargs["backend"] = backend
    p = Usb(VENDOR_ID, PRODUCT_ID, **kwargs)
    p.profile.profile_data["media"]["width"] = _MEDIA_WIDTH
    try:
        yield p
    finally:
        p.close()
