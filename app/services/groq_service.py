import os
import json
import time
import base64
import logging
from pathlib import Path

import cv2
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """
Analyze this drone video frame.

Return ONLY valid JSON.

DO NOT:
- use markdown
- use ```json
- write explanations outside JSON
- invent information
- guess compass directions

If something cannot be determined, use null.

============================================================
SCENE
============================================================

Identify:

- overall scene
- weather
- time of day
- environment


============================================================
OBJECTS
============================================================

Detect visible:

- people
- cars
- trucks
- motorcycles
- bicycles
- buildings
- houses
- trees
- vegetation
- poles
- signs
- road markings
- bridges
- water
- rivers
- mountains
- hills
- rocks
- fences
- walls
- other important objects

For every object provide:

- type
- position
- color
- estimated_size
- movement
- confidence

Use image-relative positions:

top_left
top_center
top_right
middle_left
center
middle_right
bottom_left
bottom_center
bottom_right


============================================================
TERRAIN
============================================================

Analyze:

- terrain type
- terrain color
- terrain texture
- vegetation
- slope
- dryness
- ground condition

Do not invent exact RGB values.

Use descriptive colors such as:

brown
dark_brown
light_brown
green
dark_green
gray
dark_gray
yellow
sand_color
reddish_brown


============================================================
ROAD
============================================================

Analyze:

- road present
- road type
- road color
- road condition
- approximate width
- direction in image
- lane markings
- traffic


============================================================
SUN
============================================================

Analyze:

- whether sun is visible
- sun position
- lighting direction
- shadow direction
- shadow length
- approximate time of day

Do NOT determine north/east/south/west from the sun.

Use image-relative directions instead.


============================================================
DIRECTIONS
============================================================

Only provide compass directions if reliable orientation metadata
is available.

Otherwise:

camera_facing = null
north = null
east = null
south = null
west = null


============================================================
OUTPUT
============================================================

Return exactly:

{
    "scene": {
        "description": null,
        "weather": null,
        "time_of_day": null
    },

    "objects": [
        {
            "type": null,
            "position": null,
            "color": null,
            "estimated_size": null,
            "movement": null,
            "confidence": 0.0
        }
    ],

    "terrain": {
        "type": null,
        "color": null,
        "texture": null,
        "vegetation": null,
        "slope": null,
        "dryness": null,
        "ground_condition": null,
        "confidence": 0.0
    },

    "road": {
        "present": false,
        "type": null,
        "color": null,
        "condition": null,
        "width": null,
        "direction_in_image": null,
        "lane_markings": null,
        "traffic": null,
        "confidence": 0.0
    },

    "sun": {
        "visible": false,
        "position": null,
        "lighting_direction": null,
        "shadow_direction": null,
        "shadow_length": null,
        "confidence": 0.0
    },

    "directions": {
        "camera_facing": null,
        "north": null,
        "east": null,
        "south": null,
        "west": null
    }
}
"""

MAX_WIDTH = 1024
MAX_HEIGHT = 768
MODEL = "qwen/qwen3.6-27b"


class GroqService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        self.progress_callback = None

        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")

    def is_available(self):
        return self.client is not None

    def set_progress_callback(self, callback):
        self.progress_callback = callback

    def _emit_progress(self, message):
        logger.info(message)
        if self.progress_callback:
            self.progress_callback(message)

    def _resize_frame(self, frame):
        height, width = frame.shape[:2]
        scale = min(MAX_WIDTH / width, MAX_HEIGHT / height, 1.0)
        if scale < 1.0:
            new_w = int(width * scale)
            new_h = int(height * scale)
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return frame

    def _frame_to_base64(self, frame):
        frame = self._resize_frame(frame)
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
        success, buffer = cv2.imencode(".jpg", frame, encode_params)
        if not success:
            return None
        return base64.b64encode(buffer).decode("utf-8")

    def extract_frames(self, video_path, interval=2):
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        interval_frames = max(1, int(fps * interval))

        frames = []
        frame_number = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_number % interval_frames == 0:
                image = self._frame_to_base64(frame)
                if image:
                    timestamp = frame_number / fps
                    frames.append({
                        "image": image,
                        "timestamp": timestamp,
                        "frame_number": frame_number,
                    })
            frame_number += 1

        cap.release()
        return frames

    def analyze_frame(self, frame_data, frame_index):
        if not self.client:
            return None

        timestamp = frame_data["timestamp"]
        self._emit_progress(f"Analyzing frame {frame_index} | {timestamp:.2f}s")

        content = [
            {
                "type": "text",
                "text": ANALYSIS_PROMPT + f"\n\nFrame timestamp: {timestamp:.2f} seconds",
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/jpeg;base64," + frame_data["image"]
                },
            },
        ]

        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": content}],
                max_completion_tokens=2000,
                response_format={"type": "json_object"},
            )
            result = response.choices[0].message.content
            return json.loads(result)
        except Exception as e:
            logger.error(f"Error analyzing frame {frame_index}: {e}")
            return None

    def analyze_video(self, video_path, frame_interval=2, output_path=None):
        self._emit_progress("Extracting frames...")
        frames = self.extract_frames(video_path, frame_interval)
        self._emit_progress(f"Extracted {len(frames)} frames")

        if not frames:
            raise ValueError("No frames extracted from video")

        analyses = []
        total = len(frames)

        for index, frame_data in enumerate(frames, start=1):
            self._emit_progress(f"Analyzing frame {index}/{total}...")
            result = self.analyze_frame(frame_data, index)
            if result is not None:
                analyses.append({
                    "frame_number": index,
                    "video_timestamp": frame_data["timestamp"],
                    "analysis": result,
                })
            time.sleep(1)

        final_result = {
            "video": {
                "file": str(video_path),
                "frame_interval_seconds": frame_interval,
                "frames_extracted": len(frames),
                "frames_successfully_analyzed": len(analyses),
            },
            "frames": analyses,
        }

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(final_result, f, indent=4, ensure_ascii=False)
            self._emit_progress(f"Analysis saved to {output_path}")

        self._emit_progress("Analysis complete")
        return final_result
