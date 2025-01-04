import os
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
import webbrowser

class MyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        label = Button(text="Start Flask Server")
        button = Button(text="Open Flask App")

        def start_flask_server(instance):
            os.system("python3 app.py")  # Jalankan Flask server

        def open_browser(instance):
            webbrowser.open("http://127.0.0.1:5000")  # Buka di browser

        label.bind(on_press=start_flask_server)
        button.bind(on_press=open_browser)

        layout.add_widget(label)
        layout.add_widget(button)
        return layout

if __name__ == '__main__':
    MyApp().run()
