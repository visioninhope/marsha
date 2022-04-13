import { fireEvent, render, screen } from '@testing-library/react';
import React, { Suspense } from 'react';
import { Grommet, Tab } from 'grommet';

import { appData } from '../../data/appData';
import {
  documentMockFactory,
  playlistMockFactory,
  videoMockFactory,
} from '../../utils/tests/factories';
import { SelectContent, SelectContentTabProps } from './index';
import { wrapInIntlProvider } from '../../utils/tests/intl';
import { uploadState } from '../../types/tracks';
import { Toaster } from 'react-hot-toast';

jest.mock('../../data/appData', () => ({
  appData: {
    new_document_url: 'https://example.com/lti/documents/new-hash',
    new_video_url: 'https://example.com/lti/videos/new-hash',
    lti_select_form_action_url: '/lti/select/',
    lti_select_form_data: {},
  },
}));

jest.mock('../Loader', () => ({
  Loader: () => <span>Loader</span>,
}));

const mockCustomSelectContentTab = ({
  selectContent,
}: SelectContentTabProps) => (
  <Tab title="Custom app tab">
    <p
      onClick={() =>
        selectContent(
          'custom-select-content-url',
          'Custom select content title',
          'Custom select content description',
        )
      }
    >
      Select app content
    </p>
  </Tab>
);

jest.mock(
  '../../apps/custom_app/SelectContentTab',
  () => mockCustomSelectContentTab,
  {
    virtual: true,
  },
);

const mockOtherCustomSelectContentTab = ({
  selectContent,
}: SelectContentTabProps) => (
  <Tab title="Other custom app tab">
    <p
      onClick={() =>
        selectContent(
          'other-custom-select-content-url',
          'Other custom select content title',
          'Other custom select content description',
        )
      }
    >
      Other select app content
    </p>
  </Tab>
);

jest.mock(
  '../../apps/other_custom_app/SelectContentTab',
  () => mockOtherCustomSelectContentTab,
  {
    virtual: true,
  },
);

/**
 * Mock available app type in the front to provide the app used in the test
 */
jest.mock('types/AppData.ts', () => ({
  appNames: {
    custom_app: 'custom_app',
    other_custom_app: 'other_custom_app',
  },
}));

/**
 * Mock appConfig to override real config because enums are mock
 * and real values don't exist anymore
 */
jest.mock('data/appConfigs.ts', () => ({
  appConfigs: {},
}));

window.HTMLFormElement.prototype.submit = jest.fn();

describe('<SelectContent />', () => {
  afterEach(jest.resetAllMocks);

  it('displays content infos', async () => {
    render(
      wrapInIntlProvider(
        <Grommet>
          <Toaster />
          <SelectContent
            playlist={playlistMockFactory({
              id: '1',
              title: 'Playlist 1',
            })}
            documents={[
              documentMockFactory({
                id: '1',
                title: 'Document 1',
                upload_state: uploadState.PROCESSING,
                is_ready_to_show: false,
              }),
            ]}
            videos={[
              videoMockFactory({
                id: '1',
                title: 'Video 1',
                upload_state: uploadState.PROCESSING,
                is_ready_to_show: false,
              }),
              videoMockFactory({
                id: '2',
                title: 'Video 2',
                upload_state: uploadState.READY,
                is_ready_to_show: true,
              }),
            ]}
            new_document_url={appData.new_document_url}
            new_video_url={appData.new_video_url}
            lti_select_form_action_url={appData.lti_select_form_action_url!}
            lti_select_form_data={appData.lti_select_form_data!}
          />
        </Grommet>,
      ),
    );

    screen.getByText('Playlist Playlist 1 (1)');

    const video1 = screen.getByTitle('Select Video 1');
    expect(video1.getElementsByTagName('img')[0]).toHaveAttribute(
      'src',
      'https://example.com/default_thumbnail/144',
    );

    expect(screen.queryByText('Video 1')).toBeNull();
    expect(screen.queryByText('Not uploaded')).toBeNull();
    expect(screen.queryByText('Not ready to show')).toBeNull();
    fireEvent.mouseEnter(video1);
    screen.getByText('Video 1');
    screen.getByLabelText('Not uploaded');
    screen.getByLabelText('Not ready to show');
    fireEvent.mouseLeave(video1);

    expect(screen.queryByText('Video 2')).toBeNull();
    expect(screen.queryByText('Uploaded')).toBeNull();
    expect(screen.queryByText('Ready to show')).toBeNull();
    fireEvent.mouseEnter(screen.getByTitle('Select Video 2'));
    screen.getByText('Video 2');
    screen.getByLabelText('Uploaded');
    screen.getByLabelText('Ready to show');

    screen.getByRole('tab', {
      name: /videos/i,
    });

    expect(screen.queryByText('Document 1')).toBeNull();
    expect(screen.queryByText('Not uploaded')).toBeNull();
    expect(screen.queryByText('Not ready to show')).toBeNull();
    const documentTab = screen.getByRole('tab', {
      name: 'Documents',
    });
    fireEvent.click(documentTab);
    fireEvent.mouseEnter(screen.getByTitle('Select Document 1'));
    screen.getByText('Document 1');
    screen.getByLabelText('Not uploaded');
    screen.getByLabelText('Not ready to show');
  });

  it('displays first available generated video thumbnail', async () => {
    render(
      wrapInIntlProvider(
        <Grommet>
          <SelectContent
            videos={[
              videoMockFactory({
                id: '1',
                title: 'Video 1',
                upload_state: uploadState.PROCESSING,
                is_ready_to_show: false,
                urls: {
                  manifests: {
                    hls: '',
                  },
                  mp4: {},
                  thumbnails: {
                    480: 'https://example.com/default_thumbnail/480',
                    720: 'https://example.com/default_thumbnail/720',
                    1080: 'https://example.com/default_thumbnail/1080',
                  },
                },
              }),
            ]}
            new_document_url={appData.new_document_url}
            new_video_url={appData.new_video_url}
            lti_select_form_action_url={appData.lti_select_form_action_url!}
            lti_select_form_data={appData.lti_select_form_data!}
          />
        </Grommet>,
      ),
    );

    screen.getByTitle('Select Video 1');
    expect(
      screen.getByTitle('Select Video 1').getElementsByTagName('img')[0],
    ).toHaveAttribute('src', 'https://example.com/default_thumbnail/480');
  });

  it('displays first available uploaded video thumbnail', async () => {
    render(
      wrapInIntlProvider(
        <Grommet>
          <SelectContent
            videos={[
              videoMockFactory({
                id: '1',
                title: 'Video 1',
                upload_state: uploadState.PROCESSING,
                is_ready_to_show: false,
                thumbnail: {
                  active_stamp: null,
                  is_ready_to_show: true,
                  upload_state: uploadState.READY,
                  id: '1',
                  video: '1',
                  urls: {
                    480: 'https://example.com/uploaded_thumbnail/480',
                    720: 'https://example.com/uploaded_thumbnail/720',
                    1080: 'https://example.com/uploaded_thumbnail/1080',
                  },
                },
              }),
            ]}
            new_document_url={appData.new_document_url}
            new_video_url={appData.new_video_url}
            lti_select_form_action_url={appData.lti_select_form_action_url!}
            lti_select_form_data={appData.lti_select_form_data!}
          />
        </Grommet>,
      ),
    );

    screen.getByTitle('Select Video 1');
    expect(
      screen.getByTitle('Select Video 1').getElementsByTagName('img')[0],
    ).toHaveAttribute('src', 'https://example.com/uploaded_thumbnail/480');
  });

  it('fallback to generated video thumbnail if uploaded thumbnail not ready', async () => {
    render(
      wrapInIntlProvider(
        <Grommet>
          <SelectContent
            videos={[
              videoMockFactory({
                id: '1',
                title: 'Video 1',
                upload_state: uploadState.PROCESSING,
                is_ready_to_show: false,
                thumbnail: {
                  active_stamp: null,
                  is_ready_to_show: false,
                  upload_state: uploadState.PROCESSING,
                  id: '1',
                  video: '1',
                  urls: {
                    480: 'https://example.com/uploaded_thumbnail/480',
                    720: 'https://example.com/uploaded_thumbnail/720',
                    1080: 'https://example.com/uploaded_thumbnail/1080',
                  },
                },
              }),
            ]}
            new_document_url={appData.new_document_url}
            new_video_url={appData.new_video_url}
            lti_select_form_action_url={appData.lti_select_form_action_url!}
            lti_select_form_data={appData.lti_select_form_data!}
          />
        </Grommet>,
      ),
    );

    screen.getByTitle('Select Video 1');
    expect(
      screen.getByTitle('Select Video 1').getElementsByTagName('img')[0],
    ).toHaveAttribute('src', 'https://example.com/default_thumbnail/144');
  });

  it('video not uploaded', async () => {
    render(
      wrapInIntlProvider(
        <Grommet>
          <SelectContent
            videos={[
              videoMockFactory({
                id: '1',
                title: 'Video 1',
                upload_state: uploadState.PENDING,
                is_ready_to_show: false,
                urls: null,
              }),
            ]}
            new_document_url={appData.new_document_url}
            new_video_url={appData.new_video_url}
            lti_select_form_action_url={appData.lti_select_form_action_url!}
            lti_select_form_data={appData.lti_select_form_data!}
          />
        </Grommet>,
      ),
    );

    fireEvent.mouseEnter(screen.getByTitle('Select Video 1'));
    screen.getByText('Video 1');
    screen.getByLabelText('Not uploaded');
    screen.getByLabelText('Not ready to show');
  });

  it('select content', async () => {
    const { container } = render(
      wrapInIntlProvider(
        <SelectContent
          documents={[
            documentMockFactory({
              id: '1',
              title: 'Document 1',
              description: 'Document 1 description',
              upload_state: uploadState.PROCESSING,
              is_ready_to_show: false,
            }),
          ]}
          lti_select_form_action_url={appData.lti_select_form_action_url!}
          lti_select_form_data={{
            lti_response_url: 'https://example.com/lti',
            lti_message_type: 'ContentItemSelection',
          }}
        />,
      ),
    );

    const documentTab = screen.getByRole('tab', {
      name: 'Documents',
    });
    fireEvent.click(documentTab);
    fireEvent.click(screen.getByTitle('Select Document 1'));

    expect(window.HTMLFormElement.prototype.submit).toHaveBeenCalledTimes(1);

    expect(container.querySelector('form')).toHaveFormValues({
      lti_response_url: 'https://example.com/lti',
      lti_message_type: 'ContentItemSelection',
      content_items: JSON.stringify({
        '@context': 'http://purl.imsglobal.org/ctx/lti/v1/ContentItem',
        '@graph': [
          {
            '@type': 'ContentItem',
            url: 'https://example.com/lti/documents/1',
            frame: [],
            title: 'Document 1',
            text: 'Document 1 description',
          },
        ],
      }),
    });
  });

  it('select content with activity title and description', async () => {
    const { container } = render(
      wrapInIntlProvider(
        <SelectContent
          documents={[
            documentMockFactory({
              id: '1',
              title: 'Document 1',
              description: 'Document 1 description',
              upload_state: uploadState.PROCESSING,
              is_ready_to_show: false,
            }),
          ]}
          lti_select_form_action_url={appData.lti_select_form_action_url!}
          lti_select_form_data={{
            lti_response_url: 'https://example.com/lti',
            lti_message_type: 'ContentItemSelection',
            activity_title: 'Activity title',
            activity_description: 'Activity description',
          }}
        />,
      ),
    );

    const documentTab = screen.getByRole('tab', {
      name: 'Documents',
    });
    userEvent.click(documentTab);
    userEvent.click(screen.getByTitle('Select Document 1'));

    expect(window.HTMLFormElement.prototype.submit).toHaveBeenCalledTimes(1);

    expect(container.querySelector('form')).toHaveFormValues({
      lti_response_url: 'https://example.com/lti',
      lti_message_type: 'ContentItemSelection',
      content_items: JSON.stringify({
        '@context': 'http://purl.imsglobal.org/ctx/lti/v1/ContentItem',
        '@graph': [
          {
            '@type': 'ContentItem',
            url: 'https://example.com/lti/documents/1',
            frame: [],
            title: 'Activity title',
            text: 'Activity description',
          },
        ],
      }),
    });
  });

  it('select content without document title', async () => {
    const { container } = render(
      wrapInIntlProvider(
        <SelectContent
          documents={[
            documentMockFactory({
              id: '1',
              title: null,
              description: 'Document 1 description',
              upload_state: uploadState.PROCESSING,
              is_ready_to_show: false,
            }),
          ]}
          lti_select_form_action_url={appData.lti_select_form_action_url!}
          lti_select_form_data={{
            lti_response_url: 'https://example.com/lti',
            lti_message_type: 'ContentItemSelection',
          }}
        />,
      ),
    );

    const documentTab = screen.getByRole('tab', {
      name: 'Documents',
    });
    userEvent.click(documentTab);
    userEvent.click(screen.getByTitle('Select'));

    expect(window.HTMLFormElement.prototype.submit).toHaveBeenCalledTimes(1);

    expect(container.querySelector('form')).toHaveFormValues({
      lti_response_url: 'https://example.com/lti',
      lti_message_type: 'ContentItemSelection',
      content_items: JSON.stringify({
        '@context': 'http://purl.imsglobal.org/ctx/lti/v1/ContentItem',
        '@graph': [
          {
            '@type': 'ContentItem',
            url: 'https://example.com/lti/documents/1',
            frame: [],
            text: 'Document 1 description',
          },
        ],
      }),
    });
  });

  it('add new content', async () => {
    const { container } = render(
      wrapInIntlProvider(
        <SelectContent
          documents={appData.documents}
          videos={appData.videos}
          new_document_url={appData.new_document_url}
          new_video_url={appData.new_video_url}
          lti_select_form_action_url={appData.lti_select_form_action_url!}
          lti_select_form_data={appData.lti_select_form_data!}
        />,
      ),
    );
    fireEvent.click(screen.getByText('Add a video'));

    expect(window.HTMLFormElement.prototype.submit).toHaveBeenCalledTimes(1);

    const form = container.querySelector('form');
    expect(form).toHaveFormValues({
      content_items: JSON.stringify({
        '@context': 'http://purl.imsglobal.org/ctx/lti/v1/ContentItem',
        '@graph': [
          {
            '@type': 'ContentItem',
            url: 'https://example.com/lti/videos/new-hash',
            frame: [],
          },
        ],
      }),
    });
    expect(form).toHaveAttribute('action', '/lti/select/');
  });

  it('add new content with activity title and description', async () => {
    const { container } = render(
      wrapInIntlProvider(
        <SelectContent
          documents={appData.documents}
          videos={appData.videos}
          new_document_url={appData.new_document_url}
          new_video_url={appData.new_video_url}
          lti_select_form_action_url={appData.lti_select_form_action_url!}
          lti_select_form_data={{
            ...appData.lti_select_form_data!,
            activity_title: 'Activity title',
            activity_description: 'Activity description',
          }}
        />,
      ),
    );
    fireEvent.click(screen.getByText('Add a video'));

    expect(window.HTMLFormElement.prototype.submit).toHaveBeenCalledTimes(1);

    const form = container.querySelector('form');
    expect(form).toHaveFormValues({
      content_items: JSON.stringify({
        '@context': 'http://purl.imsglobal.org/ctx/lti/v1/ContentItem',
        '@graph': [
          {
            '@type': 'ContentItem',
            url: 'https://example.com/lti/videos/new-hash',
            frame: [],
            title: 'Activity title',
            text: 'Activity description',
          },
        ],
      }),
    });
    expect(form).toHaveAttribute('action', '/lti/select/');
  });

  it('loads app tab', async () => {
    const { container } = render(
      wrapInIntlProvider(
        <Suspense fallback="Loading...">
          <SelectContent
            lti_select_form_action_url={appData.lti_select_form_action_url!}
            lti_select_form_data={{
              lti_response_url: 'https://example.com/lti',
              lti_message_type: 'ContentItemSelection',
            }}
          />
        </Suspense>,
      ),
    );

    const otherCustomAppTab = await screen.findByRole('tab', {
      name: 'Other custom app tab',
    });
    fireEvent.click(otherCustomAppTab);
    screen.getByText('Other select app content');
    expect(screen.queryByText('Select app content')).not.toBeInTheDocument();

    const customAppTab = await screen.findByRole('tab', {
      name: 'Custom app tab',
    });
    fireEvent.click(customAppTab);
    expect(
      screen.queryByText('Other select app content'),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByText('Select app content'));

    expect(window.HTMLFormElement.prototype.submit).toHaveBeenCalledTimes(1);

    expect(container.querySelector('form')).toHaveFormValues({
      lti_response_url: 'https://example.com/lti',
      lti_message_type: 'ContentItemSelection',
      content_items: JSON.stringify({
        '@context': 'http://purl.imsglobal.org/ctx/lti/v1/ContentItem',
        '@graph': [
          {
            '@type': 'ContentItem',
            url: 'custom-select-content-url',
            frame: [],
            title: 'Custom select content title',
            text: 'Custom select content description',
          },
        ],
      }),
    });
  });
});
