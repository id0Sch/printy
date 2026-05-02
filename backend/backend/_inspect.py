"""Print USB descriptor info for the thermal printer to find correct endpoints."""
import usb.core
import usb.util

from .printer import VENDOR_ID, PRODUCT_ID, _libusb_backend


def main() -> None:
    backend = _libusb_backend()
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID, backend=backend)
    if dev is None:
        raise SystemExit("device not found")
    print(f"device: {dev.idVendor:#06x}:{dev.idProduct:#06x}")
    for cfg in dev:
        print(f"  config {cfg.bConfigurationValue}")
        for intf in cfg:
            print(f"    interface {intf.bInterfaceNumber} alt {intf.bAlternateSetting} class={intf.bInterfaceClass:#x}")
            for ep in intf:
                direction = "IN" if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_IN else "OUT"
                print(f"      endpoint {ep.bEndpointAddress:#04x} {direction} type={ep.bmAttributes & 0x3}")


if __name__ == "__main__":
    main()
