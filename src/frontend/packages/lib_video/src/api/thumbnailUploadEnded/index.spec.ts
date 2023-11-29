import fetchMock from 'fetch-mock';
import {
  thumbnailMockFactory,
  uploadState,
  useJwt,
  videoMockFactory,
} from 'lib-components';

import { thumbnailUploadEnded } from '.';

describe('sideEffects/uploadEnded', () => {
  beforeEach(() => {
    useJwt.getState().setJwt('some token');
  });

  afterEach(() => fetchMock.restore());

  const video = videoMockFactory({
    upload_state: uploadState.READY,
  });

  const thumbnail = thumbnailMockFactory({
    upload_state: uploadState.READY,
    video: video.id,
  });

  it('makes a POST request on the upload-ended route & returns the updated video', async () => {
    fetchMock.mock(
      `/api/videos/${video.id}/upload-ended/`,
      {
        ...video,
        upload_state: uploadState.PROCESSING,
      },
      { method: 'POST' },
    );
    const updatedVideo = await thumbnailUploadEnded(
      video.id,
      thumbnail.id,
      `tmp/${video.id}/thumbnail/56456454`,
    );

    expect(updatedVideo).toEqual({
      ...video,
      upload_state: uploadState.PROCESSING,
    });
    expect(fetchMock.lastCall()![1]!.headers).toEqual({
      Authorization: 'Bearer some token',
      'Content-Type': 'application/json',
      'Accept-Language': 'en',
    });
  });

  it('throws when it fails to trigger the upload-ended (request failure)', async () => {
    fetchMock.mock(
      `/api/videos/${video.id}/upload-ended/`,
      Promise.reject(new Error('Failed to perform the request')),
    );

    await expect(
      thumbnailUploadEnded(
        video.id,
        thumbnail.id,
        `tmp/${video.id}/thumbnail/56456454`,
      ),
    ).rejects.toThrow('Failed to perform the request');
  });

  it('throws when it fails to trigger the upload-ended (API error)', async () => {
    fetchMock.mock(`/api/videos/${video.id}/upload-ended/`, 400);

    await expect(
      thumbnailUploadEnded(
        video.id,
        thumbnail.id,
        `tmp/${video.id}/thumbnail/56456454`,
      ),
    ).rejects.toThrow(`Failed to end the video upload for video ${video.id}.`);
  });
});
