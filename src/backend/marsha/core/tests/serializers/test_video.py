"""Tests for the VideoBaseSerializer serializer of the Marsha project."""
from datetime import datetime, timezone as baseTimezone

from django.test import TestCase, override_settings

from marsha.core.defaults import AWS_PIPELINE, PEERTUBE_PIPELINE
from marsha.core.factories import VideoFactory
from marsha.core.serializers import VideoBaseSerializer


class VideoBaseSerializerTest(TestCase):
    """Test the VideoBaseSerializer serializer."""

    def test_video_serializer_urls_with_aws_pipeline(self):
        """The VideoBaseSerializer should return the right URLs."""
        date = datetime(2022, 1, 1, tzinfo=baseTimezone.utc)
        video = VideoFactory(
            transcode_pipeline=AWS_PIPELINE,
            live_state=None,
            resolutions=[1080],
            uploaded_on=date,
        )

        serializer = VideoBaseSerializer(video)

        self.assertTrue(
            f"https://abc.cloudfront.net/{video.pk}/mp4/1640995200_1080.mp4"
            in serializer.data["urls"]["mp4"][1080]
        )
        self.assertEqual(
            f"https://abc.cloudfront.net/{video.pk}/thumbnails/1640995200_1080.0000000.jpg",
            serializer.data["urls"]["thumbnails"][1080],
        )
        self.assertEqual(
            f"https://abc.cloudfront.net/{video.pk}/cmaf/1640995200.m3u8",
            serializer.data["urls"]["manifests"]["hls"],
        )
        self.assertEqual(
            f"https://abc.cloudfront.net/{video.pk}/previews/1640995200_100.jpg",
            serializer.data["urls"]["previews"],
        )

    @override_settings(
        MEDIA_URL="https://abc.cloudfront.net/",
    )
    def test_video_serializer_urls_with_peertube_pipeline(self):
        """The VideoBaseSerializer should return the right URLs."""
        date = datetime(2022, 1, 1, tzinfo=baseTimezone.utc)
        video = VideoFactory(
            transcode_pipeline=PEERTUBE_PIPELINE,
            live_state=None,
            resolutions=[1080],
            uploaded_on=date,
        )

        serializer = VideoBaseSerializer(video)

        self.assertEqual(
            f"https://abc.cloudfront.net/scw/{video.pk}/video/1640995200/thumbnail.jpg",
            serializer.data["urls"]["thumbnails"][1080],
        )
        self.assertEqual(
            f"https://abc.cloudfront.net/scw/{video.pk}/video/1640995200/master.m3u8",
            serializer.data["urls"]["manifests"]["hls"],
        )
        self.assertEqual(
            f"https://abc.cloudfront.net/scw/{video.pk}/video/1640995200/thumbnail.jpg",
            serializer.data["urls"]["previews"],
        )
        self.assertTrue(
            f"https://abc.cloudfront.net/scw/{video.pk}/"
            "video/1640995200/1640995200-1080-fragmented.mp4"
            in serializer.data["urls"]["mp4"][1080]
        )

    def test_video_serializer_urls_with_no_pipeline(self):
        """The VideoBaseSerializer should return empty URLs."""
        date = datetime(2022, 1, 1, tzinfo=baseTimezone.utc)
        video = VideoFactory(
            transcode_pipeline=None,
            live_state=None,
            resolutions=[1080],
            uploaded_on=date,
        )

        serializer = VideoBaseSerializer(video)

        self.assertEqual(
            {"mp4": {}, "thumbnails": {}, "manifests": {}},
            serializer.data["urls"],
        )
