FROM python:3.12-slim

# Installation de Chromium, xdotool (contrôle clavier/média X11) et alsa-utils (volume)
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    xdotool \
    alsa-utils \
    libgl1-mesa-dri \
    fonts-liberation \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copie de la bibliothèque commune et des fichiers de l'extension
COPY common/docker_comm.py ./docker_comm.py
COPY extensions/kiosk-tv/launcher.html ./launcher.html
COPY extensions/kiosk-tv/main.py ./main.py
COPY extensions/kiosk-tv/entrypoint.sh ./entrypoint.sh

RUN chmod +x ./entrypoint.sh

CMD ["./entrypoint.sh"]