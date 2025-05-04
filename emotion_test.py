import cv2
import time
from deepface import DeepFace
import numpy as np

def test_emotion_detection():
    print("Starting emotion detection test...")
    print("Press 'q' to quit")
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    last_detection_time = 0
    detection_interval = 1  # Detect emotion every 1 second
    
    while True:
        # Capture frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image")
            break
        
        # Create a copy for display
        display_frame = frame.copy()
        
        # Detect emotion at intervals to avoid overloading CPU
        current_time = time.time()
        if current_time - last_detection_time > detection_interval:
            try:
                # Analyze the frame
                result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                if isinstance(result, list):
                    result = result[0]
                
                # Get dominant emotion
                emotion = result.get('dominant_emotion', 'unknown')
                emotion_scores = result.get('emotion', {})
                
                # Format emotion scores for display
                emotion_text = f"Dominant: {emotion}"
                scores_text = " | ".join([f"{e}: {score:.1f}%" for e, score in emotion_scores.items()])
                
                # Display the results
                cv2.putText(display_frame, emotion_text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(display_frame, scores_text, (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                
                print(f"Detected emotion: {emotion}")
                last_detection_time = current_time
                
            except Exception as e:
                print(f"Error in emotion detection: {str(e)}")
        
        # Display the frame
        cv2.imshow('Emotion Detection Test', display_frame)
        
        # Check for exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    print("Test completed")

if __name__ == "__main__":
    test_emotion_detection()