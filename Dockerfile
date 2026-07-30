FROM ghcr.io/benoitc/gunicorn:24.1.0
LABEL authors="jrios"

USER root
RUN apt-get -y update && apt-get --no-install-suggests --no-install-recommends -y install curl \
    && apt-get -y clean && rm -rf /var/lib/apt/lists/*
USER gunicorn

COPY --chown=gunicorn:gunicorn ./requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt
COPY --chown=gunicorn:gunicorn ./src ./

ENV GUNICORN_CMD_ARGS="--workers=4 --worker-class=uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000"
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

CMD ["gunicorn", "app:app"]
