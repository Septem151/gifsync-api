"""Jobs that are ran by the RQ Worker nodes."""
import os
import re
import subprocess
from decimal import ROUND_HALF_UP, Decimal

from dotenv import load_dotenv
from flask import current_app
from flask.cli import ScriptInfo

from .extensions import s3

_num_frames_pattern = re.compile(r"(?P<num_frames>\d+) images")


def _get_num_frames(image_bytes: bytes) -> int:
    try:
        cmd = subprocess.run(
            ["gifsicle", "-I"], input=image_bytes, capture_output=True, check=True
        )
        cmd_data = cmd.stdout.decode("utf-8")
        res = _num_frames_pattern.search(cmd_data)
        if res:
            return int(res.group("num_frames"))
        return -1
    except subprocess.CalledProcessError as error:
        # TODO: Handle error better by logging rather than crashing
        raise RuntimeError("Could not sync image") from error


def _get_frame_times(tempo: float, num_frames: int, beats_per_loop: float) -> list:
    beats_per_second = tempo / 60
    seconds_per_beat = 1 / beats_per_second
    total_duration = int(
        Decimal(seconds_per_beat * beats_per_loop * 100).to_integral_value(
            ROUND_HALF_UP
        )
    )
    base_frame_duration, extra_frame_duration = divmod(total_duration, num_frames)
    frame_times = [base_frame_duration] * num_frames
    for i in range(0, extra_frame_duration):
        frame_times[(i * num_frames // extra_frame_duration) % num_frames] += 1
    return frame_times


def sync_gif(gif_name: str, tempo: float, beats_per_loop: float) -> bool:
    """Synchronizes a gif from S3 with the given tempo, then updates
    the gif in S3.

    Args:
        gif_name (:obj:`str`): Name of the gif in S3.
        tempo (:obj:`float`): Tempo to sync the gif to.
        beats_per_loop (:obj:`float`): Beats per loop to sync the gif to.

    Raises:
        :obj:`RuntimeError`: If gifsicle could not create a new gif.

    Returns:
        :obj:`bool`: Whether the operation completed successfully.
    """
    if not os.environ.get("FLASK_APP"):
        load_dotenv(".flaskenv")
    if current_app:
        app = current_app
    else:
        app = ScriptInfo().load_app()
    with app.app_context():
        image_bytes = s3.get_image(gif_name)
        if not image_bytes:
            return False
        num_frames = _get_num_frames(image_bytes)
        frame_times = _get_frame_times(tempo, num_frames, beats_per_loop)
        args = [
            "gifsicle",
            "-o",
            "-",
        ]
        for frame_index, frame_time in enumerate(frame_times):
            args.append(f"-d{frame_time}")
            args.append(f"#{frame_index}")
        try:
            result = subprocess.run(
                args, input=image_bytes, capture_output=True, check=True
            )
            result_data = result.stdout
            s3.update_image(gif_name, result_data)
            return True
        except subprocess.CalledProcessError as error:
            # TODO: Handle error better by logging rather than crashing
            raise RuntimeError("Could not sync image") from error
