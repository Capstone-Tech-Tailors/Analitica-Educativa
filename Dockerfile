FROM ghcr.io/benoitc/gunicorn:25.2.0
LABEL authors="jrios"

COPY --chown=gunicorn:gunicorn ./requirements.txt /tmp/requirements.txt
COPY --chown=gunicorn:gunicorn ./src/ ./
COPY --chown=gunicorn:gunicorn ./alembic.ini ./
COPY --chown=gunicorn:gunicorn ./alembic/ ./alembic/

RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm -f /tmp/requirements.txt

USER root

RUN apt-get -y update && apt-get --no-install-suggests --no-install-recommends -y install curl postgresql-client \
    && apt-get -y clean && rm -rf /var/lib/apt/lists/* \
    && mv /home/gunicorn/.local/bin/alembic /usr/local/bin/alembic \
    && chown root:root /usr/local/bin/alembic \
    && rm -rf /home/gunicorn/.local/bin

USER gunicorn

ENV GUNICORN_ARGS="--timeout 120 --worker-class uvicorn.workers.UvicornWorker --access-logfile -"
CMD ["app:app"]
