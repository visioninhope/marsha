"""Custom permission classes for the Marsha project."""
from django.core.exceptions import FieldError, ObjectDoesNotExist

from rest_framework import permissions

from marsha.core import models


class BaseTokenRolePermission(permissions.BasePermission):
    """Base permission class for JWT Tokens based on token roles.

    These permissions grant access to users authenticated with a JWT token built from a
    playlist ie related to a TokenPlaylist.
    """

    role = None

    def check_role(self, token):
        """Check if the required role is in the token and if can_update is granted."""
        return models.LTI_ROLES[self.__class__.role] & set(
            token.payload.get("roles", [])
        ) and token.payload.get("permissions", {}).get("can_update", False)

    def has_permission(self, request, view):
        """
        Add a check to allow users identified via a JWT token with a given token-granted role.

        Parameters
        ----------
        request : Type[django.http.request.HttpRequest]
            The request that holds the authenticated user
        view : Type[restframework.viewsets or restframework.views]
            The API view for which permissions are being checked

        Returns
        -------
        boolean
            True if the request is authorized, False otherwise

        """
        return request.resource and self.check_role(request.resource.token)


class IsTokenInstructor(BaseTokenRolePermission):
    """Class dedicated to instructor users."""

    role = models.INSTRUCTOR


class IsTokenAdmin(BaseTokenRolePermission):
    """Class dedicated to administrator users."""

    role = models.ADMINISTRATOR


class IsTokenStudent(BaseTokenRolePermission):
    """Class dedicated to student users."""

    def check_role(self, token):
        """Check if the student role is in the token."""
        return bool(
            models.LTI_ROLES[models.STUDENT] & set(token.payload.get("roles", []))
        )


class IsTokenPlaylistRouteObject(permissions.BasePermission):
    """
    Base permission class for JWT Tokens related to a resource object.

    These permissions grant access to users authenticated with a JWT token built from a
    resource ie related to a TokenResource.
    """

    def has_permission(self, request, view):
        """
        Add a check to allow the request if the JWT resource matches the object in the url path.

        Parameters
        ----------
        request : Type[django.http.request.HttpRequest]
            The request that holds the authenticated user
        view : Type[restframework.viewsets or restframework.views]
            The API view for which permissions are being checked

        Returns
        -------
        boolean
            True if the request is authorized, False otherwise
        """
        return request.resource and view.get_object_pk() == request.resource.id


class IsTokenPlaylistRouteObjectRelatedPlaylist(permissions.BasePermission):
    """
    Base permission class for JWT Tokens related to a playlist linked to a video.

    These permissions grant access to users authenticated with a JWT token built from a
    resource ie related to a TokenResource.
    """

    def has_permission(self, request, view):
        """
        Add a check to allow the request if the JWT resource matches the playlist in the url path.

        Parameters
        ----------
        request : Type[django.http.request.HttpRequest]
            The request that holds the authenticated user
        view : Type[restframework.viewsets or restframework.views]
            The API view for which permissions are being checked

        Returns
        -------
        boolean
            True if the request is authorized, False otherwise
        """
        return (
            request.resource
            and request.resource.id == view.get_object_pk()
            and models.Playlist.objects.filter(id=request.resource.id).exists()
        )


class IsTokenPlaylistRouteObjectRelatedVideo(permissions.BasePermission):
    """
    Base permission class for JWT Tokens related to a resource object linked to a video.

    These permissions grant access to users authenticated with a JWT token built from a
    resource ie related to a TokenResource.
    """

    def has_permission(self, request, view):
        """
        Allow the request if the JWT resource matches the video related to the object in the url.

        Parameters
        ----------
        request : Type[django.http.request.HttpRequest]
            The request that holds the authenticated user
        view : Type[restframework.viewsets or restframework.views]
            The API view for which permissions are being checked

        Returns
        -------
        boolean
            True if the request is authorized, False otherwise
        """
        try:
            return (
                request.resource
                and str(view.get_related_object().video.playlist.id)
                == request.resource.id
            )
        except ObjectDoesNotExist:
            return False


class IsPlaylistTokenMatchingRouteObject(permissions.BasePermission):
    """
    Allow a request to proceed. Permission class.

    Only if the user has a playlist token payload.
    """

    def has_permission(self, request, view):
        """
        Allow the request.

        Only if the playlist exists.
        """
        if request.resource:
            playlist_id = request.resource.id
            playlist_exists = models.Playlist.objects.filter(id=playlist_id).exists()
            try:
                return (
                    playlist_exists
                    and view.get_queryset()
                    .filter(id=view.get_object_pk(), playlist__id=playlist_id)
                    .exists()
                )
            except FieldError:
                return playlist_exists and (
                    view.get_queryset()
                    .filter(id=view.get_object_pk(), video__playlist__id=playlist_id)
                    .exists()
                )
        return False


class IsPlaylistToken(permissions.BasePermission):
    """
    Allow a request to proceed. Permission class.

    Only if the user has a playlist token payload.
    """

    def has_permission(self, request, view):
        """
        Allow the request.

        Only if the playlist exists.
        """
        if request.resource:
            playlist_id = request.resource.id
            return models.Playlist.objects.filter(id=playlist_id).exists()
        return False


class PortToPlaylistExists(permissions.BasePermission):
    """
    Allow a request to proceed. Permission class.

    Only if the playlist is ported to exist.
    """

    def has_permission(self, request, view):
        """
        Allow the request.

        Only if the playlist exists.
        """
        if request.resource:
            playlist_id = request.resource.port_to_playlist_id
            return models.Playlist.objects.filter(id=playlist_id).exists()
        return False
