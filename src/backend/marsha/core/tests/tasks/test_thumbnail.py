"""Test for thumbnail celery tasks"""
# pylint: disable=protected-access
from io import BytesIO

from django.core.files.base import ContentFile
from django.test import TestCase

from PIL import Image

from marsha.core.defaults import TMP_VIDEOS_STORAGE_BASE_DIRECTORY
from marsha.core.factories import ThumbnailFactory
from marsha.core.storage.storage_class import video_storage
from marsha.core.tasks.thumbnail import resize_thumbnails


class TestThumbnailTask(TestCase):
    """
    Test for thumbnail celery tasks
    """

    def test_resize_thumbnails_task(self):
        """
        Test the the test_resize_thumbnails function. It should create
        different thumbnails for different sizes from the original image.
        """
        thumbnail = ThumbnailFactory()
        image = Image.new("RGBA", size=(1080, 1080), color=(256, 0, 0))
        stamp = "1640995200"
        with BytesIO() as buffer:
            image.save(buffer, "PNG")
            content_file = ContentFile(buffer.getvalue())
            video_storage.save(
                thumbnail.get_videos_storage_prefix(
                    stamp, TMP_VIDEOS_STORAGE_BASE_DIRECTORY
                ),
                content_file,
            )
        sizes = [1080, 720, 480, 240, 144]
        for size in sizes:
            self.assertFalse(
                video_storage.exists(
                    f"{thumbnail.get_videos_storage_prefix(stamp)}/{size}.jpg"
                )
            )

        resize_thumbnails(str(thumbnail.pk), stamp)

        for size in sizes:
            self.assertTrue(
                video_storage.exists(
                    f"{thumbnail.get_videos_storage_prefix(stamp)}/{size}.jpg"
                )
            )
