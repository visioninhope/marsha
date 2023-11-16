"""Tests for the Video start live API of the Marsha project."""
import json
from unittest import mock

from django.test import TestCase, override_settings

from marsha.core import factories, models
from marsha.core.defaults import PEERTUBE_PIPELINE, PROCESSING
from marsha.core.simple_jwt.factories import UserAccessTokenFactory


class VideoUploadEndedAPITest(TestCase):
    """Test the "upload-ended" API of the video object."""

    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.some_organization = factories.OrganizationFactory()
        cls.some_video = factories.VideoFactory(
            playlist__organization=cls.some_organization,
            transcode_pipeline=PEERTUBE_PIPELINE,
        )

    def assert_user_cannot_end_an_upload(self, user, video):
        """Assert the user cannot end an upload."""

        jwt_token = UserAccessTokenFactory(user=user)
        response = self.client.post(
            f"/api/videos/{video.pk}/upload-ended/",
            HTTP_AUTHORIZATION=f"Bearer {jwt_token}",
        )

        self.assertEqual(response.status_code, 403)

    @override_settings(LIVE_CHAT_ENABLED=True)
    def assert_user_can_end_an_upload(self, user, video):
        """Assert the user can end an upload."""

        jwt_token = UserAccessTokenFactory(user=user)
        with mock.patch(
            "marsha.websocket.utils.channel_layers_utils.dispatch_video"
        ) as mock_dispatch_video, mock.patch(
            "marsha.core.api.video.transcode_video"
        ) as mock_transcode_video:
            response = self.client.post(
                f"/api/videos/{video.id}/upload-ended/",
                {
                    "file_key": f"tmp/{video.pk}/video/4564565456",
                },
                HTTP_AUTHORIZATION=f"Bearer {jwt_token}",
            )
            mock_transcode_video.assert_called_once_with(
                file_path=f"tmp/{video.pk}/video/4564565456",
                destination=f"scw/{video.pk}/video/4564565456",
                base_name="4564565456",
                domain="http://testserver",
            )
            mock_dispatch_video.assert_called_once_with(video, to_admin=True)

        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)

        self.assertEqual(content["upload_state"], PROCESSING)

    def test_end_upload_by_anonymous_user(self):
        """Anonymous users cannot end an upload."""
        response = self.client.post(f"/api/videos/{self.some_video.pk}/upload-ended/")

        self.assertEqual(response.status_code, 401)

    def test_end_upload_by_random_user(self):
        """Authenticated user without access cannot end an upload."""
        user = factories.UserFactory()

        self.assert_user_cannot_end_an_upload(user, self.some_video)

    def test_end_upload_by_organization_student(self):
        """Organization students cannot end an upload."""
        organization_access = factories.OrganizationAccessFactory(
            organization=self.some_organization,
            role=models.STUDENT,
        )

        self.assert_user_cannot_end_an_upload(organization_access.user, self.some_video)

    def test_end_upload_by_organization_instructor(self):
        """Organization instructors cannot end an upload."""
        organization_access = factories.OrganizationAccessFactory(
            organization=self.some_organization,
            role=models.INSTRUCTOR,
        )

        self.assert_user_cannot_end_an_upload(organization_access.user, self.some_video)

    def test_end_upload_by_organization_administrator(self):
        """Organization administrators can end an upload."""
        organization_access = factories.OrganizationAccessFactory(
            organization=self.some_organization,
            role=models.ADMINISTRATOR,
        )

        self.assert_user_can_end_an_upload(organization_access.user, self.some_video)

    def test_end_upload_by_consumer_site_any_role(self):
        """Consumer site roles cannot end an upload."""
        consumer_site_access = factories.ConsumerSiteAccessFactory(
            consumer_site=self.some_video.playlist.consumer_site,
        )

        self.assert_user_cannot_end_an_upload(
            consumer_site_access.user, self.some_video
        )

    def test_end_upload_by_playlist_student(self):
        """Playlist student cannot end an upload."""
        playlist_access = factories.PlaylistAccessFactory(
            playlist=self.some_video.playlist,
            role=models.STUDENT,
        )

        self.assert_user_cannot_end_an_upload(playlist_access.user, self.some_video)

    def test_end_upload_by_playlist_instructor(self):
        """Playlist instructor cannot end an upload."""
        playlist_access = factories.PlaylistAccessFactory(
            playlist=self.some_video.playlist,
            role=models.INSTRUCTOR,
        )

        self.assert_user_can_end_an_upload(playlist_access.user, self.some_video)

    def test_end_upload_by_playlist_admin(self):
        """Playlist administrator can end an upload."""
        playlist_access = factories.PlaylistAccessFactory(
            playlist=self.some_video.playlist,
            role=models.ADMINISTRATOR,
        )

        self.assert_user_can_end_an_upload(playlist_access.user, self.some_video)

    def test_end_upload_with_wrong_body(self):
        """Playlist administrator can end an upload."""
        playlist_access = factories.PlaylistAccessFactory(
            playlist=self.some_video.playlist,
            role=models.ADMINISTRATOR,
        )

        jwt_token = UserAccessTokenFactory(user=playlist_access.user)
        response = self.client.post(
            f"/api/videos/{self.some_video.id}/upload-ended/",
            {
                "wrong_key": f"source/{self.some_video.pk}/video/4564565456",
            },
            HTTP_AUTHORIZATION=f"Bearer {jwt_token}",
        )
        self.assertEqual(response.status_code, 400)

    def test_end_upload_with_forged_path(self):
        """Playlist administrator can end an upload."""
        playlist_access = factories.PlaylistAccessFactory(
            playlist=self.some_video.playlist,
            role=models.ADMINISTRATOR,
        )

        jwt_token = UserAccessTokenFactory(user=playlist_access.user)
        response = self.client.post(
            f"/api/videos/{self.some_video.id}/upload-ended/",
            {
                "file_key": f"tmp/{self.some_video.pk}/crafted/4564565456",
            },
            HTTP_AUTHORIZATION=f"Bearer {jwt_token}",
        )
        self.assertEqual(response.status_code, 400)

    def test_end_upload_with_forged_stamp(self):
        """Playlist administrator can end an upload."""
        playlist_access = factories.PlaylistAccessFactory(
            playlist=self.some_video.playlist,
            role=models.ADMINISTRATOR,
        )

        jwt_token = UserAccessTokenFactory(user=playlist_access.user)
        response = self.client.post(
            f"/api/videos/{self.some_video.id}/upload-ended/",
            {
                "wrong_key": f"tmp/{self.some_video.pk}/video/crafted_stamp",
            },
            HTTP_AUTHORIZATION=f"Bearer {jwt_token}",
        )
        self.assertEqual(response.status_code, 400)
