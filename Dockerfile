# Job Cloud Run « analyse » : python -m chessan.worker <pseudo>
FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
 && curl -sSL https://github.com/official-stockfish/Stockfish/releases/download/sf_19/stockfish-linux-x86-64-universal.tar.gz \
    | tar xz -C /tmp \
 && mkdir -p /app/bin && cp /tmp/stockfish/stockfish-linux-x86-64-universal /app/bin/stockfish && rm -rf /tmp/stockfish \
 && apt-get purge -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir chess==1.11.2 firebase-admin==7.7.0
WORKDIR /app
COPY config.toml run.py ./
COPY chessan ./chessan
COPY templates ./templates
ENTRYPOINT ["python", "-m", "chessan.worker"]
