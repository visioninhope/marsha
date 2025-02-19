"""Test caching LTI views in the ``core`` app of the Marsha project."""
from html import unescape
import json
import random
import re
import time
from unittest import mock
import uuid

from django.test import TestCase

from waffle.testutils import override_switch

from marsha.core.defaults import AWS_PIPELINE, SENTRY, STATE_CHOICES
from marsha.core.factories import ConsumerSiteFactory, LiveSessionFactory, VideoFactory
from marsha.core.lti import LTI


# We don't enforce arguments documentation in tests
# pylint: disable=unused-argument


class CacheLTIViewTestCase(TestCase):
    """Test caching in LTI views."""

    def _fetch_lti_request(self, url, data=None):
        """Not a test but utility method to make an LTI request and test cache behavior."""
        started_at = time.time()
        response = self.client.post(url, data) if data else self.client.get(url)
        elapsed = time.time() - started_at
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        match = re.search(
            '<div id="marsha-frontend-data" data-context="(.*)">', content
        )
        context = json.loads(unescape(match.group(1)))
        return elapsed, context.get("resource")

    @mock.patch.object(LTI, "verify")
    @mock.patch.object(LTI, "get_consumer_site")
    @override_switch(SENTRY, active=True)
    def test_views_lti_cache_student(self, mock_get_consumer_site, mock_verify):
        """Validate that responses are cached for students."""
        video1, video2 = VideoFactory.create_batch(
            2,
            upload_state=random.choice([s[0] for s in STATE_CHOICES]),
            playlist__is_portable_to_playlist=True,
            playlist__is_portable_to_consumer_site=True,
            uploaded_on="2019-09-24 07:24:40+00",
            resolutions=[144, 240],
            transcode_pipeline=AWS_PIPELINE,
        )

        mock_get_consumer_site.return_value = video1.playlist.consumer_site

        url = f"/lti/videos/{video1.pk}"
        data = {
            "resource_link_id": video1.lti_id,
            "context_id": video1.playlist.lti_id,
            "roles": "student",
            "user_id": "111",
            "lis_person_sourcedid": "jane_doe",
        }

        with self.assertNumQueries(5):
            elapsed, resource_origin = self._fetch_lti_request(url, data)
        self.assertEqual(resource_origin["id"], str(video1.id))
        self.assertLess(elapsed, 0.1)

        # Calling the same resource a second time with the same LTI parameters
        # should hit the cache and be ultra fast
        with self.assertNumQueries(0):
            elapsed, resource = self._fetch_lti_request(url, data)
        self.assertEqual(resource, resource_origin)
        self.assertLess(elapsed, 0.01)

        # The cache should not be hit on first call if we change the playlist id
        data["context_id"] = "other_playlist"
        with self.assertNumQueries(4):
            elapsed, resource = self._fetch_lti_request(url, data)
        self.assertEqual(resource, resource_origin)
        self.assertLess(elapsed, 0.1)

        with self.assertNumQueries(0):
            elapsed, resource = self._fetch_lti_request(url, data)
        self.assertEqual(resource, resource_origin)
        self.assertLess(elapsed, 0.01)

        # The cache should not be hit on first call if we change the domain
        mock_get_consumer_site.return_value = ConsumerSiteFactory()
        with self.assertNumQueries(4):
            elapsed, resource = self._fetch_lti_request(url, data)
        self.assertEqual(resource, resource_origin)
        self.assertLess(elapsed, 0.1)

        with self.assertNumQueries(0):
            elapsed, resource = self._fetch_lti_request(
                url, {**data, "context_id": "other_playlist"}
            )
        self.assertEqual(resource, resource_origin)
        self.assertLess(elapsed, 0.01)

        # The cache should not be hit on first call if we change the resource id
        url = f"/lti/videos/{video2.pk}"
        with self.assertNumQueries(4):
            elapsed, resource_video2 = self._fetch_lti_request(url, data)
        self.assertEqual(resource_video2["id"], str(video2.id))
        self.assertLess(elapsed, 0.2)

        with self.assertNumQueries(0):
            elapsed, resource = self._fetch_lti_request(url, data)
        self.assertEqual(resource, resource_video2)
        self.assertLess(elapsed, 0.01)

        # The cache should STILL be hit if the user changes
        data["user_id"] = "222"
        with self.assertNumQueries(0):
            elapsed, resource = self._fetch_lti_request(url, data)
        self.assertEqual(resource, resource_video2)
        self.assertLess(elapsed, 0.01)

    @mock.patch.object(LTI, "verify")
    @mock.patch.object(LTI, "get_consumer_site")
    @override_switch(SENTRY, active=True)
    def test_views_lti_cache_instructor(self, mock_get_consumer_site, mock_verify):
        """Validate that responses are not cached for instructors."""
        video = VideoFactory(
            upload_state=random.choice([s[0] for s in STATE_CHOICES]),
            uploaded_on="2019-09-24 07:24:40+00",
            resolutions=[144, 240],
            transcode_pipeline=AWS_PIPELINE,
        )

        mock_get_consumer_site.return_value = video.playlist.consumer_site

        url = f"/lti/videos/{video.pk}"
        data = {
            "resource_link_id": video.lti_id,
            "context_id": video.playlist.lti_id,
            "roles": "instructor",
            "user_id": "111",
            "lis_person_sourcedid": "jane_doe",
        }

        with self.assertNumQueries(5):
            elapsed, resource_origin = self._fetch_lti_request(url, data)
        self.assertEqual(resource_origin["id"], str(video.id))
        self.assertLess(elapsed, 0.1)

        # Calling the same resource a second time with the same LTI parameters
        # should not hit the cache
        with self.assertNumQueries(4):
            elapsed, resource = self._fetch_lti_request(url, data)
        self.assertEqual(resource, resource_origin)
        self.assertLess(elapsed, 0.1)

    @override_switch(SENTRY, active=True)
    def test_views_public_resource(self):
        """Validate that response for public resources are cached."""
        video = VideoFactory(
            upload_state=random.choice([s[0] for s in STATE_CHOICES]),
            uploaded_on="2019-09-24 07:24:40+00",
            transcode_pipeline=AWS_PIPELINE,
            resolutions=[144, 240],
            is_public=True,
        )
        url = f"/videos/{video.pk}"

        with self.assertNumQueries(5):
            elapsed, resource_origin = self._fetch_lti_request(url)
        self.assertEqual(resource_origin["id"], str(video.id))
        self.assertLess(elapsed, 0.1)

        with self.assertNumQueries(0):
            elapsed, resource_origin = self._fetch_lti_request(url)
        self.assertEqual(resource_origin["id"], str(video.id))
        self.assertLess(elapsed, 0.1)

    @override_switch(SENTRY, active=True)
    def test_views_direct_access_lti_resource(self):
        """Validate that response for public resources on direct access are cached."""
        video = VideoFactory()
        livesession = LiveSessionFactory(
            consumer_site=video.playlist.consumer_site,
            email="sarah@openfun.fr",
            is_registered=True,
            lti_id=str(video.playlist.lti_id),
            lti_user_id="5555",
            video=video,
        )
        url = (
            f"/videos/{video.id}?lrpk={livesession.pk}&key="
            f"{livesession.get_generate_salted_hmac()}"
        )

        with self.assertNumQueries(8):
            elapsed, resource_origin = self._fetch_lti_request(url)

        self.assertEqual(resource_origin["id"], str(video.id))
        self.assertLess(elapsed, 0.7)

        with self.assertNumQueries(4):
            elapsed, resource_origin = self._fetch_lti_request(url)
        self.assertEqual(resource_origin["id"], str(video.id))
        self.assertLess(elapsed, 0.1)

    @override_switch(SENTRY, active=True)
    def test_views_direct_access_public_resource(self):
        """Validate that response for lti resources on direct access are cached."""
        video = VideoFactory()
        public_registration = LiveSessionFactory(
            anonymous_id=uuid.uuid4(),
            email="sarah@test-fun-mooc.fr",
            is_registered=True,
            should_send_reminders=True,
            video=video,
        )

        url = (
            f"/videos/{video.id}?lrpk={public_registration.pk}&key="
            f"{public_registration.get_generate_salted_hmac()}"
        )

        with self.assertNumQueries(7):
            elapsed, resource_origin = self._fetch_lti_request(url)

        self.assertEqual(resource_origin["id"], str(video.id))
        self.assertLess(elapsed, 0.2)

        with self.assertNumQueries(3):
            elapsed, resource_origin = self._fetch_lti_request(url)
        self.assertEqual(resource_origin["id"], str(video.id))
        self.assertLess(elapsed, 0.2)
