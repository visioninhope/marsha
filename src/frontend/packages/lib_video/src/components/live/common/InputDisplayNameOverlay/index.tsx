import { Box } from 'grommet';
import { ExitCrossSVG } from 'lib-components';
import React from 'react';
import { defineMessages, useIntl } from 'react-intl';

import { useSetDisplayName } from '@lib-video/hooks/useSetDisplayName';

import { InputDisplayName } from '../InputDisplayName';

const messages = defineMessages({
  closeButtonTitle: {
    defaultMessage: 'Click this button to close the overlay.',
    description: 'A title describing the close button action',
    id: 'components.InputDiplayNameOverlay.closeButtonTitle',
  },
});

export const InputDisplayNameOverlay = () => {
  const intl = useIntl();
  const [_, setDisplayName] = useSetDisplayName();

  const hideDisplayName = () => {
    setDisplayName(false);
  };

  return (
    <Box height="100%">
      <Box
        direction="row-reverse"
        margin={{
          right: '5px',
          top: '5px',
        }}
      >
        <Box
          onClick={hideDisplayName}
          title={intl.formatMessage(messages.closeButtonTitle)}
        >
          <ExitCrossSVG
            containerStyle={{
              height: '20px',
              width: '20px',
            }}
            iconColor="blue-focus"
          />
        </Box>
      </Box>
      <Box height="100%">
        <InputDisplayName onSuccess={hideDisplayName} />
      </Box>
    </Box>
  );
};
