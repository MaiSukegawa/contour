import pyrealsense2 as rs
import numpy as np
import cv2

RAW_WIDTH = 640
RAW_HEIGHT = 480

TARGET_WIDTH = RAW_WIDTH // 8
TARGET_HEIGHT = RAW_HEIGHT // 8

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

# Compare current frame to previous frame to detect motion

# def detect_motion(current_frame, previous_frame):





# ----------------------------------------------

try:
    # Initialize RealSense depth pipeline
    pipeline = rs.pipeline()
    config = rs.config()

    config.enable_stream(rs.stream.depth, RAW_WIDTH, RAW_HEIGHT, rs.format.z16, 30)

    profile = pipeline.start(config)

    print("RealSense pipeline started successfully.")

    # (LOOP), ('depth' is temporal name)
    depth = fetch_depth_for_flow(pipeline)
    print("Fetched depth frame shape:", depth.shape if depth is not None else "No depth frame")

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


