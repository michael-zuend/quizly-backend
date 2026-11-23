FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Security updates and ffmpeg, which Whisper needs to read audio files.
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# The CPU build of PyTorch is installed first, so Whisper does not pull the
# much larger CUDA build. pip is removed afterwards, so its vendored
# libraries are not part of the runtime image.
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y pip

COPY . .

RUN useradd --create-home appuser \
    && mkdir -p /app/staticfiles /app/tmp_audio /home/appuser/.cache/whisper \
    && chown -R appuser /app /home/appuser/.cache
USER appuser

EXPOSE 8000

# Quiz creation can take several minutes, so the Gunicorn timeout is high.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 600"]
