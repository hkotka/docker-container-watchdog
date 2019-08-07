# docker-container-watchdog
The script monitors Docker host's container health status, restarting unhealthy containers and alerting via Slack webhook and email.

Script can be deployed to Docker host machine either as Docker container(preferred) or simply by running the script. The script needs access to host machines /var/run/docker.sock. The example docker-compose.yml is pre-configured to mount docker.sock from host machine.  

To enable notifications via Slack, provide webhook url via ENV.

To enable notifications via email, provide smtp server address and email receiver information via ENVs.

Following environment variables can be passed to script to change polling interval and notification channel settings.

``DOCKER_HOSTMACHINE`` Used to identify which hostmachine notifications are sent.  
``POLLING_INTERVAL`` Container status polling interval in seconds.  
``POLLING_INTERVAL_AFTER_RESTART`` - Polling interval after container has been restarted in last polling. Should be a bit higher than normal interval to give restarted container time to recover.  
``SLACK_WEBHOOK_URL`` Send notifications to Slack webhook url.  
``SMTP_SERVER`` Email server for sending smtp messages.  
``EMAIL_RECEIVER`` Receiver's email address.  
