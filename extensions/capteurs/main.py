"""Lit la température via le module ky001 et l'envoie toutes les 5 secondes."""
import logging
import os
import time
from docker_comm import DockerComm
from ky001 import KY001Sensor

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def wait_for_sensor() -> KY001Sensor:
    device_id = os.environ.get("KY001_DEVICE_ID") or None
    while True:
        try:
            return KY001Sensor(device_id=device_id)
        except FileNotFoundError as exc:
            logging.warning("%s Nouvelle tentative dans 5 s.", exc)
            time.sleep(5)


def main():
    comm = DockerComm(name="capteurs", enable_send=True, enable_receive=False)

    try:
        sensor = wait_for_sensor()
        logging.info("Capteur KY-001 prêt (%s)", sensor.device_file)

        while True:
            temperature = sensor.read_temperature(decimals=1)
            if temperature is not None:
                success = comm.send(
                    "chauffage",
                    "temperature_update",
                    {"temperature": temperature},
                )
                logging.info("Température %.1f °C envoyée : %s", temperature, success)
            else:
                logging.warning("Lecture ignorée pour ce cycle.")

            time.sleep(5)
    except KeyboardInterrupt:
        logging.info("Arrêt du service capteurs.")


if __name__ == "__main__":
    main()