from flask import Flask, render_template, Response
import cv2
import time
import random
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
socketio = SocketIO(app)

base_dir = os.path.abspath(os.path.dirname(__file__))

face_cascade_path = os.path.join(base_dir, "haarcascade_frontalface_default.xml")
eye_cascade_path = os.path.join(base_dir, "haarcascade_eye.xml")

face_cascade = cv2.CascadeClassifier(face_cascade_path)
eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

detection_active = True
status = "Waiting..."
stress_level = 0
detection_time = None
remaining_time = 5 

def detect_stress(frame):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray_frame,
        scaleFactor=1.1,
        minNeighbors=5,  
        minSize=(50, 50) 
    )

    stress_detected = False
    stress_level = 0

    for (x, y, w, h) in faces:
        roi_gray = gray_frame[y:y+h, x:x+w]

        eyes = eye_cascade.detectMultiScale(
            roi_gray,
            scaleFactor=1.1,  
            minNeighbors=5, 
            minSize=(20, 20),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        eye_pair = []
        for (ex, ey, ew, eh) in eyes:
            if ew > 0.25 * w and eh > 0.1 * h:
                eye_pair.append((ex, ey, ew, eh))
        if len(eye_pair) == 2:
            stress_detected = False
        else:
            stress_detected = True
            stress_level = random.randint(0, 100) 

        if stress_detected:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(frame, f"Stressed {stress_level}%", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    return frame, stress_detected, stress_level

def generate_frames():
    global detection_active, detection_time, status, stress_level, remaining_time

    detection_active = True
    status = "Waiting..."
    stress_level = 0
    detection_time = None
    remaining_time = 5

    while True:
        success, frame = camera.read()
        if not success:
            break 

        if detection_active:
            frame, stress_detected, detected_level = detect_stress(frame)

            if detection_time is None:
                detection_time = time.time()

            elapsed_time = time.time() - detection_time
            remaining_time = max(0, 5 - int(elapsed_time))

            if elapsed_time >= 5:
                if stress_detected:
                    status = f"Stressed detected with level {detected_level}%"
                    stress_level = detected_level
                else:
                    status = "No stress detected"
                    stress_level = 0

                socketio.emit('status_update', {'status': status, 'level': stress_level, 'timer': remaining_time})

                detection_active = False
                camera.release()

        frame = cv2.resize(frame, (800, 600))

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    global detection_active, detection_time, status, stress_level, remaining_time

    detection_active = True
    status = "Waiting..."
    stress_level = 0
    detection_time = None
    remaining_time = 5

    return render_template('index.html', status=status, level=stress_level)

@app.route('/video_feed')
def video_feed():
    global camera
    camera = cv2.VideoCapture(0) 
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('connect')
def handle_connect():
    emit('status_update', {'status': status, 'level': stress_level, 'timer': remaining_time})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
