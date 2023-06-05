"""
Models for the markdown app of the Marsha project.

In this base model, we activate generic behaviours that apply to all our models and enforce
checks and validation that go further than what Django is doing.
"""

import logging

from django.db import models
from django.utils.translation import gettext_lazy as _

from parler.managers import TranslatableManager
from parler.models import TranslatableModelMixin, TranslatedFields

from marsha.core.models import AbstractImage, BaseModel, Playlist, User
from marsha.core.utils.time_utils import to_timestamp


logger = logging.getLogger(__name__)


class MarkdownDocument(TranslatableModelMixin, BaseModel):
    """Model representing a markdown document."""

    RESOURCE_NAME = "markdown-documents"

    # Common LTI resource fields
    lti_id = models.CharField(
        max_length=255,
        verbose_name=_("lti id"),
        help_text=_("ID for synchronization with an external LTI tool"),
        blank=True,
        null=True,
    )
    playlist = models.ForeignKey(
        to=Playlist,
        related_name="%(class)ss",
        verbose_name=_("playlist"),
        help_text=_("playlist to which this file belongs"),
        # don't allow hard deleting a playlist if it still contains files
        on_delete=models.PROTECT,
    )
    position = models.PositiveIntegerField(
        verbose_name=_("position"),
        help_text=_("position of this file in the playlist"),
        default=0,
    )
    duplicated_from = models.ForeignKey(
        to="self",
        related_name="duplicates",
        verbose_name=_("duplicated from"),
        help_text=_("original file this one was duplicated from"),
        # don't delete a file if the one it was duplicated from is hard deleted
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Common resource attribute
    created_by = models.ForeignKey(
        to=User,
        related_name="created_%(class)s",
        verbose_name=_("author"),
        help_text=_("author of the file"),
        # file is (soft-)deleted if author is (soft-)deleted
        on_delete=models.CASCADE,
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=_("is Markdown document public"),
        help_text=_("Is the Markdown document publicly accessible?"),
    )

    # Specific Markdown document fields
    is_draft = models.BooleanField(
        default=True,
        verbose_name=_("is Markdown document still a draft"),
        help_text=_("Is the Markdown document a draft?"),
    )

    translations = TranslatedFields(
        # Title might not be limited to 255 characters
        title=models.CharField(
            max_length=255,
            verbose_name=_("title"),
            help_text=_("Markdown document's title"),
            blank=True,
        ),
        content=models.TextField(
            verbose_name=_("Markdown document content"),
            help_text=_("The document Markdown formatted content"),
            blank=True,
        ),
        rendered_content=models.TextField(
            verbose_name=_("Markdown document rendered content"),
            help_text=_("The Markdown document formatted content for students"),
            blank=True,
        ),
    )

    rendering_options = models.JSONField(
        default=dict,
        verbose_name=_("Markdown rendering options"),
        help_text=_(
            "Markdown rendering options are use by the frontend's markdown to HTML renderer"
        ),
        blank=True,
    )

    # use the translation manager, this is mandatory
    objects = TranslatableManager()

    class Meta:
        """Options for the ``MarkdownDocument`` model."""

        db_table = "md_document"
        verbose_name = _("Markdown document")
        verbose_name_plural = _("Markdown documents")
        constraints = [
            models.UniqueConstraint(
                fields=["lti_id", "playlist"],
                condition=models.Q(deleted=None),
                name="markdown_document_unique_idx",
            )
        ]

    @staticmethod
    def get_ready_clause():
        """Clause used in lti.utils.get_or_create_resource to filter the documents.

        Returns
        -------
        models.Q
            A condition added to a QuerySet
        """
        return models.Q(is_draft=False)

    def __str__(self):
        """Get the string representation of an instance, needs to be in an i18n context."""
        result = f"{self.title}"
        if self.deleted:
            result = _("{:s} [deleted]").format(result)
        return result

    @property
    def consumer_site(self):
        """Return the consumer site linked to this file via the playlist."""
        return self.playlist.consumer_site


class MarkdownImage(AbstractImage):
    """Model for image included in a Markdown document.

    Lifecycle looks like:
     - The markdown document writer ask to add an image.
     - The backend returns an access policy to allow
       frontend to upload the image.
     - The frontend starts uploading the image.
     - When uploaded to the bucket, a lambda is triggered
       to move the image to the destination bucket.
     - When the image is on the final bucket, AWS (for now)
       will trigger the `update_upload_state` method, which
       in turn will send Channel message to the frontend.
    """

    RESOURCE_NAME = "markdown-images"
    S3_IDENTIFIER = "markdown-image"

    markdown_document = models.ForeignKey(
        to=MarkdownDocument,
        related_name="images",
        verbose_name=_("Markdown document"),
        help_text=_("markdown document using this image"),
        # No need to keep image without Markdown document
        # it's ok since it's soft deleted,
        # but may add cleaning when hard deleted.
        on_delete=models.CASCADE,
    )

    extension = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=10,
        verbose_name=_("file extension"),
        help_text=_('image extension (like "png", "jpg", etc.'),
    )

    class Meta:
        """Options for the ``MarkdownImage`` model."""

        db_table = "md_images"
        verbose_name = _("image")
        ordering = ["-created_on", "id"]

    def get_source_s3_key(self, stamp=None, extension=None):
        """Compute the S3 key in the source bucket.

        It is built from the document ID + ID of the image.

        Parameters
        ----------
        stamp: Type[string]
            Passing a value for this argument will return the source S3 key for the image
            assuming its active stamp is set to this value. This is not for versioning but
            so client can upload the file to S3 and the confirmation lambda can set the
            `uploaded_on` field to this value only after the file upload and processing
            is successful.

        Returns
        -------
        string
            The S3 key for the image file in the source bucket, where uploaded files are
            stored before they are converted and copied to the destination bucket.

        """
        stamp = stamp or to_timestamp(self.uploaded_on)

        # We don't want to deal with None value, so we set it with an empty string
        extension = extension or ""

        # We check if the extension starts with a leading dot or not. If it's not the case we add
        # it at the beginning of the string
        if extension and extension[:1] != ".":
            extension = "." + extension

        return (
            f"{self.markdown_document_id}/markdown-image/"
            f"{self.pk}/{stamp}{extension}"
        )
