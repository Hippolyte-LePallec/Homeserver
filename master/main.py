"""Maître : point de départ de la supervision (orchestration à développer)."""
import logging
import threading
from docker_comm import DockerComm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def on_message(message):
    logging.info("Message reçu de %s : %s %s", message["source"], message["action"], message["payload"])


def main():
    comm = DockerComm(name="master", enable_send=True, enable_receive=True, on_message=on_message)
    try:
        with comm:
            logging.info("Maître prêt. Gestion dynamique des conteneurs non implémentée dans cette base.")
            threading.Event().wait()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
