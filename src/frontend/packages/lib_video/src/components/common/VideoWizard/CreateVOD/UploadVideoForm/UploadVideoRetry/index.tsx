import { colorsTokens } from 'lib-common';
import { RetryUploadButton, Text, formatSizeErrorScale } from 'lib-components';
import React from 'react';
import { defineMessages, useIntl } from 'react-intl';

import { BigDashedBox } from '../BigDashedBox';

const messages = defineMessages({
  errorOccuredVideoUpload: {
    defaultMessage: 'An error occured when uploading your video. Please retry.',
    description:
      "Button's label offering the user to go validate is form and create a new video.",
    id: 'components.UploadVideoRetry.errorOccuredVideoUpload',
  },
  errorFileTooLarge: {
    defaultMessage: 'Error : File too large. Max size authorized is {maxSize}.',
    description:
      "Button's label explaining the 400 error that happens on large files upload.",
    id: 'components.UploadVideoRetry.errorFileTooLarge',
  },
});

interface UploadVideoRetryProps {
  onClickRetry: () => void;
  maxSize?: number;
}

export const UploadVideoRetry = ({
  onClickRetry,
  maxSize,
}: UploadVideoRetryProps) => {
  const intl = useIntl();
  let outputMessage: string;

  if (maxSize) {
    outputMessage = intl.formatMessage(messages.errorFileTooLarge, {
      maxSize: formatSizeErrorScale(maxSize),
    });
  } else {
    outputMessage = intl.formatMessage(messages.errorOccuredVideoUpload);
  }

  return (
    <BigDashedBox direction="row">
      <Text color={colorsTokens['danger-300']} size="large">
        {outputMessage}
      </Text>
      <RetryUploadButton
        color={colorsTokens['danger-500']}
        onClick={() => onClickRetry()}
        size="large"
      />
    </BigDashedBox>
  );
};
