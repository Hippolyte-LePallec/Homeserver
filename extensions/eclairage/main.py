"""Exemple : reçoit des commandes d'éclairage (simulation uniquement)."""
import logging
import threading
from docker_comm import DockerComm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def on_message(message):
    if message["action"] == "light.turn_on":
        logging.info("Simulation : allumage demandé (%s)", message["payload"])
    elif message["action"] == "light.turn_off":
        logging.info("Simulation : extinction demandée (%s)", message["payload"])
    else:
        logging.warning("Action inconnue : %s", message["action"])


def main():
    comm = DockerComm(name="eclairage", enable_send=False, enable_receive=True, on_message=on_message)
    try:
        with comm:
            logging.info("Module éclairage prêt (simulation uniquement).")
            threading.Event().wait()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
