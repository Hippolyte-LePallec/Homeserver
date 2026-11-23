"""Exemple : reçoit les mises à jour de température (sans commande physique)."""
import logging
import threading
from docker_comm import DockerComm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def on_message(message):
    if message["action"] == "temperature_update":
        temperature = message["payload"]["temperature"]
        logging.info("Température reçue : %s °C", temperature)
    else:
        logging.warning("Action inconnue : %s", message["action"])


def main():
    comm = DockerComm(name="chauffage", enable_send=False, enable_receive=True, on_message=on_message)
    try:
        with comm:
            logging.info("Module chauffage prêt (simulation uniquement).")
            threading.Event().wait()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
