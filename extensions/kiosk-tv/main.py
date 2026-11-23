"""Extension kiosk-tv : interface Google TV et contrôle multimédia via DockerComm."""
import logging
import os
import subprocess
import threading
from docker_comm import DockerComm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

LAUNCHER_URL = "file:///app/launcher.html"

# Catalogue d'applications prédéfinies
APPS = {
    "home": LAUNCHER_URL,
    "youtube": "https://www.youtube.com/tv",
    "netflix": "https://www.netflix.com",
    "prime": "https://www.primevideo.com",
    "twitch": "https://www.twitch.tv",
    "plex": "https://app.plex.tv",
}

# User-Agent Cobalt / Android TV pour débloquer l'interface TV de YouTube (/tv)
GOOGLE_TV_UA = (
    "Mozilla/5.0 (Linux; Android 12; Chromecast) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 CrKey/1.56.500000"
)

browser_proc = None
browser_lock = threading.Lock()
comm = None


def launch_browser(url: str):
    """Lance ou relance Chromium en plein écran (mode Kiosk) sur l'URL cible."""
    global browser_proc
    with browser_lock:
        stop_browser_locked()
        cmd = [
            "chromium",
            "--no-sandbox",
            "--kiosk",
            "--incognito",
            "--noerrdialogs",
            "--disable-infobars",
            "--disable-session-crashed-bubble",
            "--autoplay-policy=no-user-gesture-required",
            "--check-for-update-interval=31536000",
            f"--user-agent={GOOGLE_TV_UA}",
            url,
        ]
        try:
            browser_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logging.info("Navigateur Google TV ouvert sur : %s", url)
        except FileNotFoundError:
            logging.warning("Chromium non disponible (mode simulation sans affichage : %s)", url)


def stop_browser_locked():
    """Ferme proprement le processus Chromium actif."""
    global browser_proc
    if browser_proc and browser_proc.poll() is None:
        browser_proc.terminate()
        try:
            browser_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            browser_proc.kill()
        logging.info("Navigateur Google TV arrêté.")
    browser_proc = None


def send_key(key: str):
    """Envoie une touche X11 à la fenêtre active via xdotool."""
    try:
        subprocess.run(["xdotool", "key", key], check=True, timeout=2)
        logging.info("Touche envoyée : %s", key)
    except Exception as exc:
        logging.warning("Impossible d'envoyer la touche %s : %s", key, exc)


def set_volume(level: int):
    """Ajuste le volume matériel via ALSA (0 à 100%)."""
    level = max(0, min(100, int(level)))
    try:
        subprocess.run(["amixer", "sset", "Master", f"{level}%"], check=True, timeout=2)
        logging.info("Volume réglé à %d%%", level)
    except Exception as exc:
        logging.warning("Impossible de régler le volume ALSA (%d%%) : %s", level, exc)


def on_message(message):
    action = message["action"]
    payload = message.get("payload") or {}

    if action == "tv.home":
        launch_browser(LAUNCHER_URL)

    elif action == "tv.open_app":
        app_name = str(payload.get("app", "home")).lower()
        target_url = APPS.get(app_name, LAUNCHER_URL)
        launch_browser(target_url)

    elif action == "tv.open_url":
        url = payload.get("url")
        if url:
            launch_browser(url)
        else:
            logging.warning("Paramètre 'url' manquant pour tv.open_url")

    elif action == "tv.key":
        # Exemples : "Up", "Down", "Left", "Right", "Return", "Escape", "BackSpace", "space"
        key = payload.get("key", "space")
        send_key(key)

    elif action == "tv.play_pause":
        send_key("space")

    elif action == "tv.volume":
        level = payload.get("level", 50)
        set_volume(level)

    elif action == "tv.mute":
        try:
            subprocess.run(["amixer", "sset", "Master", "toggle"], check=True, timeout=2)
            logging.info("Mute/Unmute basculé.")
        except Exception as exc:
            logging.warning("Échec toggle mute : %s", exc)

    elif action == "tv.stop":
        with browser_lock:
            stop_browser_locked()

    else:
        logging.warning("Action inconnue : %s", action)


def main():
    global comm
    comm = DockerComm(
        name="kiosk-tv",
        enable_send=True,
        enable_receive=True,
        on_message=on_message,
    )
    try:
        with comm:
            logging.info("Module kiosk-tv prêt sur TCP 5000.")
            # Lance l'accueil Google TV au démarrage si un serveur X11/XWayland est détecté
            if os.environ.get("DISPLAY"):
                launch_browser(LAUNCHER_URL)
            else:
                logging.info("Aucun DISPLAY détecté au démarrage : en attente de commandes.")
            threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        with browser_lock:
            stop_browser_locked()


if __name__ == "__main__":
    main()