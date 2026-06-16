FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir ".[dev]"

COPY migrations/ migrations/
COPY alembic.ini .

RUN useradd -m -u 1000 appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "dice_applet.main:app", "--host", "0.0.0.0", "--port", "8000"]
