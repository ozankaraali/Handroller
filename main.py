import argparse
import cv2
import mediapipe as mp
import pyautogui
import time

# lag protection
pyautogui.PAUSE = 0
pyautogui.MINIMUM_SLEEP = 0

# Constants
screen_width, screen_height = pyautogui.size()
margin = 150

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

cooldown_period = 0.7
last_release_time, last_click_time = 0, 0


def get_gesture_landmark_distances(landmarks):
    """Calculate distances between thumb and other fingertips for gesture detection."""
    distance_index = abs(
        landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].x - landmarks[mp_hands.HandLandmark.THUMB_TIP].x) + abs(
        landmarks[mp_hands.HandLandmark.INDEX_FINGER_TIP].y - landmarks[mp_hands.HandLandmark.THUMB_TIP].y)
    distance_middle = abs(
        landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].x - landmarks[mp_hands.HandLandmark.THUMB_TIP].x) + abs(
        landmarks[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y - landmarks[mp_hands.HandLandmark.THUMB_TIP].y)
    distance_ring = abs(
        landmarks[mp_hands.HandLandmark.RING_FINGER_TIP].x - landmarks[mp_hands.HandLandmark.THUMB_TIP].x) + abs(
        landmarks[mp_hands.HandLandmark.RING_FINGER_TIP].y - landmarks[mp_hands.HandLandmark.THUMB_TIP].y)
    return distance_index, distance_middle, distance_ring


def process_gesture(landmarks):
    """Detect and process gesture."""
    global last_release_time
    distance_index, distance_middle, distance_ring = get_gesture_landmark_distances(landmarks)
    threshold_index, threshold_middle, threshold_ring = 0.06, 0.06, 0.06
    current_time = time.time()

    # Okay Sign
    if distance_index < threshold_index:
        return handle_index_gesture(current_time)

    # Yoga Sign
    if distance_middle < threshold_middle:
        return handle_middle_gesture(current_time)

    if distance_ring < threshold_ring:
        return handle_ring_gesture(current_time)

    last_release_time = current_time
    return None


def handle_index_gesture(current_time):
    """Handle logic specific to okay sign gesture."""
    global last_release_time
    pyautogui.click()
    if current_time - last_release_time > cooldown_period:
        return 'Left Click Hold'
    return 'Left Click'


def handle_middle_gesture(current_time):
    """Handle logic specific to yoga sign gesture."""
    global last_release_time
    pyautogui.click(button='right')
    if current_time - last_release_time > cooldown_period:
        return 'Right Click Hold'
    return 'Right Click'


def handle_ring_gesture(current_time):
    """Handle logic specific to yoga sign gesture."""
    global last_click_time
    if current_time - last_click_time > cooldown_period:
        last_click_time = current_time
        pyautogui.doubleClick()
    return 'Double Click'


def map_to_screen(x, y, frame_width, frame_height):
    """Map the camera's resolution to the computer display resolution with added margin."""
    mapped_x = (x - margin) / (frame_width - 2 * margin) * screen_width
    mapped_y = (y - margin) / (frame_height - 2 * margin) * screen_height
    return int(mapped_x), int(mapped_y)


def handle_multiple_hands(landmarks_list, handedness_list, left=False):
    """Returns the right hand's landmarks if present, otherwise the first hand's landmarks."""
    if left:
        for index, handedness in enumerate(handedness_list):
            if handedness.classification[0].label == 'Left':
                return landmarks_list[index]
    for index, handedness in enumerate(handedness_list):
        if handedness.classification[0].label == 'Right':
            return landmarks_list[index]
    return landmarks_list[0]


# Add argparse for command-line toggling
def parse_arguments():
    parser = argparse.ArgumentParser(description="Hand Gesture Mouse Control")
    parser.add_argument('--nodisplay', action='store_true', help="Display the webcam feed with hand landmarks.")
    parser.add_argument('--lefthanded', action='store_true', help="Only track the left hand.")
    return parser.parse_args()


def main():
    args = parse_arguments()
    frame_width, frame_height = 640, 480
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
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
            landmarks = handle_multiple_hands(results.multi_hand_landmarks, results.multi_handedness, args.lefthanded)
            gesture = process_gesture(landmarks.landmark)
            index_mcp_x = int(landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].x * frame_width)
            index_mcp_y = int(landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].y * frame_height)
            mapped_x, mapped_y = map_to_screen(index_mcp_x, index_mcp_y, frame_width, frame_height)
            if gesture == 'Left Click Hold':
                pyautogui.dragTo(mapped_x, mapped_y, button='left')
            elif gesture == 'Right Click Hold':
                pyautogui.dragTo(mapped_x, mapped_y, button='right')
            # elif gesture == 'Double Click':
            #   continue
            else:
                pyautogui.moveTo(mapped_x, mapped_y)
            mp_drawing.draw_landmarks(frame, landmarks, mp_hands.HAND_CONNECTIONS)
            if gesture:
                cv2.putText(frame, gesture, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, f"x:{index_mcp_x}", (frame_width - 100, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0),
                        1)
            cv2.putText(frame, f"y:{index_mcp_y}", (frame_width - 100, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0),
                        1)

        if not args.nodisplay:
            cv2.imshow('Handroller', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
