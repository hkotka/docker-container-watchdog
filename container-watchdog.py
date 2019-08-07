import docker
import logging
import time
import json
import requests
import os
import re
import smtplib
from email.message import EmailMessage

# Set logging options and variables
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO)
pollingIntervalAfterRestart: int = int(os.getenv('POLLING_INTERVAL_AFTER_RESTART', '600'))
pollingInterval: int = int(os.getenv('POLLING_INTERVAL', '20'))
dockerHost: str = os.getenv('DOCKER_HOSTMACHINE', 'UNKNOWN')
slack_webhook_url: str = os.getenv('SLACK_WEBHOOK_URL', '')
emailSender: str = os.getenv('EMAIL_SENDER', '')
emailReceiver: str = os.getenv('EMAIL_RECEIVER', '')
smtpServer: str = os.getenv('SMTP_SERVER', '')
restartedContainers: list = []
notificationContent: dict = {}

# Test and establish connection to docker socket
try:
    client = docker.from_env()
    client.version()
    logging.info("Connection to Docker socket OK")
except Exception as e:
    logging.fatal("%s", e)
    exit()

def sendSlackMessage(notificationContent):
    if slack_webhook_url != "":
        try:
            requests.post(slack_webhook_url, data=json.dumps(notificationContent), headers={'Content-Type': 'application/json'})
            logging.info("Message sent to Slack webhook: %s", notificationContent['text'])
        except Exception as e:
            logging.error("%s", e)

def sendSmtpMessage(notificationContent):
    if emailReceiver != "" and smtpServer != "":
        try:
            emailContent: str = re.sub('[^ :A-Za-z0-9]+', '', notificationContent)
            emailMessage = EmailMessage()
            emailMessage.set_content(emailContent)
            emailMessage['Subject'] = 'Container Watchdog Alert notification'
            emailMessage['From'] = emailSender
            emailMessage['To'] = emailReceiver
            mail = smtplib.SMTP(smtpServer, 25, timeout=40)
            mail.send_message(emailMessage)
            logging.info("Email sent to %s with content: %s", emailReceiver, emailContent)
            mail.quit()
        except Exception as e:
            logging.error("%s", e)

# Check and return container health status. If 'Health' key doesn't exist for container(healthcheck not set), log exception.
def getContainerHealthStatus(container):
    try:
        containerHealthStatus: str = container.attrs['State']['Health']['Status']
    except KeyError:
        containerHealthStatus: str = 'nokey'
    return containerHealthStatus

def restartContainer(container):
    try:
        container.restart()
        logging.info("Restarted container: %s",container.name)
        notificationContent['text'] = ("[Container watchdog]: has *_restarted_* container: [ *_{0}_* ] which had healthstatus: [ _{1}_ ] and state:"
                                        " [ _{2}_ ] on hostmachine [ _{3}_ ]".format(container.name, containerHealthStatus,
                                         containerStatus, dockerHost))
        if container.short_id not in restartedContainers:
            restartedContainers.append(container.short_id)
    except Exception as e:
        logging.fatal("%s", e)
        notificationContent['text'] = ("[Container watchdog]: Docker daemon failed to restart container *{0}* on hostmachine *{1}*"
                                        " with error message: _{2}_".format(container.name, dockerHost, e))

def containerRecovered(container):
    logging.info("Container %s has recovered and is now healthy!", container.name)
    notificationContent['text'] = ("[Container watchdog]: Container: [ *_{0}_* ] has *recovered* with healthstatus: [ _{1}_ ] and state: [ _{2}_ ]"
                                    " on hostmachine [ _{3}_ ]".format(container.name, containerHealthStatus, containerStatus, dockerHost))
    restartedContainers.remove(container.short_id)


# Run loop indefinetly polling every 30 seconds normally or in 15 minutes after watchdog has restarted a container.
while True:
    restartStatus: bool = False
    ContainerList: list = client.containers.list()
    for container in ContainerList:
        containerStatus = container.status
        containerHealthStatus: str = getContainerHealthStatus(container)
        # Check if the container was restarted previously and is now healthy. Send Slack/email notification. Remove from a list of restarted containers
        if container.short_id in restartedContainers and containerHealthStatus == 'healthy':
            containerRecovered(container)
            sendSlackMessage(notificationContent)
            sendSmtpMessage(notificationContent['text'])
        #  If container is in unhealthy or exited status, restart and end Slack/Email notification. Add container to list of restarted containers.
        elif containerHealthStatus == 'unhealthy':
            logging.error("Found container in unhealthy state! Container: %s has health status: %s and container status: %s",
                         container.name, containerHealthStatus, containerStatus)
            restartContainer(container)
            sendSlackMessage(notificationContent)
            sendSmtpMessage(notificationContent['text'])
            restartStatus = True
        logging.debug('%s - %s - %s', container.name, containerHealthStatus, containerStatus)

    # Wait to poll again, longer if restarts were done in previous loop
    if restartStatus is True:
        logging.info("Waiting %s seconds until next polling, because container was restarted", pollingIntervalAfterRestart)
        time.sleep(pollingIntervalAfterRestart)
    elif restartStatus is False:
        logging.info("All containers are in healthy state!")
        time.sleep(pollingInterval)