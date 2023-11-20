""" Utils related to transcoding """
from marsha.core.defaults import PEERTUBE_PIPELINE, READY
from marsha.core.models.video import Video
from marsha.core.utils.time_utils import to_datetime
from marsha.websocket.utils import channel_layers_utils


def transcoding_ended_callback(transcoded_video):
    """
    Callback used when the a Peertube runnner has finished
    to transcode a video.

    Parameters
    ----------
    transcoded_video : Type[Video]
        The transcoded video (The video a django_peertube_runner_connector Video model).

    """
    # Directory format: "scw/<video_id>/video/<stamp>"
    directory = transcoded_video.directory.split("/")
    uploaded_on = directory[-1]
    video_id = directory[-3]
    video = Video.objects.get(pk=video_id)

    video.uploaded_on = to_datetime(uploaded_on)
    if transcoded_video.streamingPlaylist:
        video.resolutions = [
            x.resolution for x in transcoded_video.streamingPlaylist.videoFiles.all()
        ]
    video.upload_state = READY
    video.transcode_pipeline = PEERTUBE_PIPELINE
    video.save()

    channel_layers_utils.dispatch_video(video, to_admin=True)
