import {
  getByText as getByTextInContainer,
  findByText,
  render,
  screen,
} from '@testing-library/react';
import WS from 'jest-websocket-mock';
import fetchMock from 'fetch-mock';
import React from 'react';

import { FULL_SCREEN_ERROR_ROUTE } from 'components/ErrorComponents/route';
import { timedTextMode, uploadState } from 'types/tracks';
import { report } from 'utils/errors/report';
import { wrapInIntlProvider } from 'utils/tests/intl';
import { wrapInRouter } from 'utils/tests/router';
import { DashboardTimedTextPane } from '.';
import { timedTextMockFactory, videoMockFactory } from 'utils/tests/factories';
import { initVideoWebsocket } from 'data/websocket';
import { modelName } from 'types/models';

jest.mock('data/appData', () => ({
  appData: {
    jwt: 'foo',
  },
}));

jest.mock('utils/errors/report', () => ({
  report: jest.fn(),
}));

const video = videoMockFactory();
let server: WS;

describe('<DashboardTimedTextPane />', () => {
  beforeAll(async () => {
    server = new WS(`ws://localhost:1234/ws/video/${video.id}/`);

    global.window = Object.create(window);
    Object.defineProperty(window, 'location', {
      value: {
        href: 'http://localhost:1234/',
        host: 'localhost:1234',
        protocol: 'http',
      },
    });

    initVideoWebsocket(video);
    await server.connected;
  });

  afterAll(() => {
    server.close();
    WS.clean();
  });

  beforeEach(() => {
    fetchMock.mock(
      '/api/timedtexttracks/',
      {
        actions: {
          POST: {
            language: {
              choices: [
                { display_name: 'English', value: 'en' },
                { display_name: 'French', value: 'fr' },
              ],
            },
          },
        },
      },
      { method: 'OPTIONS' },
    );
  });

  afterEach(() => {
    jest.resetAllMocks();
    fetchMock.restore();
  });

  it('gets the list of timedtexttracks and displays them by mode', async () => {
    const track1 = timedTextMockFactory({
      active_stamp: 2094219242,
      id: '142',
      is_ready_to_show: true,
      language: 'en',
      mode: timedTextMode.SUBTITLE,
      upload_state: uploadState.READY,
      source_url: 'https://example.com/ttt/142',
      url: 'https://example.com/ttt/142.vtt',
      video: '43',
    });
    const track2 = timedTextMockFactory({
      active_stamp: 2094219242,
      id: '144',
      is_ready_to_show: true,
      language: 'fr',
      mode: timedTextMode.CLOSED_CAPTIONING,
      upload_state: uploadState.PROCESSING,
      source_url: 'https://example.com/ttt/144',
      url: 'https://example.com/ttt/144.vtt',
      video: '43',
    });
    fetchMock.get('/api/timedtexttracks/?limit=20&offset=0', {
      count: 2,
      next: null,
      previous: null,
      results: [track1, track2],
    });
    await server.connected;

    render(wrapInIntlProvider(wrapInRouter(<DashboardTimedTextPane />)));

    const closedCaptions = await screen.findByText('Closed captions');
    getByTextInContainer(closedCaptions.parentElement!, 'French');
    getByTextInContainer(closedCaptions.parentElement!, 'Processing');
    const subtitles = screen.getByText('Subtitles');
    getByTextInContainer(subtitles.parentElement!, 'English');
    screen.getByText('Transcripts');

    // Send updated timed text track with upload_state ready.
    // Display should be updated to reflect this change.
    server.send(
      JSON.stringify({
        type: modelName.TIMEDTEXTTRACKS,
        resource: {
          ...track2,
          upload_state: uploadState.READY,
        },
      }),
    );

    await findByText(closedCaptions.parentElement!, (content) =>
      content.startsWith('Ready'),
    );
  });

  it('redirects to the error view when the timedtexttrack list request fails', async () => {
    fetchMock.mock(
      '/api/timedtexttracks/?limit=20&offset=0',
      Promise.reject(new Error('Failed!')),
    );
    render(
      wrapInIntlProvider(
        wrapInRouter(<DashboardTimedTextPane />, [
          {
            path: FULL_SCREEN_ERROR_ROUTE(),
            render: ({ match }) => (
              <span>{`Error Component: ${match.params.code}`}</span>
            ),
          },
        ]),
      ),
    );

    await screen.findByText('Error Component: notFound');
    expect(report).toBeCalledWith(new Error('Failed!'));
  });
});
