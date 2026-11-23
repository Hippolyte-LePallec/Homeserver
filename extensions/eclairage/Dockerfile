FROM python:3.12-slim
WORKDIR /app
COPY common/docker_comm.py ./docker_comm.py
COPY extensions/eclairage/main.py ./main.py
CMD ["python", "-u", "main.py"]
