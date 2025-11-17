import pyrealsense2 as rs
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

# Get frames and downsample frames
def fetch_depth_for_flow(pipeline):
    if not pipeline:
        return None
    
    frameset = pipeline.wait_for_frames()
    if not frameset:
        return None
    
    depth_frame = frameset.get_depth_frame()
    if not depth_frame:
        return None
    
    depth_image_original = np.asanyarray(depth_frame.get_data())
    depth_image_downsampled = cv2.resize(
        depth_image_original,
        (TARGET_WIDTH, TARGET_HEIGHT),
        interpolation=cv2.INTER_LINEAR
    )
    depth_image_normalized = cv2.normalize(
        depth_image_downsampled,
        None, 0, 255, cv2.NORM_MINMAX
    ).astype(np.uint8)

    return depth_image_normalized

def process_flow_for_synthesis(current_frame, previous_frame):
    # Optical flow (Farneback method)
    flow = cv2.calcOpticalFlowFarneback(
        previous_frame,
        current_frame,
        None, 0.5, 3, 15, 3, 5, 1.2, 0
    )

    # Get speed (magnitude) and angle of the flow
    magnitude, _ = cv2.cartToPolar(
        flow[..., 0], flow[..., 1], angleInDegrees=True
    )

    magnitude_smoothed = cv2.GaussianBlur(
        magnitude, (5, 5), 0
    )

    magnitude_clipped = np.clip(
        magnitude_smoothed, MIN_SPEED_THRESHOLD, MAX_SPEED_THRESHOLD
    )

    magnitude_normalized = cv2.normalize(
        magnitude_clipped,
        None, 0, 255, cv2.NORM_MINMAX
    ).astype(np.uint8)

    return magnitude_normalized

def divide_flow_into_cells(flow):
    flow_float = flow.astype(np.float32)
    flow_reshaped = flow_float.reshape(
        GRID_HEIGHT, GRID_SIZE,
        GRID_WIDTH, GRID_SIZE
    )

    # average of each grid
    flow_cells = flow_reshaped.mean(axis=(1, 3))

    return flow_cells

# ----------------------------------------------

try:
    # Initialize RealSense depth pipeline
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, RAW_WIDTH, RAW_HEIGHT, rs.format.z16, 30)
    profile = pipeline.start(config)

    print("RealSense pipeline started successfully.")

    previous_depth_frame = None

    while True:
        current_depth_frame = fetch_depth_for_flow(pipeline)
        
        if current_depth_frame is None:
            continue

        if previous_depth_frame is None:
            previous_depth_frame = current_depth_frame.copy()
            continue

        motion_magnitude = process_flow_for_synthesis(current_depth_frame, previous_depth_frame)

        ###### Send this via OSC ######################################################
        # Check cell indices, type, value ranges
        motion_magnitude_cells = divide_flow_into_cells(motion_magnitude)

        # Visualize the motion
        cv2.imshow('Motion Magnitude', motion_magnitude)

        # Exit the loop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        previous_depth_frame = current_depth_frame.copy()


except Exception as e:
    print(f"Error initializing RealSense pipeline: {e}")
    pipeline = None

finally:
    if 'profile' in locals() and profile:
        print("Stopping pipeline...")
        pipeline.stop()
    elif 'pipeline' in locals() and pipeline:
        try:
            pipeline.stop()
        except:
            pass

    cv2.destroyAllWindows()