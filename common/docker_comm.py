"""Communication TCP JSON entre services d'un même réseau Docker privé."""

import json
import logging
import socket
import socketserver
import threading
import uuid
from typing import Callable, Optional

LOGGER = logging.getLogger(__name__)
DEFAULT_PORT = 5000
MAX_MESSAGE_SIZE = 1024 * 1024  # 1 Mio (hors délimiteur de ligne)


class _TCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    block_on_close = False


class DockerComm:
    """Client/serveur TCP. Émission et réception activables séparément."""

    def __init__(
        self,
        name: str,
        enable_send: bool = True,
        enable_receive: bool = True,
        port: int = DEFAULT_PORT,
        on_message: Optional[Callable[[dict], None]] = None,
        bind_host: str = "0.0.0.0",
    ):
        if not isinstance(name, str) or not name:
            raise ValueError("Le nom du service est obligatoire.")
        self.name = name
        self.enable_send = enable_send
        self.enable_receive = enable_receive
        self.port = port
        self.on_message = on_message
        self.bind_host = bind_host
        self._server = None
        self._thread = None

    def start(self):
        """Lance la réception dans un thread, si elle est activée."""
        if not self.enable_receive or self._server is not None:
            return
        owner = self

        class MessageHandler(socketserver.StreamRequestHandler):
            def handle(self):
                try:
                    self.request.settimeout(5.0)
                    raw = self.rfile.readline(MAX_MESSAGE_SIZE + 2)
                    if not raw or len(raw) > MAX_MESSAGE_SIZE + 1:
                        raise ValueError("Message vide ou trop volumineux.")
                    if not raw.endswith(b"\n"):
                        raise ValueError("Message incomplet.")
                    if len(raw) - 1 > MAX_MESSAGE_SIZE:
                        raise ValueError("Message trop volumineux.")
                    message = json.loads(raw.decode("utf-8"))
                    if not isinstance(message, dict):
                        raise ValueError("Un objet JSON est attendu.")
                    required = ("id", "source", "destination", "action", "payload")
                    if any(key not in message for key in required):
                        raise ValueError("Champs obligatoires manquants.")
                    if message["destination"] != owner.name:
                        raise ValueError("Mauvais destinataire.")
                    if owner.on_message is not None:
                        owner.on_message(message)
                    response = {"status": "received", "id": message["id"]}
                except Exception as exc:
                    LOGGER.warning("Erreur de réception (%s) : %s", owner.name, exc)
                    response = {"status": "error", "reason": str(exc)}
                try:
                    self.wfile.write(json.dumps(response).encode("utf-8") + b"\n")
                    self.wfile.flush()
                except OSError:
                    LOGGER.debug("Connexion fermée avant l'accusé de réception.")

        self._server = _TCPServer((self.bind_host, self.port), MessageHandler)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name=f"comm-{self.name}",
            daemon=True,
        )
        self._thread.start()
        LOGGER.info("%s écoute sur le port %s", self.name, self.port)

    def send(
        self,
        destination: str,
        action: str,
        payload=None,
        port: int = DEFAULT_PORT,
        timeout: float = 3.0,
    ) -> bool:
        """Envoie un message à un service DNS Docker et attend son ACK.

        True indique que le callback distant a terminé sans erreur,
        pas que l'effet métier/physique a été confirmé.
        """
        if not self.enable_send:
            raise RuntimeError(f"L'émission est désactivée pour {self.name}.")
        if not destination or not action:
            raise ValueError("Destination et action obligatoires.")
        message = {
            "id": uuid.uuid4().hex,
            "source": self.name,
            "destination": destination,
            "action": action,
            "payload": {} if payload is None else payload,
        }
        data = json.dumps(message, ensure_ascii=False).encode("utf-8") + b"\n"
        if len(data) - 1 > MAX_MESSAGE_SIZE:
            raise ValueError("Message trop volumineux.")
        try:
            with socket.create_connection((destination, port), timeout=timeout) as sock:
                sock.settimeout(timeout)
                sock.sendall(data)
                with sock.makefile("rb") as reader:
                    raw = reader.readline(4096)
                if not raw or not raw.endswith(b"\n"):
                    raise ValueError("Accusé de réception absent ou incomplet.")
                response = json.loads(raw.decode("utf-8"))
                return (
                    isinstance(response, dict)
                    and response.get("status") == "received"
                    and response.get("id") == message["id"]
                )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            LOGGER.warning("Échec d'envoi %s -> %s : %s", self.name, destination, exc)
            return False

    def stop(self):
        """Arrête proprement le serveur."""
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join()
        self._server = None
        self._thread = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()
