FROM ghcr.io/benoitc/gunicorn:24.1.0
LABEL authors="jrios"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home appuser
WORKDIR /home/appuser/app

COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt
COPY --chown=appuser:appuser src/ ./

USER appuser
ENV GUNICORN_CMD_ARGS="--workers=4 --worker-class=uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000"
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

CMD ["gunicorn", "app:app"]
