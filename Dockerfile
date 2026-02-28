FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

ENV WISHLISTOPS_HOST=0.0.0.0 \
    PORT=8080 \
    WISHLISTOPS_CONFIG=wishlistops/config.json

EXPOSE 8080

CMD ["sh", "-c", "python -m wishlistops.main setup --config ${WISHLISTOPS_CONFIG:-wishlistops/config.json} --host ${WISHLISTOPS_HOST:-0.0.0.0} --port ${PORT:-8080}"]
