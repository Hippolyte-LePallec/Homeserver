import glob
import logging

BASE_DIR = "/sys/bus/w1/devices/"


class KY001Sensor:
    """Lecteur de température pour module KY-001 (DS18B20 sur bus 1-Wire)."""

    def __init__(self, device_id: str | None = None, base_dir: str = BASE_DIR):
        self.device_file = self._resolve_device_file(device_id, base_dir)

    @staticmethod
    def _resolve_device_file(device_id: str | None, base_dir: str) -> str:
        if device_id:
            return f"{base_dir.rstrip('/')}/{device_id}/w1_slave"

        devices = sorted(glob.glob(f"{base_dir.rstrip('/')}/28-*"))
        if not devices:
            raise FileNotFoundError(
                f"Aucun capteur 1-Wire (28-*) détecté dans {base_dir}. "
                "Vérifie l'activation 1-Wire et le câblage du KY-001."
            )
        return f"{devices[0]}/w1_slave"

    def read_temperature(self, decimals: int | None = 1) -> float | None:
        """Retourne la température en °C, ou None si la lecture est invalide."""
        try:
            with open(self.device_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError as exc:
            logging.warning("Erreur d'accès au capteur (%s) : %s", self.device_file, exc)
            return None

        if len(lines) < 2 or not lines[0].strip().endswith("YES"):
            logging.warning("CRC invalide ou trame incomplète sur %s", self.device_file)
            return None

        equals_pos = lines[1].find("t=")
        if equals_pos == -1:
            logging.warning("Valeur 't=' introuvable dans : %s", lines[1].strip())
            return None

        temp_c = float(lines[1][equals_pos + 2 :].strip()) / 1000.0
        return round(temp_c, decimals) if decimals is not None else temp_c