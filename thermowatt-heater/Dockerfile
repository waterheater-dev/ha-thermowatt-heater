ARG BUILD_FROM
FROM $BUILD_FROM

# Install python and dependencies
RUN apk add --no-cache python3 py3-pip

# Install python libraries
RUN pip3 install paho-mqtt requests urllib3 --break-system-packages

ENV PYTHONUNBUFFERED=1
# Copy data for add-on
COPY run.sh /
COPY thermowatt_bridge.py /
COPY client.crt /
COPY client.key /
COPY root.pem /

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
