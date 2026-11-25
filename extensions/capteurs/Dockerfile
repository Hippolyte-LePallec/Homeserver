FROM python:3.12-slim
WORKDIR /app
COPY common/docker_comm.py ./docker_comm.py
COPY extensions/capteurs/ky001.py ./ky001.py
COPY extensions/capteurs/main.py ./main.py
CMD ["python", "-u", "main.py"]