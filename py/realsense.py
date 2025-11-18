import pyrealsense2 as rs2
import numpy as np
import cv2

RAW_WIDTH = 640
RAW_HEIGHT = 480

DOWNSAMPLE_FACTOR = 2
TARGET_WIDTH = RAW_WIDTH // DOWNSAMPLE_FACTOR
TARGET_HEIGHT = RAW_HEIGHT // DOWNSAMPLE_FACTOR
MIN_SPEED_THRESHOLD = 8 // DOWNSAMPLE_FACTOR
MAX_SPEED_THRESHOLD = 64 // DOWNSAMPLE_FACTOR

GRID_SIZE = 16
GRID_WIDTH = TARGET_WIDTH // GRID_SIZE
GRID_HEIGHT = TARGET_HEIGHT // GRID_SIZE

def init_realsense_pipeline():
    _pipeline = rs2.pipeline()
    _config = rs2.config()
    _config.enable_stream(rs2.stream.depth, RAW_WIDTH, RAW_HEIGHT, rs2.format.z16, 30)
    _profile = _pipeline.start(_config)

    print("RealSense pipeline started successfully.")

    return _pipeline, _profile

# Get frames and downsample frames
def fetch_depth_for_flow(_pipeline):
    if not _pipeline:
        return None
    
    _frameset = _pipeline.wait_for_frames()
    if not _frameset:
        return None
    
    _depth_frame = _frameset.get_depth_frame()
    if not _depth_frame:
        return None
    
    _depth_image_original = np.asanyarray(_depth_frame.get_data())
    _depth_image_downsampled = cv2.resize(
        _depth_image_original,
        (TARGET_WIDTH, TARGET_HEIGHT),
        interpolation=cv2.INTER_LINEAR
    )
    _depth_image_normalized = cv2.normalize(
        _depth_image_downsampled,
        None, 0, 255, cv2.NORM_MINMAX
    ).astype(np.uint8)

    return _depth_image_normalized

def process_flow_for_visualization(_current_frame, _previous_frame):
    # Optical flow (Farneback method)
    _flow = cv2.calcOpticalFlowFarneback(
        _previous_frame,
        _current_frame,
        None, 0.5, 3, 15, 3, 5, 1.2, 0
    )

    # Get speed (magnitude) and angle of the flow
    _magnitude, _ = cv2.cartToPolar(
        _flow[..., 0], _flow[..., 1], angleInDegrees=True
    )

    _magnitude_smoothed = cv2.GaussianBlur(
        _magnitude, (5, 5), 0
    )

    _magnitude_clipped = np.clip(
        _magnitude_smoothed, MIN_SPEED_THRESHOLD, MAX_SPEED_THRESHOLD
    )

    _magnitude_normalized = cv2.normalize(
        _magnitude_clipped,
        None, 0, 255, cv2.NORM_MINMAX
    ).astype(np.uint8)

    return _magnitude_normalized

def divide_flow_into_cells(_flow):
    _flow_float = _flow.astype(np.float32)
    _flow_reshaped = _flow_float.reshape(
        GRID_HEIGHT, GRID_SIZE,
        GRID_WIDTH, GRID_SIZE
    )

    # average of each grid
    _flow_cells = _flow_reshaped.mean(axis=(1, 3))

    return _flow_cells