import realsense as rs
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
            
            if current_depth_frame is None:
                continue

            if previous_depth_frame is None:
                previous_depth_frame = current_depth_frame.copy()
                continue

            motion_magnitude = rs.process_flow_for_visualization(current_depth_frame, previous_depth_frame)

            ###### Send this via OSC ######################################################
            # Check cell indices, type, value ranges
            motion_magnitude_cells = rs.divide_flow_into_cells(motion_magnitude)

            # Visualize the motion
            cv2.imshow('Motion Magnitude', motion_magnitude)

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