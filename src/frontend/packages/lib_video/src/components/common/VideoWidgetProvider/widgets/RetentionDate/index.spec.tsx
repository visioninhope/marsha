import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import fetchMock from 'fetch-mock';
import { InfoWidgetModalProvider, useJwt } from 'lib-components';
import { videoMockFactory } from 'lib-components/tests';
import { render, userTypeDatePicker } from 'lib-tests';
import { DateTime, Settings } from 'luxon';

import { wrapInVideo } from '@lib-video/utils/wrapInVideo';

import { RetentionDate } from '.';

Settings.defaultLocale = 'en';
Settings.defaultZone = 'Europe/Paris';

jest.mock('lib-components', () => ({
  ...jest.requireActual('lib-components'),
  report: jest.fn(),
}));

describe('Video <RetentionDate />', () => {
  beforeEach(() => {
    useJwt.setState({
      jwt: 'json web token',
    });
  });

  afterEach(() => {
    jest.resetAllMocks();
    fetchMock.restore();
  });

  it('renders the component and set a date with success', async () => {
    const mockedVideo = videoMockFactory();

    fetchMock.mock(
      `/api/videos/${mockedVideo.id}/`,
      {
        status: 200,
        body: mockedVideo,
      },
      { method: 'PATCH' },
    );

    render(
      wrapInVideo(
        <InfoWidgetModalProvider value={null}>
          <RetentionDate />
        </InfoWidgetModalProvider>,
        mockedVideo,
      ),
    );

    expect(screen.getAllByText('Retention date')).toBeTruthy();

    const inputRetentionDate = within(
      screen.getByTestId('retention-date-picker'),
    ).getByRole('presentation');

    expect(inputRetentionDate).toHaveTextContent('MM/DD/YYYY');

    const retentionDate = DateTime.local()
      .plus({ days: 1 })
      .set({ second: 0, millisecond: 0 });

    await userTypeDatePicker(
      retentionDate,
      screen.getAllByText(/Retention date/i)[1],
    );

    expect(inputRetentionDate).toHaveTextContent(
      retentionDate.toLocaleString(),
    );

    await waitFor(() => expect(fetchMock.calls()).toHaveLength(1));

    const lastCall = fetchMock.lastCall();
    expect(lastCall).not.toBe(undefined);
    expect(lastCall?.[0]).toBe(`/api/videos/${mockedVideo.id}/`);
    expect(lastCall?.[1]?.body).toEqual(
      `{"retention_date":"${retentionDate.toISODate()!}"}`,
    );
    expect(lastCall?.[1]?.method).toBe('PATCH');

    await screen.findByText('Video updated.');
  });

  it('renders the component with a default date and deletes it', async () => {
    const retentionDate = DateTime.utc()
      .plus({ days: 1 })
      .set({ second: 0, millisecond: 0 });

    const mockedVideo = videoMockFactory({
      retention_date: retentionDate.toISODate(),
    });

    fetchMock.mock(
      `/api/videos/${mockedVideo.id}/`,
      {
        status: 200,
        body: mockedVideo,
      },
      { method: 'PATCH' },
    );

    render(
      wrapInVideo(
        <InfoWidgetModalProvider value={null}>
          <RetentionDate />
        </InfoWidgetModalProvider>,
        mockedVideo,
      ),
    );

    expect(screen.getAllByText('Retention date')).toBeTruthy();

    const inputRetentionDate = within(
      screen.getByTestId('retention-date-picker'),
    ).getByRole('presentation');
    expect(inputRetentionDate).toHaveTextContent(
      retentionDate.toLocaleString(),
    );

    const deleteButton = await screen.findByRole('button', {
      name: 'Delete retention date',
    });

    await userEvent.click(deleteButton);

    await waitFor(() => expect(fetchMock.calls()).toHaveLength(1));

    const lastCall = fetchMock.lastCall();
    expect(lastCall).not.toBe(undefined);
    expect(lastCall?.[0]).toBe(`/api/videos/${mockedVideo.id}/`);
    expect(lastCall?.[1]?.body).toEqual('{"retention_date":null}');
    expect(lastCall?.[1]?.method).toBe('PATCH');

    await screen.findByText('Video updated.');
  });

  it('fails to update the video and displays the right error message', async () => {
    // Set by default with an All rights reserved license
    const mockedVideo = videoMockFactory({
      retention_date: '2020-01-01',
    });
    fetchMock.patch(`/api/videos/${mockedVideo.id}/`, 401);

    render(
      wrapInVideo(
        <InfoWidgetModalProvider value={null}>
          <RetentionDate />
        </InfoWidgetModalProvider>,
        mockedVideo,
      ),
    );

    const deleteButton = await screen.findByRole('button', {
      name: 'Delete retention date',
    });

    await userEvent.click(deleteButton);

    await waitFor(() => expect(fetchMock.calls()).toHaveLength(1));

    await screen.findByText('Video update has failed!');
  });
});
