"""Tests for the audio download and the Whisper transcription."""

import shutil
import sys
import tempfile
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase, override_settings
from yt_dlp.utils import DownloadError

from quiz_app import utils
from quiz_app.utils import QuizGenerationError, VideoDownloadError

from .helpers import VIDEO_URL


class DownloadTests(SimpleTestCase):
    """download_audio and the temporary folder."""

    def setUp(self):
        """Use a fresh temporary base folder for every test."""
        self.base_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.base_dir, ignore_errors=True)
        override = override_settings(AUDIO_TEMP_DIR=self.base_dir)
        override.enable()
        self.addCleanup(override.disable)
        self.work_dir = utils.create_work_dir()

    def test_work_dir_is_created_and_removed(self):
        """The folder lies inside AUDIO_TEMP_DIR and can be removed."""
        self.assertEqual(self.work_dir.parent, self.base_dir)
        utils.remove_work_dir(self.work_dir)
        self.assertFalse(self.work_dir.exists())

    def test_download_options_are_safe(self):
        """No playlists, a size limit and FFmpeg conversion to mp3."""
        options = utils.get_download_options(self.work_dir)
        self.assertTrue(options["noplaylist"])
        self.assertEqual(options["max_filesize"], 104857600)
        self.assertEqual(
            options["postprocessors"][0]["preferredcodec"], "mp3"
        )

    @mock.patch("quiz_app.utils.YoutubeDL")
    def test_download_returns_mp3_path(self, youtube_dl):
        """A successful download returns the path of audio.mp3."""
        (self.work_dir / "audio.mp3").write_bytes(b"audio")
        audio_file = utils.download_audio(VIDEO_URL, self.work_dir)
        self.assertEqual(audio_file.name, "audio.mp3")
        downloader = youtube_dl.return_value.__enter__.return_value
        downloader.download.assert_called_once_with([VIDEO_URL])

    @mock.patch("quiz_app.utils.YoutubeDL")
    def test_download_error_is_converted(self, youtube_dl):
        """yt-dlp errors become VideoDownloadError."""
        downloader = youtube_dl.return_value.__enter__.return_value
        downloader.download.side_effect = DownloadError("private")
        with self.assertRaises(VideoDownloadError):
            utils.download_audio(VIDEO_URL, self.work_dir)

    @mock.patch("quiz_app.utils.YoutubeDL")
    def test_skipped_video_raises_error(self, youtube_dl):
        """A video skipped by the match filter leaves no file."""
        with self.assertRaises(VideoDownloadError):
            utils.download_audio(VIDEO_URL, self.work_dir)


class TranscriptionTests(SimpleTestCase):
    """transcribe_audio and load_whisper_model."""

    def setUp(self):
        """Empty the model cache before and after every test."""
        utils.load_whisper_model.cache_clear()
        self.addCleanup(utils.load_whisper_model.cache_clear)

    def test_model_is_loaded_once(self):
        """The Whisper model is cached per process."""
        fake_whisper = mock.MagicMock()
        with mock.patch.dict(sys.modules, {"whisper": fake_whisper}):
            utils.load_whisper_model()
            utils.load_whisper_model()
        fake_whisper.load_model.assert_called_once_with("base")

    @mock.patch("quiz_app.utils.load_whisper_model")
    def test_transcribe_returns_text(self, load_model):
        """The transcript text is returned without spaces around it."""
        load_model.return_value.transcribe.return_value = {"text": " Hi "}
        self.assertEqual(utils.transcribe_audio(Path("a.mp3")), "Hi")

    @mock.patch("quiz_app.utils.load_whisper_model")
    def test_empty_transcript_raises_error(self, load_model):
        """A video without speech cannot become a quiz."""
        load_model.return_value.transcribe.return_value = {"text": "  "}
        with self.assertRaises(QuizGenerationError):
            utils.transcribe_audio(Path("a.mp3"))

    @mock.patch("quiz_app.utils.load_whisper_model")
    def test_whisper_error_is_converted(self, load_model):
        """FFmpeg or model errors become QuizGenerationError."""
        load_model.return_value.transcribe.side_effect = RuntimeError("ff")
        with self.assertRaises(QuizGenerationError):
            utils.transcribe_audio(Path("a.mp3"))
