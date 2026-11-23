# HomeSystem — prototype domotique sur Raspberry Pi 4

Architecture Docker modulaire : un maître, une bibliothèque Python commune pour sockets TCP/JSON et trois extensions d'exemple.

## Prérequis

- Raspberry Pi 4 avec OS 64 bits et Docker Engine + plugin Docker Compose (également exécutable sur PC avec Docker).
- Accès à Internet au premier build pour télécharger `python:3.12-slim`.

## Démarrer

Depuis le dossier `HomeSystem` :

```bash
docker compose up --build -d
docker compose logs -f
```

Arrêter les conteneurs :

```bash
docker compose down
```

Le conteneur `capteurs` envoie toutes les cinq secondes une température simulée au service `chauffage` sur TCP 5000. Le module `eclairage` attend des commandes d'exemple ; le maître affiche les messages qui lui sont destinés.

## Structure

```text
HomeSystem/
├── master/
│   ├── Dockerfile
│   └── main.py
├── common/
│   └── docker_comm.py
├── extensions/
│   ├── capteurs/
│   │   ├── Dockerfile
│   │   └── main.py
│   ├── chauffage/
│   │   ├── Dockerfile
│   │   └── main.py
│   └── eclairage/
│       ├── Dockerfile
│       └── main.py
├── compose.yaml
├── .dockerignore
├── .gitignore
└── README.md
```

## Bibliothèque commune

```python
from docker_comm import DockerComm

comm = DockerComm(
    name="mon_service",
    enable_send=True,
    enable_receive=True,
    on_message=lambda msg: print(msg),
)
comm.start()
comm.send("chauffage", "temperature_update", {"temperature": 21.0})
comm.stop()
```

Les options `enable_send` et `enable_receive` sont indépendantes. Le port interne par défaut est `5000` pour chaque conteneur. Les services sont joignables par leur nom DNS sur le réseau privé `domotique` ; il n'est pas nécessaire de publier un port sur l'hôte.

Les messages sont des objets JSON, encodés en UTF-8, terminés par un saut de ligne :

```json
{"id":"abc123","source":"capteurs","destination":"chauffage","action":"temperature_update","payload":{"temperature":19.5}}
```

L'ACK `received` confirme seulement que le callback distant s'est terminé sans exception ; ce n'est **pas** une confirmation de l'exécution d'un ordre physique. `send()` bloque pendant la tentative de communication, au maximum le délai de connexion et de lecture configuré (3 s par défaut chacun).

## Ajouter une extension

1. Créer `extensions/nom_service/main.py` et son `Dockerfile` sur le modèle d'une extension existante.
2. Déclarer le service dans `compose.yaml` avec `build.context: .` et `build.dockerfile: extensions/nom_service/Dockerfile`.
3. Choisir les drapeaux d'émission et réception, et déclarer le callback métier si besoin.
4. Lancer `docker compose up --build -d`.

## Portée de ce prototype

- Le **maître est une base de réception/supervision** : le lancement dynamique d'autres conteneurs par le maître n'est pas encore implémenté. Dans cette version, **Docker Compose** lance les conteneurs.
- `capteurs`, `chauffage` et `eclairage` sont des démonstrations : aucun matériel réel n'est piloté.
- Les sockets ne sont **pas authentifiés ni chiffrés**. Garder le réseau privé, ne pas publier les ports et ne pas exposer ces services à Internet. Ne pas monter le socket Docker dans un conteneur sans analyser les risques de privilèges.
- Pas de persistance ni de retransmission durable des messages. Prévoir ensuite validation des actions, versions de protocole, authentification et découverte des services.
