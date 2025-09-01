FROM python:3.11-slim

WORKDIR /app

# Install system deps (optional: git for future enhancements)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY cli.py /app/cli.py

# Install as an editable package
RUN pip install --no-cache-dir .

ENTRYPOINT ["prompt-scan"]
CMD ["--help"]



