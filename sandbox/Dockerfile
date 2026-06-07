FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pytest==8.2.2 \
    pytest-cov==5.0.0 \
    pytest-asyncio==0.23.7 \
    httpx==0.27.0 \
    bandit==1.7.9 \
    locust==2.29.0

RUN useradd -m -s /bin/bash sandbox
RUN mkdir -p /workspace/output && chown sandbox:sandbox /workspace/output

WORKDIR /workspace
USER sandbox

ENTRYPOINT ["tail", "-f", "/dev/null"]
