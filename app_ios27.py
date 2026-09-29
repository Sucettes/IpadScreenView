"""
Affiche l'ecran de l'iPad en direct dans une fenetre, en FLUIDE (flux video HEVC).

Reserve a iPadOS 27+ : sur les versions anterieures l'iPad refuse le flux
("Remote control requires iOS 27.0 or later"). Pour les versions plus anciennes,
utiliser app.py (captures, plus lent).

Prerequis (comme app.py) : tunnel lance en admin et image developpeur montee.
Le plus simple : passer par mirror.bat. Sinon, en manuel :
    python -m pymobiledevice3 remote tunneld          (terminal admin)
    python -m pymobiledevice3 mounter auto-mount
    python app_ios27.py

Quitter : touche q ou Echap.
"""

import asyncio
import socket
import struct
import sys
import uuid

import av
import cv2
from pymobiledevice3.remote.core_device.display_service import DisplayService
from pymobiledevice3.remote.core_device.screen_stream import depacketize_hevc
from pymobiledevice3.tunneld.api import get_tunneld_devices

# Selector loop : sock_recv UDP fiable sous Windows.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

WINDOW = "iPad (q = quitter)"
DISPLAY_ID = 1


def build_rtcp_rr(local_ssrc, remote_ssrc, highest_seq):
    """Receiver Report minimal (RFC 3550). Sans envoi periodique, l'encodeur
    de l'iPad s'arrete au bout de ~25 s (RTCPTimeoutEnabled)."""
    return struct.pack("!BBHII BBBB IIII",
                       0x81, 0xC9, 7,
                       local_ssrc & 0xFFFFFFFF, remote_ssrc & 0xFFFFFFFF,
                       0, 0, 0, 0,
                       highest_seq & 0xFFFFFFFF, 0, 0, 0)


async def get_rsd():
    devices = await get_tunneld_devices()
    if not devices:
        sys.exit("Tunnel introuvable. Lance d'abord, en admin :\n"
                 "  python -m pymobiledevice3 remote tunneld")
    return devices[0]


def show(frame):
    """Affiche une image decodee. Renvoie False si l'utilisateur veut quitter."""
    img = frame.to_ndarray(format="bgr24")
    cv2.imshow(WINDOW, img)
    if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
        return False
    return cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) >= 0


async def main():
    rsd = await get_rsd()
    sender_ip = rsd.service.address[0]

    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock.bind(("::", 0))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
    port = sock.getsockname()[1]

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    decoder = av.CodecContext.create("hevc", "r")

    async with DisplayService(rsd) as service:
        answer = await service.start_video_stream(
            receiver_ip=service.service.local_address[0],
            receiver_port=port,
            sender_ip=sender_ip,
            display_id=DISPLAY_ID,
        )
        session_id = uuid.UUID(str(
            answer["connection"]["options"]["avcMediaStreamOptionClientSessionID"]["uuid"]))

        # SSRC vus du cote iPad : LocalSSRC = le sien, RemoteSSRC = le notre.
        cfg = answer["connection"].get("streamConfig", {})
        rtcp_dest = (sender_ip, int(cfg.get("SourcePort", 0)), 0, 0)
        local_ssrc = int(cfg.get("RemoteSSRC", 0))
        remote_ssrc = int(cfg.get("LocalSSRC", 0))

        loop = asyncio.get_running_loop()
        sock.setblocking(False)
        highest_seq = 0
        rtcp_last = 0.0
        fu_buffer = bytearray()
        au = bytearray()
        running = True

        try:
            while running:
                data = await loop.sock_recv(sock, 65535)
                if len(data) < 12 or 64 <= (data[1] & 0x7F) <= 95:
                    continue  # trop court ou paquet RTCP

                highest_seq = max(highest_seq, int.from_bytes(data[2:4], "big"))
                marker = data[1] >> 7
                header_len = 12 + (data[0] & 0x0F) * 4
                if data[0] & 0x10:  # extension
                    ext = int.from_bytes(data[header_len + 2:header_len + 4], "big")
                    header_len += 4 + ext * 4

                nals = []
                depacketize_hevc(data[header_len:], fu_buffer, nals)
                for nal in nals:
                    if nal:
                        au += b"\x00\x00\x00\x01" + nal

                if marker and au:
                    try:
                        for packet in decoder.parse(bytes(au)):
                            for frame in decoder.decode(packet):
                                if not show(frame):
                                    running = False
                    except av.error.InvalidDataError:
                        pass  # trames initiales avant la 1re image cle : on ignore
                    au = bytearray()

                # Receiver Report ~1x/seconde pour garder le flux vivant.
                now = loop.time()
                if now - rtcp_last > 1.0 and local_ssrc and remote_ssrc:
                    sock.sendto(build_rtcp_rr(local_ssrc, remote_ssrc, highest_seq), rtcp_dest)
                    rtcp_last = now
        finally:
            try:
                await service.stop_media_stream(session_id)
            except Exception:
                pass
            sock.close()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(main())
