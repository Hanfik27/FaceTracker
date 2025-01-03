import os
import PyInstaller.__main__

# Konfigurasi file dan folder
script_name = "app.py"
output_name = "Face and Stress Detection"
templates_folder = "templates"
haar_eye = "haarcascade_eye.xml"
haar_face = "haarcascade_frontalface_default.xml"

# Jalankan PyInstaller dengan konfigurasi
PyInstaller.__main__.run([
    script_name,
    "--onefile",
    "--clean",
    "--name", output_name,
    f"--add-data={templates_folder};templates",
    f"--add-data={haar_eye};.",
    f"--add-data={haar_face};.",
    "--hidden-import=cv2",
    "--hidden-import=flask_socketio",
    "--hidden-import=engineio.async_drivers.threading",
    "--hidden-import=.venv",
])
