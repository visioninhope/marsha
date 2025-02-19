"""Tests for the classroomdocument update API."""
import json

from django.test import TestCase, override_settings

from marsha.bbb.factories import ClassroomDocumentFactory, ClassroomFactory
from marsha.bbb.models import ClassroomDocument
from marsha.core.factories import (
    OrganizationAccessFactory,
    PlaylistAccessFactory,
    PlaylistFactory,
)
from marsha.core.models import ADMINISTRATOR, INSTRUCTOR, STUDENT
from marsha.core.simple_jwt.factories import (
    InstructorOrAdminLtiTokenFactory,
    StudentLtiTokenFactory,
    UserAccessTokenFactory,
)
from marsha.core.tests.testing_utils import reload_urlconf


# We don't enforce arguments documentation in tests
# pylint: disable=unused-argument


@override_settings(BBB_ENABLED=True)
class ClassroomDocumentUpdateAPITest(TestCase):
    """Test for the ClassroomDocument update API."""

    maxDiff = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Force URLs reload to use BBB_ENABLED
        reload_urlconf()

    def test_api_classroom_document_update_student(self):
        """A student user should not be able to update a classroom_document."""
        classroom_document = ClassroomDocumentFactory()
        jwt_token = StudentLtiTokenFactory(
            playlist=classroom_document.classroom.playlist
        )
        data = {"filename": "updated_name.pdf", "size": 100}

        response = self.client.patch(
            f"/api/classrooms/{classroom_document.classroom.id}"
            f"/classroomdocuments/{classroom_document.id}/",
            json.dumps(data),
            HTTP_AUTHORIZATION=f"Bearer {jwt_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_api_classroom_document_update_instructor(self):
        """An instructor should be able to update a classroom_document."""
        classroom_document = ClassroomDocumentFactory()
        jwt_token = InstructorOrAdminLtiTokenFactory(
            playlist=classroom_document.classroom.playlist
        )
        data = {"filename": "updated_name.pdf", "size": 100}

        response = self.client.patch(
            f"/api/classrooms/{classroom_document.classroom.id}"
            f"/classroomdocuments/{classroom_document.id!s}/",
            data,
            HTTP_AUTHORIZATION=f"Bearer {jwt_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "classroom_id": str(classroom_document.classroom.id),
                "filename": "updated_name.pdf",
                "id": str(classroom_document.id),
                "is_default": False,
                "upload_state": "pending",
                "uploaded_on": None,
                "url": None,
            },
        )

    def test_api_classroom_document_update_instructor_default(self):
        """A document set to be the default one should set others to false"""
        classroom = ClassroomFactory()
        first_document = ClassroomDocumentFactory(
            classroom=classroom,
            is_default=True,
        )
        second_document = ClassroomDocumentFactory(classroom=classroom)
        jwt_token = InstructorOrAdminLtiTokenFactory(playlist=classroom.playlist)
        data = {"is_default": True}

        response = self.client.patch(
            f"/api/classrooms/{classroom.id}/classroomdocuments/{second_document.id!s}/",
            data,
            HTTP_AUTHORIZATION=f"Bearer {jwt_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "classroom_id": str(second_document.classroom.id),
                "filename": second_document.filename,
                "id": str(second_document.id),
                "is_default": True,
                "upload_state": "pending",
                "uploaded_on": None,
                "url": None,
            },
        )
        self.assertEqual(ClassroomDocument.objects.count(), 2)
        self.assertEqual(ClassroomDocument.objects.filter(is_default=True).count(), 1)
        first_document.refresh_from_db()
        self.assertFalse(first_document.is_default)

    def test_api_classroom_document_update_user_access_token(self):
        """A user with UserAccessToken should not be able to update a classroom_document."""
        organization_access = OrganizationAccessFactory()
        playlist = PlaylistFactory(organization=organization_access.organization)
        classroom_document = ClassroomDocumentFactory(classroom__playlist=playlist)
        jwt_token = UserAccessTokenFactory(user=organization_access.user)
        data = {"filename": "updated_name.pdf"}

        response = self.client.patch(
            f"/api/classrooms/{classroom_document.classroom.id}"
            f"/classroomdocuments/{classroom_document.id}/",
            json.dumps(data),
            HTTP_AUTHORIZATION=f"Bearer {jwt_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_api_classroom_document_update_user_access_token_organization_admin(self):
        """An organization administrator should be able to update a classroom_document."""
        organization_access = OrganizationAccessFactory(role=ADMINISTRATOR)
        playlist = PlaylistFactory(organization=organization_access.organization)
        classroom_document = ClassroomDocumentFactory(classroom__playlist=playlist)
        jwt_token = UserAccessTokenFactory(user=organization_access.user)
        data = {"filename": "updated_name.pdf", "size": 100}

        response = self.client.patch(
            f"/api/classrooms/{classroom_document.classroom.id}"
            f"/classroomdocuments/{classroom_document.id!s}/",
            data,
            HTTP_AUTHORIZATION=f"Bearer {jwt_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "classroom_id": str(classroom_document.classroom.id),
                "filename": "updated_name.pdf",
                "id": str(classroom_document.id),
                "is_default": False,
                "upload_state": "pending",
                "uploaded_on": None,
                "url": None,
            },
        )

    def test_api_classroom_document_update_user_access_token_playlist_admin(self):
        """A playlist administrator should be able to update a classroom_document."""
        playlist_access = PlaylistAccessFactory(role=ADMINISTRATOR)
        classroom_document = ClassroomDocumentFactory(
            classroom__playlist=playlist_access.playlist
        )
        jwt_token = UserAccessTokenFactory(user=playlist_access.user)
        data = {"filename": "updated_name.pdf", "size": 100}

        response = self.client.patch(
            f"/api/classrooms/{classroom_document.classroom.id}"
            f"/classroomdocuments/{classroom_document.id!s}/",
            data,
            HTTP_AUTHORIZATION=f"Bearer {jwt_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "classroom_id": str(classroom_document.classroom.id),
                "filename": "updated_name.pdf",
                "id": str(classroom_document.id),
                "is_default": False,
                "upload_state": "pending",
                "uploaded_on": None,
                "url": None,
            },
        )

    def test_api_classroom_document_update_user_access_token_playlist_instructor(self):
        """A playlist instructor should be able to update a classroom_document."""
        playlist_access = PlaylistAccessFactory(role=INSTRUCTOR)
        classroom_document = ClassroomDocumentFactory(
            classroom__playlist=playlist_access.playlist
        )
        jwt_token = UserAccessTokenFactory(user=playlist_access.user)
        data = {"filename": "updated_name.pdf", "size": 100}

        response = self.client.patch(
            f"/api/classrooms/{classroom_document.classroom.id}"
            f"/classroomdocuments/{classroom_document.id!s}/",
            data,
            HTTP_AUTHORIZATION=f"Bearer {jwt_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "classroom_id": str(classroom_document.classroom.id),
                "filename": "updated_name.pdf",
                "id": str(classroom_document.id),
                "is_default": False,
                "upload_state": "pending",
                "uploaded_on": None,
                "url": None,
            },
        )

    def test_api_classroom_document_update_user_access_token_playlist_student(self):
        """A playlist student should not be able to update a classroom_document."""
        playlist_access = PlaylistAccessFactory(role=STUDENT)
        classroom_document = ClassroomDocumentFactory(
            classroom__playlist=playlist_access.playlist
        )
        jwt_token = UserAccessTokenFactory(user=playlist_access.user)
        data = {"filename": "updated_name.pdf", "size": 100}

        response = self.client.patch(
            f"/api/classrooms/{classroom_document.classroom.id}"
            f"/classroomdocuments/{classroom_document.id!s}/",
            data,
            HTTP_AUTHORIZATION=f"Bearer {jwt_token}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
