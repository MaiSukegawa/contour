import realsense as rs
import osc_server as osc
import cv2

def main():
    pipeline = None
    profile = None

    previous_depth_frame = None
    current_depth_frame = None

    try:
        # Initialize RealSense depth pipeline
        pipeline, profile = rs.init_realsense_pipeline()

        while True:
            current_depth_frame = rs.fetch_depth_for_flow(pipeline)
            # cv2.imshow('Raw Image', current_depth_frame)
            
            if current_depth_frame is None:
                continue

            if previous_depth_frame is None:
                previous_depth_frame = current_depth_frame.copy()
                continue

            motion_magnitude = rs.process_flow(current_depth_frame, previous_depth_frame)

            motion_magnitude_cells = rs.divide_flow_into_cells(motion_magnitude)
            motion_magnitude_cells_flattened = motion_magnitude_cells.flatten()
            osc.send_motion_data(motion_magnitude_cells_flattened.tolist())

            # Visualize the motion
            # cv2.imshow('Motion Magnitude', motion_magnitude)

            # Exit the loop
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            previous_depth_frame = current_depth_frame.copy()


    except Exception as e:
        print(f"Error initializing RealSense pipeline or during loop: {e}")
        pipeline = None
        profile = None

    finally:
        if profile and pipeline:
            print("Stopping pipeline...")
            pipeline.stop()

        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()