FROM python:3.7-alpine

RUN pip3 install docker==4.0.2
COPY container_watchdog.py /container_watchdog.py

ENTRYPOINT [ "python3", "/container_watchdog.py" ]