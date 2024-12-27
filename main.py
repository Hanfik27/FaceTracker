import cv2
import mediapipe as mp
import numpy as np
from flask import Flask, render_template, Response

app = Flask(__name__)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

def detect_hand_gesture(finger_positions):
    gestures = "Unknown Gesture"

    if finger_positions:
        thumb_tip = finger_positions["Thumb"]["tip"]
        thumb_base = finger_positions["Thumb"]["base"]
        if thumb_tip[1] < thumb_base[1]:
            gestures = "Thumbs"

        finger_names = ["Index", "Middle", "Ring", "Pinky"]
        for finger in finger_names:
            finger_tip = finger_positions[finger]["tip"]
            finger_base = finger_positions[finger]["base"]
            if finger_tip[1] < finger_base[1]:
                gestures = f"{finger} Finger"

        fingers_up = sum(1 for pos in finger_positions.values() if pos["tip"][1] < pos["base"][1])
        if fingers_up == 5:
            gestures = "Open Hand"

        fingers_down = sum(1 for pos in finger_positions.values() if pos["tip"][1] > pos["base"][1])
        if fingers_down == 5:
            gestures = "Closed Fist"

    return gestures

def generate():
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (1200, 720))

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results_hands = hands.process(rgb_frame)

            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray_frame, 1.3, 5)

            for (x, y, w, h) in faces:
                face_roi = frame[y:y+h, x:x+w]

                face_area = w * h
                if face_area > 40000:
                    age = "Adult"
                elif face_area > 15000:
                    age = "Teenager"
                else:
                    age = "Child"

                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                cv2.putText(frame, f"Age: {age}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

            if results_hands.multi_hand_landmarks:
                for hand_landmarks in results_hands.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    finger_positions = track_finger_positions(hand_landmarks)

                    gesture = detect_hand_gesture(finger_positions)
                    cv2.putText(frame, f"Gesture: {gesture}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            frame = jpeg.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    cap.release()

def track_finger_positions(hand_landmarks):
    finger_positions = {}
    if hand_landmarks:
        fingers = {
            "Thumb": [mp_hands.HandLandmark.THUMB_TIP, mp_hands.HandLandmark.THUMB_IP],
            "Index": [mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.INDEX_FINGER_DIP],
            "Middle": [mp_hands.HandLandmark.MIDDLE_FINGER_TIP, mp_hands.HandLandmark.MIDDLE_FINGER_DIP],
            "Ring": [mp_hands.HandLandmark.RING_FINGER_TIP, mp_hands.HandLandmark.RING_FINGER_DIP],
            "Pinky": [mp_hands.HandLandmark.PINKY_TIP, mp_hands.HandLandmark.PINKY_DIP]
        }

        # Ambil posisi jari berdasarkan landmark yang sudah didefinisikan
        for finger_name, landmarks in fingers.items():
            tip = hand_landmarks.landmark[landmarks[0]]
            base = hand_landmarks.landmark[landmarks[1]]

            # Menyimpan posisi tip dan pangkal jari dalam dictionary
            finger_positions[finger_name] = {
                "tip": (tip.x, tip.y),
                "base": (base.x, base.y)
            }

    return finger_positions

# Route untuk video streaming
@app.route('/video_feed')
def video_feed():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Home route
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
