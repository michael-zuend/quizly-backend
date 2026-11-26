# Small official Python base image (Debian slim, no build tools).
FROM python:3.13-slim

# No .pyc files in the image and log output without buffering.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Security updates of the base image and ffmpeg, which yt-dlp and Whisper
# need to convert and read audio files. The apt lists are removed, so the
# image stays small.
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# All following commands run in /app.
WORKDIR /app

# The requirements are copied first, so Docker can cache this layer as
# long as requirements.txt does not change.
COPY requirements.txt .

# The CPU build of PyTorch is installed first, so Whisper does not pull the
# much larger CUDA build. pip is removed afterwards, so its vendored
# libraries are not part of the runtime image (fewer CVEs in the scan).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y pip

# The source code (.dockerignore keeps .env, the database and git out).
COPY . .

# The app runs as an unprivileged user, never as root. Only the folders the
# app writes to belong to this user.
RUN useradd --create-home appuser \
    && mkdir -p /app/staticfiles /app/tmp_audio /home/appuser/.cache/whisper \
    && chown -R appuser /app/staticfiles /app/tmp_audio /home/appuser/.cache
USER appuser

# Port of Gunicorn inside the container.
EXPOSE 8000

# Migrations and static files on start, then Gunicorn as WSGI server.
# Quiz creation can take several minutes, so the timeout is high.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 600"]
