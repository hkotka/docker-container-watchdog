FROM python:3.7-alpine

RUN pip3 install docker==4.0.2
COPY container-watchdog.py /container-watchdog.py

ENTRYPOINT [ "python3", "/container-watchdog.py" ]