# Quizly Backend

REST API for **Quizly**, an app that turns YouTube videos into quizzes. The
audio of a video is downloaded with yt-dlp, transcribed locally with Whisper
and turned into a quiz with 10 questions by Gemini Flash.

The frontend is not part of this repository.

## Requirements

- Python 3.13+
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
git clone https://github.com/michael-zuend/quizly-backend.git
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

3. Install the requirements (CPU PyTorch first, it is much smaller)

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

```bash
pip install -r requirements.txt
```

4. Create the `.env` file, then set `SECRET_KEY` and `GEMINI_API_KEY`.
   A secret key can be generated with
   `python -c "import secrets; print(secrets.token_urlsafe(50))"`

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

Docker Desktop must be running and the `.env` file must exist (step 4
above). The image contains FFmpeg and the CPU version of PyTorch, so it is
several GB large.

```bash
docker compose up --build
```

Create an admin user inside the container:

```bash
docker compose exec backend python manage.py createsuperuser
```

Stop the containers:

```bash
docker compose down
```

### Why Docker

- **Same environment everywhere**: Python, FFmpeg and all packages have
  the same versions on every machine. Nobody has to install FFmpeg or
  PyTorch manually.
- **PostgreSQL** runs in its own container, like in production. SQLite is
  only used for local development without Docker.
- **Whisper model cache**: the model is downloaded once and kept in the
  `whisper_cache` volume.

### Docker security

- Base image `python:3.13-slim` with all Debian security updates
  (`apt-get upgrade`).
- The app runs as the unprivileged user `appuser`, not as root. The
  source code is not writable for this user.
- `pip` is removed from the final image, it is not needed at runtime.
- Only the CPU build of PyTorch is installed (much smaller image, fewer
  libraries that can have vulnerabilities).
- `.env`, the local database and the git history are excluded with
  `.dockerignore`, so no secrets end up in the image.
- The database has no port mapping and is only reachable inside the
  Docker network.
- The backend port is bound to `127.0.0.1` only.
- `no-new-privileges` and `cap_drop: ALL`: the container process cannot
  gain more rights.

## CI/CD

Every push and pull request runs the GitHub Actions pipeline
(`.github/workflows/ci.yml`):

| Job | What it checks |
|---|---|
| Lint and tests | flake8 (PEP 8), missing migrations, all tests on PostgreSQL, coverage of at least 95 % |
| Django deploy checks | `manage.py check --deploy` with production settings |
| Security scans | Bandit (insecure code patterns), pip-audit (known CVEs in dependencies) |
| Secret scan | Gitleaks scans the whole git history for leaked keys |
| Docker image scan | Builds the image and scans it with Trivy (critical and high CVEs) |

All GitHub Actions are pinned to full commit hashes, because version tags
can be moved to other (malicious) commits. The workflow token only has
read rights.

Note: yt-dlp is pinned to `2026.10.26` instead of `2025.07.21` from the
project checklist, because the older version has known vulnerabilities.

## Endpoints

Base URL: `http://127.0.0.1:8000/api/`

Authentication works with two HttpOnly cookies that are set on login:
`access_token` (15 minutes) and `refresh_token` (1 day). The frontend has to
send requests with `credentials: "include"`.

### Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/register/` | no | Create a user account |
| POST | `/api/login/` | no | Log in, sets both JWT cookies |
| POST | `/api/logout/` | yes | Blacklists the refresh token, deletes the cookies |
| POST | `/api/token/refresh/` | refresh cookie | Sets a new access token cookie |

Register request:

```json
{"username": "user", "email": "user@example.com", "password": "Str0ngPassw0rd!", "confirmed_password": "Str0ngPassw0rd!"}
```

Login request:

```json
{"username": "user", "password": "Str0ngPassw0rd!"}
```

Login response (200):

```json
{"detail": "Login successfully!", "user": {"id": 1, "username": "user", "email": "user@example.com"}}
```

Status codes: `201` registered, `200` success, `400` invalid data,
`401` wrong credentials or invalid/blacklisted token, `429` too many
requests.

### Quizzes

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/quizzes/` | Create a quiz from a YouTube URL |
| GET | `/api/quizzes/` | List all quizzes of the logged in user |
| GET | `/api/quizzes/{id}/` | Get one quiz |
| PATCH | `/api/quizzes/{id}/` | Change `title` and/or `description` |
| DELETE | `/api/quizzes/{id}/` | Delete the quiz and its questions |

All quiz endpoints require the login cookies.

Create request:

```json
{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
```

Quiz response:

```json
{
  "id": 1,
  "title": "Quiz title",
  "description": "Quiz description",
  "created_at": "2026-11-23T12:00:00Z",
  "updated_at": "2026-11-23T12:00:00Z",
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "questions": [
    {
      "id": 1,
      "question_title": "Question 1?",
      "question_options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Option A",
      "created_at": "2026-11-23T12:00:00Z",
      "updated_at": "2026-11-23T12:00:00Z"
    }
  ]
}
```

Status codes: `201` created, `200` success, `204` deleted, `400` invalid
URL or video not available, `401` not logged in, `403` quiz of another
user, `404` quiz not found, `429` too many quizzes, `500` transcription or
Gemini failed.

### How a quiz is created

1. The URL is validated: only `youtube.com` and `youtu.be` links with a
   valid 11 character video id are accepted.
2. yt-dlp downloads only the audio into a temporary folder, FFmpeg
   converts it to mp3.
3. Whisper transcribes the audio locally (no audio leaves the server).
4. The transcript is sent to Gemini Flash, which returns 10 questions with
   4 options each as JSON.
5. The JSON is validated and saved in one database transaction.
6. The temporary audio folder is deleted, also when an error happens.

Creating a quiz takes between several seconds and a few minutes, depending
on the video length and the Whisper model.

## Security measures

### Authentication

- JWT tokens are stored in **HttpOnly cookies**, JavaScript cannot read
  them, so an XSS bug cannot steal the tokens.
- Cookies use `SameSite=Lax` (no cookies on cross-site POST requests,
  protection against CSRF) and `Secure` in production (HTTPS only).
- Short access token lifetime (15 minutes), refresh token 1 day.
- On logout the refresh token is put on a **blacklist** and cannot be used
  again.
- Login errors are generic ("Invalid username or password."), so nobody
  can find out which usernames exist.
- Passwords are hashed by Django and checked by the Django password
  validators (length, common passwords, similarity to username).
- Login and registration are **rate limited** (5 per minute per client).

### Quiz creation

- **URL allowlist**: only YouTube hosts and valid video ids are accepted.
  This prevents Server Side Request Forgery (the server cannot be used to
  load internal or other URLs).
- The URL is normalized to `https://www.youtube.com/watch?v=<id>`, so
  playlists and extra parameters are removed.
- **Limits against abuse**: maximum video length (30 minutes), maximum
  audio size (100 MB), no live streams, maximum transcript length for
  Gemini. Quiz creation is rate limited (10 per hour per user).
- **Prompt injection**: the transcript is placed in a marked block and
  Gemini is told to treat it as data only.
- **AI output is untrusted**: the JSON is validated (10 questions,
  4 different options, answer is one of the options) before it is saved.
- Temporary audio files are always deleted after the request.
- Internal error details are only written to the server log, the client
  gets a short message.

### Authorization

- Users only see their own quizzes. Reading, changing or deleting a quiz
  of another user returns `403`.
- Only `title` and `description` can be changed with PATCH, `PUT` is not
  allowed.

### Configuration

- All secrets (`SECRET_KEY`, `GEMINI_API_KEY`, database password) are read
  from `.env`, which is never committed.
- The app does not start without a `SECRET_KEY`.
- `DEBUG` is `False` by default. In production HTTPS redirect, HSTS,
  secure session and CSRF cookies are active.
- CORS only allows the configured frontend origins.

## Tests

The tests mock yt-dlp, Whisper and Gemini, so they run without internet,
FFmpeg or an API key.

```bash
coverage run manage.py test
```

```bash
coverage report
```

Code style:

```bash
flake8
```

## Project structure

```text
core/                 settings, URL routing, WSGI
auth_app/
  api/                views, serializers, URLs, cookie JWT authentication
  utils.py            cookie and token helpers
  tests/
quiz_app/
  api/                views, serializers, URLs, owner permission
  models.py           Quiz and Question
  admin.py            admin panel for quizzes and questions
  utils.py            URL validation, download, Whisper, Gemini, saving
  tests/
Dockerfile            backend image
docker-compose.yml    backend + PostgreSQL
.github/workflows/    CI pipeline
```
