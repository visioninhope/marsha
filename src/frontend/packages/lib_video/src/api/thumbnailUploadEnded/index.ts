import {
  API_ENDPOINT,
  Thumbnail,
  Video,
  fetchResponseHandler,
  fetchWrapper,
  useJwt,
} from 'lib-components';

/**
 * Post to an action endpoint to inform the end of the video upload.
 * Returns the updated video
 * @param video this video's file has been uploaded
 */
export const thumbnailUploadEnded = async (
  videoId: Video['id'],
  thumbnailId: Thumbnail['id'],
  fileKey: string,
): Promise<Thumbnail> => {
  const body = {
    file_key: fileKey,
  };

  const response = await fetchWrapper(
    `${API_ENDPOINT}/videos/${videoId}/thumbnails/${thumbnailId}/upload-ended/`,
    {
      body: JSON.stringify(body),
      headers: {
        Authorization: `Bearer ${useJwt.getState().getJwt() ?? ''}`,
        'Content-Type': 'application/json',
      },
      method: 'POST',
    },
  );

  return await fetchResponseHandler(response, {
    errorMessage: `Failed to end the thumbnail upload for thumbnail ${thumbnailId}.`,
  });
};
