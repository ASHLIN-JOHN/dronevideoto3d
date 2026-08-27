import os
import cv2
import json
import base64
import time

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY not found in .env"
    )

client = Groq(api_key=api_key)

VIDEO_PATH = "data/synthetic/v1.mp4"

# Take one frame every 2 seconds
FRAME_INTERVAL = 2

# IMPORTANT:
# Start with ONE image per request because your
# current Groq TPM limit is 8000.
BATCH_SIZE = 1

# Resize images before sending them to Groq
MAX_WIDTH = 1024
MAX_HEIGHT = 768

OUTPUT_FILE = "video_analysis.json"

MODEL = "qwen/qwen3.6-27b"


# ============================================================
# RESIZE FRAME
# ============================================================

def resize_frame(frame):

    height, width = frame.shape[:2]

    scale = min(
        MAX_WIDTH / width,
        MAX_HEIGHT / height,
        1.0
    )

    new_width = int(width * scale)
    new_height = int(height * scale)

    if scale < 1.0:

        frame = cv2.resize(
            frame,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA
        )

    return frame


# ============================================================
# FRAME → BASE64
# ============================================================

def frame_to_base64(frame):

    frame = resize_frame(frame)

    # JPEG quality
    encode_params = [
        int(cv2.IMWRITE_JPEG_QUALITY),
        70
    ]

    success, buffer = cv2.imencode(
        ".jpg",
        frame,
        encode_params
    )

    if not success:
        return None

    return base64.b64encode(
        buffer
    ).decode("utf-8")


# ============================================================
# EXTRACT VIDEO FRAMES
# ============================================================

def extract_frames(video_path, interval):

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():

        raise ValueError(
            f"Could not open video: {video_path}"
        )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if fps <= 0:
        fps = 30

    total_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    duration = total_frames / fps

    print(
        f"FPS: {fps:.2f}"
    )

    print(
        f"Total frames: {total_frames}"
    )

    print(
        f"Video duration: {duration:.2f} seconds"
    )

    interval_frames = max(
        1,
        int(fps * interval)
    )

    frames = []

    frame_number = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        if frame_number % interval_frames == 0:

            image = frame_to_base64(frame)

            if image:

                timestamp = frame_number / fps

                frames.append(
                    {
                        "image": image,
                        "timestamp": timestamp,
                        "frame_number": frame_number
                    }
                )

        frame_number += 1

    cap.release()

    return frames


# ============================================================
# PROMPT
# ============================================================

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


# ============================================================
# ANALYZE FRAME
# ============================================================

def analyze_frame(frame, frame_index):

    timestamp = frame["timestamp"]

    print(
        f"\nAnalyzing frame {frame_index}"
        f" | {timestamp:.2f}s"
    )

    content = [

        {
            "type": "text",
            "text": (
                ANALYSIS_PROMPT
                + f"\n\nFrame timestamp: "
                f"{timestamp:.2f} seconds"
            )
        },

        {
            "type": "image_url",
            "image_url": {
                "url":
                "data:image/jpeg;base64,"
                + frame["image"]
            }
        }

    ]

    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ],

            max_completion_tokens=2000,

            response_format={
                "type": "json_object"
            }
        )

        result = (
            response
            .choices[0]
            .message
            .content
        )

        data = json.loads(result)

        return data

    except Exception as e:

        print(
            f"ERROR on frame {frame_index}:"
        )

        print(e)

        return None


# ============================================================
# MAIN
# ============================================================

print("=" * 60)

print(
    "DRONE VIDEO ANALYZER"
)

print("=" * 60)


# ------------------------------------------------------------
# Extract frames
# ------------------------------------------------------------

print(
    "\nExtracting frames..."
)

frames = extract_frames(
    VIDEO_PATH,
    FRAME_INTERVAL
)

print(
    f"\nFrames extracted: "
    f"{len(frames)}"
)


if not frames:

    raise ValueError(
        "No frames extracted."
    )


# ------------------------------------------------------------
# Analyze frames
# ------------------------------------------------------------

analyses = []


for index, frame in enumerate(
    frames,
    start=1
):

    result = analyze_frame(
        frame,
        index
    )

    if result is not None:

        analyses.append(
            {
                "frame_number": index,

                "video_timestamp":
                    frame["timestamp"],

                "analysis":
                    result
            }
        )

    # Small delay to avoid rate-limit problems
    time.sleep(1)


# ============================================================
# FINAL JSON
# ============================================================

final_result = {

    "video": {

        "file":
            VIDEO_PATH,

        "frame_interval_seconds":
            FRAME_INTERVAL,

        "frames_extracted":
            len(frames),

        "frames_successfully_analyzed":
            len(analyses)
    },

    "frames":
        analyses
}


# ============================================================
# SAVE JSON
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        final_result,
        file,
        indent=4,
        ensure_ascii=False
    )


# ============================================================
# FINISHED
# ============================================================

print("\n" + "=" * 60)

print(
    "ANALYSIS COMPLETED"
)

print("=" * 60)

print(
    f"Frames extracted: "
    f"{len(frames)}"
)

print(
    f"Frames analyzed: "
    f"{len(analyses)}"
)

print(
    f"Output: "
    f"{OUTPUT_FILE}"
)