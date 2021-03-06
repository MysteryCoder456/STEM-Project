"""
Client application that runs on the parent/guardians mobile device, laptop, or computer.
"""

import socket
import os
import threading
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.properties import ObjectProperty
from kivy.core.audio import SoundLoader, Sound

connected = False
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
PORT = 8000


def play_sound(sound):
    so: Sound = SoundLoader.load(sound)
    so.play()


class MainScreen(Screen):
    status_label = ObjectProperty(None)
    error_label = ObjectProperty(None)
    ip_entry = ObjectProperty(None)

    listen_thread = None
    listen = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_pre_enter(self, *args):
        try:
            s.send(b"PING")
            print("Restarting main message thread...")
            self.listen = True
            self.listen_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
            self.listen_thread.start()
        except BrokenPipeError:
            s.close()
            print("Connection closed by server!")
            self.status_label.text = "Connection closed by helper device"
            self.status_label.color = "#FF0000"
            self.status_label.bold = False
            self.listen = False
        except OSError:
            pass

    def listen_for_messages(self):
        global connected
        print("Listening for messages...")

        while self.listen:
            try:
                msg = s.recv(2048)
                msg_decoded = msg.decode("utf-8")
            except OSError:
                break
            except UnicodeDecodeError:
                pass
            except ConnectionResetError:
                s.close()
                print("Connection closed by server!")
                self.status_label.text = "Connection closed by helper device"
                self.status_label.color = "#FF0000"
                self.status_label.bold = False
                connected = False
                self.listen = False
                break

            if msg_decoded == "QUIT":
                s.close()
                print("Connection closed by server!")
                self.status_label.text = "Connection closed by helper device"
                self.status_label.color = "#FF0000"
                self.status_label.bold = False
                connected = False
                self.listen = False
                break

            elif msg_decoded == "PERSON DETECTED":
                self.status_label.text = "A person was detected in your vehicle"
                self.status_label.color = "#FF0000"
                self.status_label.bold = True
                play_sound(os.path.join("sounds", "warning_sound.mp3"))

            print("Server has sent a message:", msg_decoded)

    def camera_feed(self):
        if connected:
            self.listen = False
            s.send(b"START FOOTAGE STREAM")
            self.listen_thread.join()
            self.manager.direction = "left"
            self.manager.current = "footage"
        else:
            self.error_label.text = "Please connect to a helper device first."

    def connect_btn(self):
        global s, connected

        if len(self.ip_entry.text) < 1:
            self.ip_entry.text = "127.0.0.1"

        print(f"Attempting to establish a connection with {self.ip_entry.text}...")

        try:
            try:
                s.send(b"QUIT")
                s.close()
                print("Closing previous connection...")
            except OSError:
                print("No previous connection was found, continuing...")

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((self.ip_entry.text, PORT))

        except ConnectionRefusedError:
            print("Server has not started!")
            self.error_label.text = "This helper device has not started yet."
            return

        except socket.gaierror:
            print("Invalid IP address!")
            self.error_label.text = "The IP address you entered is invalid."
            return

        except OSError:
            print("Invalid IP address!")
            self.error_label.text = "The IP address you entered is invalid."
            return

        try:
            msg = s.recv(2048).decode("utf-8")
        except socket.timeout:
            print("Server took too long to respond!")
            self.error_label.text = "The helper device took too long to respond."
            return

        if msg == "CONNECTED":
            connected = True
            self.listen = True
            hostname = socket.gethostname().encode("UTF-8")
            s.send(hostname)
            s.settimeout(None)

            # Update GUI
            self.error_label.text = ""
            self.status_label.text = "Connected"
            self.status_label.color = "#00FF00"
            self.status_label.bold = False

            # Start message receiving thread
            print("Connection established!")
            self.listen_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
            self.listen_thread.start()


class FootageScreen(Screen):
    image_widget = ObjectProperty(None)
    listen_thread = None
    listen = False
    image_complete = False

    def on_pre_enter(self, *args):
        print("Starting image streaming thread...")
        self.listen = True
        self.listen_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        self.listen_thread.start()
        Clock.schedule_interval(self.reload_image, 0.01)

    def reload_image(self, dt):
        if self.image_complete:
            self.image_widget.reload()

    def listen_for_messages(self):
        global connected
        print("Listening for messages...")

        while self.listen:
            size_msg = s.recv(2048)

            try:
                size_decoded = size_msg.decode("utf8")
            except UnicodeDecodeError:
                continue

            if size_decoded.startswith("SIZE"):
                size = int(size_msg.split()[1])
                print(f"Received image size: {size}!")
                s.send(b"GOT SIZE")

                self.image_complete = False
                img_data = b""

                while len(img_data) < size:
                    packet = s.recv(4096)
                    if b"QUIT" in packet:
                        return
                    img_data += packet

                img_data = img_data[:size]

                with open("footage.jpg", "wb") as imagefile:
                    imagefile.write(img_data)

                self.image_complete = True
                print("Received image data!")
                s.send(b"GOT IMAGE")

            elif "QUIT" in size_decoded:
                connected = False
                return

    def go_back(self):
        print("Going back to MainScreen")
        self.listen = False
        s.send(b"STOP FOOTAGE STREAM")
        self.listen_thread.join()
        self.manager.direction = "right"
        self.manager.current = "main"


class CarSafetyApp(App):
    def build(self):
        wm = ScreenManager()
        wm.add_widget(MainScreen(name="main"))
        wm.add_widget(FootageScreen(name="footage"))
        wm.current = "main"
        return wm


if __name__ == "__main__":
    play_sound(os.path.join("sounds", "startup_sound.mp3"))

    try:
        CarSafetyApp().run()
    except KeyboardInterrupt:
        print("Keyboard Interrupt...")
    finally:
        try:
            s.send(b"QUIT")

        except BrokenPipeError:
            pass

        except OSError:
            pass

        s.close()
        if os.path.exists("footage.jpg"):
            os.remove("footage.jpg")
