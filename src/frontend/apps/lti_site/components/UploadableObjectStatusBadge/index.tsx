import { normalizeColor } from 'grommet/utils';
import { colorsTokens, theme } from 'lib-common';
import {
  UploadManagerStatus,
  UploadableObject,
  uploadState,
  useUploadManager,
} from 'lib-components';
import React from 'react';
import { FormattedMessage, defineMessages } from 'react-intl';
import styled from 'styled-components';

const messages = defineMessages({
  [uploadState.DELETED]: {
    defaultMessage: 'Deleted',
    description: 'Badge text for an uploadable object that was deleted.',
    id: 'components.UploadableObjectStatusBadge.deleted',
  },
  [uploadState.ERROR]: {
    defaultMessage: 'Error',
    description:
      'Badge text for an uploadable object that encountered an error.',
    id: 'components.UploadableObjectStatusBadge.error',
  },
  [uploadState.PENDING]: {
    defaultMessage: 'Pending',
    description:
      'Badge text for an uploadable object that has no file at all and is still pending.',
    id: 'components.UploadableObjectStatusBadge.pending',
  },
  [uploadState.PROCESSING]: {
    defaultMessage: 'Processing',
    description:
      'Badge text for an uploadable object that is currently processing',
    id: 'components.UploadableObjectStatusBadge.processing',
  },
  [uploadState.READY]: {
    defaultMessage: 'Ready',
    description: 'Badge text for an uploadable object that is ready.',
    id: 'components.UploadableObjectStatusBadge.ready',
  },
  uploading: {
    defaultMessage: 'Uploading',
    description:
      'Badge text for an uploadable object that is currently uploading.',
    id: 'components.UploadableObjectStatusBadge.uploading',
  },
});

interface BadgeProps {
  background: string;
}

const Badge = styled.div`
  display: inline-block;
  color: white;
  padding: 0.375rem 0.75rem;
  border-radius: 4px;

  background-color: ${({ background }: BadgeProps) =>
    normalizeColor(background, theme)};
`;

interface UploadableObjectStatusBadgeProps {
  object: UploadableObject;
}

export const UploadableObjectStatusBadge = ({
  object,
}: UploadableObjectStatusBadgeProps) => {
  const { uploadManagerState } = useUploadManager();

  switch (object.upload_state) {
    case uploadState.READY:
      return (
        <Badge role="status" background={colorsTokens['success-600']}>
          <FormattedMessage {...messages[uploadState.READY]} />
        </Badge>
      );

    case uploadState.DELETED:
    case uploadState.PROCESSING:
      return (
        <Badge role="status" background={colorsTokens['info-300']}>
          <FormattedMessage {...messages[object.upload_state]} />
        </Badge>
      );

    case uploadState.ERROR:
      return (
        <Badge role="status" background={colorsTokens['danger-400']}>
          <FormattedMessage {...messages[uploadState.ERROR]} />
        </Badge>
      );

    case uploadState.PENDING:
      switch (uploadManagerState[object.id]?.status) {
        case UploadManagerStatus.INIT:
        case UploadManagerStatus.UPLOADING:
          return (
            <Badge role="status" background={colorsTokens['info-300']}>
              <FormattedMessage {...messages.uploading} />
            </Badge>
          );

        case UploadManagerStatus.ERR_POLICY:
        case UploadManagerStatus.ERR_UPLOAD:
          return (
            <Badge role="status" background={colorsTokens['danger-400']}>
              <FormattedMessage {...messages[uploadState.ERROR]} />
            </Badge>
          );

        case UploadManagerStatus.ERR_SIZE:
          return (
            <Badge role="status" background={colorsTokens['danger-400']}>
              <FormattedMessage {...messages[uploadState.ERROR]} />
            </Badge>
          );

        case UploadManagerStatus.SUCCESS:
          return (
            <Badge role="status" background={colorsTokens['info-300']}>
              <FormattedMessage {...messages[uploadState.PROCESSING]} />
            </Badge>
          );

        default:
          return (
            <Badge role="status" background={colorsTokens['greyscale-700']}>
              <FormattedMessage {...messages[uploadState.PENDING]} />
            </Badge>
          );
      }

    default:
      throw new Error('Unexpected object status in object status badge.');
  }
};
