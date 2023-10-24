"""Declare API endpoints for videos with Django RestFramework viewsets."""
import tempfile

from django.conf import settings
from django.core.files.storage import storages
from django.utils import timezone

import django_filters
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from marsha.core import defaults, permissions, serializers
from marsha.core.api.base import (
    APIViewMixin,
    ObjectPkMixin,
    ObjectRelatedMixin,
    ObjectVideoRelatedMixin,
)
from marsha.core.metadata import TimedTextMetadata
from marsha.core.models import TimedTextTrack
from marsha.core.utils.s3_utils import create_presigned_post
from marsha.core.utils.time_utils import to_timestamp


class TimedTextTrackFilter(django_filters.FilterSet):
    """Filter for TimedTextTrack."""

    video = django_filters.UUIDFilter(field_name="video_id")

    class Meta:
        model = TimedTextTrack
        fields = []


class TimedTextTrackViewSet(
    APIViewMixin,
    ObjectPkMixin,
    ObjectRelatedMixin,
    ObjectVideoRelatedMixin,
    viewsets.ModelViewSet,
):
    """Viewset for the API of the TimedTextTrack object."""

    permission_classes = [permissions.NotAllowed]
    queryset = TimedTextTrack.objects.all()
    serializer_class = serializers.TimedTextTrackSerializer
    metadata_class = TimedTextMetadata
    filter_backends = [
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend,
    ]
    ordering_fields = ["created_on", "video__title"]
    ordering = ["created_on"]
    filterset_class = TimedTextTrackFilter

    def get_permissions(self):
        """Instantiate and return the list of permissions that this view requires."""
        if self.action in ["metadata", "transcript_callback"]:
            permission_classes = [AllowAny]
        elif self.action in ["create", "list"]:
            permission_classes = [
                permissions.IsTokenInstructor
                | permissions.IsTokenAdmin
                | permissions.IsParamsVideoAdminOrInstructorThroughPlaylist
                | permissions.IsParamsVideoAdminThroughOrganization
            ]
        elif self.action in [
            "destroy",
            "initiate_upload",
            "retrieve",
            "update",
            "partial_update",
        ]:
            permission_classes = [
                permissions.IsTokenPlaylistRouteObjectRelatedVideo
                & (permissions.IsTokenInstructor | permissions.IsTokenAdmin)
                | permissions.IsRelatedVideoPlaylistAdminOrInstructor
                | permissions.IsRelatedVideoOrganizationAdmin
            ]
        elif self.action is None:
            if self.request.method not in self.allowed_methods:
                raise MethodNotAllowed(self.request.method)
            permission_classes = self.permission_classes
        else:
            # When here it means we forgot to define a permission for a new action
            # We enforce the permission definition in this method to have a clearer view
            raise NotImplementedError(f"Action '{self.action}' is not implemented.")
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Redefine the queryset to use based on the current action."""
        queryset = super().get_queryset()
        return queryset.filter(video__id=self.get_related_video_id())

    @action(methods=["post"], detail=True, url_path="initiate-upload")
    # pylint: disable=unused-argument
    def initiate_upload(self, request, pk=None, video_id=None):
        """Get an upload policy for a timed text track.

        Calling the endpoint resets the upload state to `pending` and returns an upload policy to
        our AWS S3 source bucket.

        Parameters
        ----------
        request : Type[django.http.request.HttpRequest]
            The request on the API endpoint
        pk: string
            The primary key of the timed text track

        Returns
        -------
        Type[rest_framework.response.Response]
            HttpResponse carrying the AWS S3 upload policy as a JSON object.

        """
        timed_text_track = self.get_object()  # check permissions first

        serializer = serializers.TimedTextUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        now = timezone.now()
        stamp = to_timestamp(now)

        key = timed_text_track.get_source_s3_key(stamp=stamp)

        presigned_post = create_presigned_post(
            [["content-length-range", 0, settings.SUBTITLE_SOURCE_MAX_SIZE]],
            {},
            key,
        )

        # Reset the upload state of the timed text track
        TimedTextTrack.objects.filter(pk=pk).update(upload_state=defaults.PENDING)

        return Response(presigned_post)

    @action(methods=["post"], detail=True, url_path="transcript-callback")
    # pylint: disable=unused-argument
    def transcript_callback(self, request, pk=None, video_id=None):
        """Handle callback from Gladia"""
        s3_storage = storages["s3"]

        print(request.data)
        timed_text_track = self.get_object()
        timed_text_track.mode = "st"
        timed_text_track.extension = "tts"
        timed_text_track.language = request.data["payload"]["prediction_raw"][
            "transcription"
        ][0]["language"]
        now = timezone.now()
        stamp = to_timestamp(now)
        timed_text_track.uploaded_on = now
        timed_text_track.save()

        with tempfile.NamedTemporaryFile(mode="w+t") as temp_file:
            content = request.data["payload"]["prediction"]
            temp_file.write(content)
            temp_file.flush()
            s3_storage.save(timed_text_track.get_source_s3_key(), temp_file)

        return Response(status=200)
