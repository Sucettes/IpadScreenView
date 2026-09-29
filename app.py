"""Affiche en direct l'ecran d'un iPad branche en USB dans une fenetre."""

import asyncio
import sys

import cv2
import numpy as np
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot

WINDOW = "iPad (q = quitter)"


async def connect():
    """Ouvre le service developpeur de l'iPad (direct, ou via tunnel sur iOS 17+)."""
    lockdown = await create_using_usbmux()
    version = lockdown.product_version
    print(f"iPad detecte : iPadOS {version}")

    if int(version.split(".")[0]) < 17:
        return DvtProvider(lockdown)

    from pymobiledevice3.tunneld.api import get_tunneld_devices

    devices = await get_tunneld_devices()
    if not devices:
        sys.exit("Tunnel introuvable. Lance d'abord, en admin :\n"
                 "  python -m pymobiledevice3 remote tunneld")
    return DvtProvider(devices[0])


async def main():
    provider = await connect()
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)

    async with provider, Screenshot(provider) as screenshot:
        fps, last = 0.0, asyncio.get_event_loop().time()
        while cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) >= 0:
            png = await screenshot.get_screenshot()
            frame = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                continue

            now = asyncio.get_event_loop().time()
            fps = 0.9 * fps + 0.1 / (now - last) if fps else 1 / (now - last)
            last = now
            cv2.putText(frame, f"{fps:.0f} FPS", (12, 36),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

            cv2.imshow(WINDOW, frame)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(main())
