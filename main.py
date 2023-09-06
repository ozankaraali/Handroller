import argparse
import cv2
import mediapipe as mp
import pyautogui
import time


# Constants
screen_width, screen_height = pyautogui.size()
margin = 150

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)  # Increase thresholds for performance
mp_drawing = mp.solutions.drawing_utils

click_threshold = 0.5
cooldown_period = 0.7

last_okay_time, last_yoga_time, last_click_time = 0, 0, 0
gesture_states = {'okay_sign': False, 'yoga_sign': False}


def get_gesture_landmark_distances(landmarks):
    """Calculate distances between thumb and other fingertips for gesture detection."""
    distance_okay = abs(
        landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].x - landmarks[mp_hands.HandLandmark.THUMB_TIP].x) + abs(
        landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].y - landmarks[mp_hands.HandLandmark.THUMB_TIP].y)
    distance_yoga = abs(
        landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].x - landmarks[mp_hands.HandLandmark.THUMB_TIP].x) + abs(
        landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y - landmarks[mp_hands.HandLandmark.THUMB_TIP].y)
    return distance_okay, distance_yoga


def process_gesture(landmarks):
    """Detect and process gesture."""
    distance_okay, distance_yoga = get_gesture_landmark_distances(landmarks)
    threshold_okay, threshold_yoga = 0.05, 0.05
    current_time = time.time()

    # Okay Sign
    if distance_okay < threshold_okay:
        return handle_okay_sign_gesture(current_time)

    # Yoga Sign
    if distance_yoga < threshold_yoga:
        return handle_yoga_sign_gesture(current_time)

    return None


def handle_okay_sign_gesture(current_time):
    """Handle logic specific to okay sign gesture."""
    global last_okay_time, last_click_time, gesture_states
    if current_time - last_okay_time < click_threshold:
        last_okay_time = 0
        last_click_time = current_time
        pyautogui.doubleClick()
        return 'Double Left Click'
    elif current_time - last_click_time > cooldown_period:
        last_okay_time = current_time
        last_click_time = current_time
        pyautogui.click()
        return 'Left Click'
    return None


def handle_yoga_sign_gesture(current_time):
    """Handle logic specific to yoga sign gesture."""
    global last_yoga_time, last_click_time, gesture_states
    if current_time - last_yoga_time < click_threshold:
        last_yoga_time = 0
        last_click_time = current_time
        pyautogui.doubleClick(button='right')
        return 'Double Right Click'
    elif current_time - last_click_time > cooldown_period:
        last_yoga_time = current_time
        last_click_time = current_time
        pyautogui.click(button='right')
        return 'Right Click'
    return None


def map_to_screen(x, y, frame_width, frame_height):
    """Map the camera's resolution to the computer display resolution with added margin."""
    mapped_x = (x - margin) / (frame_width - 2 * margin) * screen_width
    mapped_y = (y - margin) / (frame_height - 2 * margin) * screen_height
    return int(mapped_x), int(mapped_y)


def handle_multiple_hands(landmarks_list, handedness_list):
    """Returns the right hand's landmarks if present, otherwise the first hand's landmarks."""
    for index, handedness in enumerate(handedness_list):
        if handedness.classification[0].label == 'Right':
            return landmarks_list[index]
    return landmarks_list[0]


# Add argparse for command-line toggling
def parse_arguments():
    parser = argparse.ArgumentParser(description="Hand Gesture Mouse Control")
    parser.add_argument('--display', action='store_true', help="Display the webcam feed with hand landmarks.")
    return parser.parse_args()


def main():
    args = parse_arguments()

    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        frame_height, frame_width, _ = frame.shape
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(image_rgb)

        # Process hands
        if results.multi_hand_landmarks and results.multi_handedness:
            landmarks = handle_multiple_hands(results.multi_hand_landmarks, results.multi_handedness)
            gesture = process_gesture(landmarks.landmark)
            index_mcp_x = int(landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].x * frame_width)
            index_mcp_y = int(landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].y * frame_height)
            mapped_x, mapped_y = map_to_screen(index_mcp_x, index_mcp_y, frame_width, frame_height)
            pyautogui.moveTo(mapped_x, mapped_y)
            # pyautogui.moveTo(mapped_x, mapped_y, duration=0.1)  # Add duration for smoother movement
            mp_drawing.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)
            if gesture:
                cv2.putText(frame, gesture, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, f"x:{index_mcp_x}", (frame_width - 100, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0),
                        1)
            cv2.putText(frame, f"y:{index_mcp_y}", (frame_width - 100, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0),
                        1)

        # If display is turned on via command line, bypassing it to debug release
        if True:
            # Resize the frame for faster display
            display_scale = 0.5  # Adjust this value as needed
            frame = cv2.resize(frame, (int(frame_width * display_scale), int(frame_height * display_scale)))

            cv2.imshow('Handroller', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
