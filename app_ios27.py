"""
Affiche l'ecran de l'iPad en direct dans une fenetre, en FLUIDE (flux video HEVC).

Juste la video, sans aucune interface. Reserve a iPadOS 27+ ; pour les versions
plus anciennes, utiliser app.py (captures, plus lent).

Fonctionnement : le serveur de mirroring de pymobiledevice3 (serve-web) tourne en
arriere-plan, sans navigateur. Il gere la session video avec l'iPad (accuses de
reception, images cles, reprise apres coupure) ; ce programme lit son flux
/stream.bin, le decode avec PyAV et affiche la derniere image recue.

Prerequis : tunnel lance en admin (le plus simple : passer par mirror.bat).

Touches : f = plein ecran, q ou Echap = quitter.
L'image suit automatiquement l'orientation de l'iPad.
"""

import asyncio
import base64
import subprocess
import sys
import threading
import time

import av
import cv2
import requests
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.springboard import InterfaceOrientation, SpringBoardServicesService

PORT = 8765
URL = f"http://127.0.0.1:{PORT}"
WINDOW = "iPad"

ROTATION = {
    InterfaceOrientation.PORTRAIT: None,
    InterfaceOrientation.PORTRAIT_UPSIDE_DOWN: cv2.ROTATE_180,
    InterfaceOrientation.LANDSCAPE: cv2.ROTATE_90_COUNTERCLOCKWISE,
    InterfaceOrientation.LANDSCAPE_HOME_TO_LEFT: cv2.ROTATE_90_CLOCKWISE,
}


class State:
    def __init__(self):
        self.running = True
        self.frame = None  # derniere image decodee (av.VideoFrame)
        self.rotation = None
        self.error = None


def start_server():
    """Lance serve-web en arriere-plan (localhost uniquement, sans son)."""
    return subprocess.Popen(
        [sys.executable, "-m", "pymobiledevice3", "developer", "core-device", "display",
         "serve-web", "--bind", "127.0.0.1", "--http-port", str(PORT), "--no-audio"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def fetch_hvcc(state, timeout=30):
    """Attend que le flux soit pret et renvoie la configuration du decodeur (hvcC)."""
    deadline = time.time() + timeout
    while state.running and time.time() < deadline:
        try:
            r = requests.get(URL + "/codec", timeout=5)
            if r.ok and r.json().get("description"):
                return base64.b64decode(r.json()["description"])
        except requests.RequestException:
            pass
        time.sleep(0.5)
    return None


def new_decoder(hvcc):
    decoder = av.CodecContext.create("hevc", "r")
    decoder.extradata = hvcc
    decoder.thread_type = "AUTO"
    return decoder


def receive(state):
    """Lit /stream.bin : suite de messages [taille 4 o][type 1 o][image HEVC].
    type 0 = image cle, 1 = image delta, 2 = image cle apres reinitialisation."""
    while state.running:
        hvcc = fetch_hvcc(state)
        if hvcc is None:
            state.error = "Le flux video n'a pas demarre (tunnel lance ? iPad deverrouille ?)"
            return
        try:
            with requests.get(URL + "/stream.bin", stream=True, timeout=(5, 30)) as r:
                r.raise_for_status()
                decoder = new_decoder(hvcc)
                buf = bytearray()
                for chunk in r.iter_content(chunk_size=None):
                    if not state.running:
                        return
                    buf += chunk
                    while len(buf) >= 5:
                        size = int.from_bytes(buf[:4], "big")
                        if len(buf) < 4 + size:
                            break
                        kind, au = buf[4], bytes(buf[5:4 + size])
                        del buf[:4 + size]
                        if kind == 2:
                            decoder = new_decoder(fetch_hvcc(state) or hvcc)
                        try:
                            for frame in decoder.decode(av.Packet(au)):
                                state.frame = frame
                        except av.error.InvalidDataError:
                            pass  # image abimee : la suivante image cle resynchronise
        except requests.RequestException:
            time.sleep(1)  # coupure : on se reconnecte


def watch_orientation(state):
    """Interroge l'orientation de l'iPad ~2x/s pour tourner l'image."""
    async def poll():
        springboard = SpringBoardServicesService(lockdown=await create_using_usbmux())
        while state.running:
            try:
                state.rotation = ROTATION.get(await springboard.get_interface_orientation())
            except Exception:
                pass
            await asyncio.sleep(0.5)

    try:
        asyncio.run(poll())
    except Exception:
        pass  # sans orientation, l'image reste en portrait


def fit_window(img):
    """Taille de fenetre : l'image entiere a ~85 % de la hauteur de l'ecran."""
    h, w = img.shape[:2]
    target = 900 if h >= w else 700
    cv2.resizeWindow(WINDOW, int(w * target / h), target)


def main():
    state = State()
    server = start_server()
    threading.Thread(target=receive, args=(state,), daemon=True).start()
    threading.Thread(target=watch_orientation, args=(state,), daemon=True).start()

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    print("Connexion au flux video de l'iPad...  (f = plein ecran, q/Echap = quitter)")

    shown, shape, fullscreen = None, None, False
    frames, t0 = 0, time.time()
    try:
        while True:
            frame = state.frame
            if frame is not None and frame is not shown:
                shown = frame
                img = frame.to_ndarray(format="bgr24")
                if state.rotation is not None:
                    img = cv2.rotate(img, state.rotation)
                if img.shape != shape and not fullscreen:
                    fit_window(img)
                shape = img.shape
                cv2.imshow(WINDOW, img)
                frames += 1

            now = time.time()
            if now - t0 >= 1:
                cv2.setWindowTitle(WINDOW, f"iPad  -  {frames / (now - t0):.0f} fps")
                frames, t0 = 0, now

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("f"):
                fullscreen = not fullscreen
                cv2.setWindowProperty(WINDOW, cv2.WND_PROP_FULLSCREEN,
                                      cv2.WINDOW_FULLSCREEN if fullscreen else cv2.WINDOW_NORMAL)
            if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1 and shown is not None:
                break  # fenetre fermee avec la croix
            if state.error:
                print("ERREUR :", state.error)
                break
    finally:
        state.running = False
        server.terminate()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
