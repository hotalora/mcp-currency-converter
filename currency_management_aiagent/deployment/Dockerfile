FROM python:3.13-slim AS builder

WORKDIR /build

COPY pyproject.toml ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/python -c "import subprocess,sys,tomllib; dependencies=tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']; subprocess.check_call([sys.executable,'-m','pip','install','--no-cache-dir',*dependencies])"

FROM python:3.13-slim AS runtime

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY . .

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app app

USER 10001:10001

EXPOSE 8003

CMD ["python", "main.py"]
