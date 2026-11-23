# Quizly Backend

REST API for **Quizly**, an app that turns YouTube videos into quizzes. The
audio of a video is downloaded with yt-dlp, transcribed locally with Whisper
and turned into a quiz with 10 questions by Gemini Flash.

The frontend is not part of this repository.

## Requirements

- Python 3.12+
- **FFmpeg installed globally** (required by Whisper)
- A Gemini API key from Google AI Studio
- Docker (optional)

### Install FFmpeg

Windows:

```bash
winget install ffmpeg
```

macOS:

```bash
brew install ffmpeg
```

Linux (Debian/Ubuntu):

```bash
sudo apt install ffmpeg
```

Check the installation:

```bash
ffmpeg -version
```

## Setup without Docker

1. Clone the repository

```bash
git clone <repository-url>
```

2. Create and activate a virtual environment

```bash
python -m venv env
```

Windows:

```bash
env\Scripts\activate
```

macOS/Linux:

```bash
source env/bin/activate
```

3. Install the requirements

```bash
pip install -r requirements.txt
```

4. Create the `.env` file and add your Gemini API key

Windows:

```bash
copy .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

5. Set up the database

```bash
python manage.py migrate
```

6. Create an admin user

```bash
python manage.py createsuperuser
```

7. Start the server

```bash
python manage.py runserver
```

## Setup with Docker

Docker Desktop must be running. The image contains FFmpeg and the CPU
version of PyTorch, so it is several GB large.

```bash
docker compose up --build
```

## Endpoints

TODO

## Tests

```bash
coverage run manage.py test
```

```bash
coverage report
```
