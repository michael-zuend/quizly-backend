"""Tests for the YouTube URL validation."""

from django.test import SimpleTestCase

from quiz_app.utils import (
    InvalidVideoUrlError,
    build_video_url,
    extract_video_id,
)

VIDEO_ID = "dQw4w9WgXcQ"


class ExtractVideoIdTests(SimpleTestCase):
    """extract_video_id accepts YouTube links only."""

    def test_valid_url_formats(self):
        """All common YouTube link formats return the id."""
        urls = [
            f"https://www.youtube.com/watch?v={VIDEO_ID}",
            f"https://youtube.com/watch?v={VIDEO_ID}&list=abc&t=10",
            f"https://m.youtube.com/watch?v={VIDEO_ID}",
            f"https://youtu.be/{VIDEO_ID}?si=tracking",
            f"https://www.youtube.com/shorts/{VIDEO_ID}",
            f"https://www.youtube.com/embed/{VIDEO_ID}",
            f"  http://www.youtube.com/live/{VIDEO_ID}  ",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(extract_video_id(url), VIDEO_ID)

    def test_invalid_urls_are_rejected(self):
        """Other hosts, schemes and broken ids raise an error."""
        urls = [
            f"https://evil.com/watch?v={VIDEO_ID}",
            f"https://youtube.com.evil.com/watch?v={VIDEO_ID}",
            f"ftp://www.youtube.com/watch?v={VIDEO_ID}",
            f"file:///etc/passwd?v={VIDEO_ID}",
            "https://www.youtube.com/watch?v=short",
            "https://www.youtube.com/channel/abc",
            "https://www.youtube.com/watch",
            "http://127.0.0.1:8000/admin/",
        ]
        for url in urls:
            with self.subTest(url=url):
                with self.assertRaises(InvalidVideoUrlError):
                    extract_video_id(url)

    def test_build_video_url(self):
        """The stored URL always has the watch?v= format."""
        self.assertEqual(
            build_video_url(VIDEO_ID),
            f"https://www.youtube.com/watch?v={VIDEO_ID}",
        )
