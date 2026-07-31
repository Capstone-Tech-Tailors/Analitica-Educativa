FROM ghcr.io/benoitc/gunicorn:25.2.0
LABEL authors="jrios"

USER root
RUN apt-get -y update && apt-get --no-install-suggests --no-install-recommends -y install curl postgresql-client \
    && apt-get -y clean && rm -rf /var/lib/apt/lists/*
USER gunicorn

COPY --chown=gunicorn:gunicorn ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt
COPY --chown=gunicorn:gunicorn ./src ./

ENV GUNICORN_ARGS="--timeout 120 --worker-class uvicorn.workers.UvicornWorker --access-logfile -"
CMD ["app:app"]
