from flask import Flask, render_template, Response
import cv2
import time
import random
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# Load Haarcascade untuk deteksi wajah dan mata
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

# Initialize webcam
camera = cv2.VideoCapture(0)

# Variabel global untuk status deteksi
detection_active = True
status = "Waiting..."
stress_level = 0
detection_time = None
remaining_time = 5  # Deteksi selama 5 detik

# Fungsi untuk mendeteksi stres
def detect_stress(frame):
    """Mendeteksi stres berdasarkan keadaan mata."""
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.3, minNeighbors=5)

    stress_detected = False
    stress_level = 0

    # Selalu tampilkan kotak pada wajah yang terdeteksi
    for (x, y, w, h) in faces:
        roi_gray = gray_frame[y:y+h, x:x+w]
        roi_color = frame[y:y+h, x:x+w]

        # Deteksi mata
        eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=10)

        # Deteksi stres jika mata tidak terdeteksi dengan jelas
        if len(eyes) < 2:
            stress_detected = True
            stress_level = random.randint(30, 70)  # Stress level acak antara 30% hingga 70%
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)  # Kotak wajah
            cv2.putText(frame, f"Stressed {stress_level}%", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        else:
            # Jika mata terdeteksi dengan baik, tetap tampilkan kotak wajah tanpa status stres
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)  # Kotak wajah normal

    return frame, stress_detected, stress_level

# Fungsi untuk menghasilkan frame video
def generate_frames():
    global detection_active, detection_time, status, stress_level, remaining_time

    # Reset variabel deteksi pada setiap permintaan
    detection_active = True
    status = "Waiting..."
    stress_level = 0
    detection_time = None
    remaining_time = 5  # Mulai timer kembali dari 5 detik

    while True:
        success, frame = camera.read()
        if not success:
            break  # Jika kamera tidak dapat mengambil gambar, hentikan

        if detection_active:
            # Proses deteksi stres
            frame, stress_detected, detected_level = detect_stress(frame)

            # Jika deteksi baru dimulai, set timer
            if detection_time is None:
                detection_time = time.time()

            # Hitung waktu yang tersisa
            elapsed_time = time.time() - detection_time
            remaining_time = max(0, 5 - int(elapsed_time))

            # Mengirim status dan timer ke klien setiap detik
            if elapsed_time >= 5:
                # Setelah 5 detik, berhenti deteksi dan kirim status ke klien
                if stress_detected:
                    status = f"Stressed detected with level {detected_level}%"
                    stress_level = detected_level
                else:
                    status = "No stress detected"
                    stress_level = 0

                # Mengirim status ke klien melalui SocketIO
                socketio.emit('status_update', {'status': status, 'level': stress_level, 'timer': remaining_time})

                # Hentikan deteksi dan keluarkan kamera setelah 5 detik
                detection_active = False
                camera.release()

        # Resize frame ke ukuran 800x600
        frame = cv2.resize(frame, (800, 600))

        # Encode frame untuk stream video
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    global detection_active, detection_time, status, stress_level, remaining_time

    # Reset variabel deteksi
    detection_active = True
    status = "Waiting..."
    stress_level = 0
    detection_time = None
    remaining_time = 5

    return render_template('index.html', status=status, level=stress_level)


@app.route('/video_feed')
def video_feed():
    global camera
    camera = cv2.VideoCapture(0)  # Pastikan kamera dibuka kembali saat streaming
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Event listener untuk koneksi socket
@socketio.on('connect')
def handle_connect():
    emit('status_update', {'status': status, 'level': stress_level, 'timer': remaining_time})

if __name__ == "__main__":
    socketio.run(app, debug=True)
