"""
Client application that runs on the parent/guardians mobile device, laptop, or computer.
"""

import socket
import threading
import pickle
import struct
from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.properties import ObjectProperty
import playsound
import gtts
import cv2

connected = False
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
PORT = 8000


def speak(text):
    tts = gtts.gTTS(text)
    tts.save("tts.mp3")
    playsound.playsound("tts.mp3")


class MainScreen(Screen):
    status_label = ObjectProperty(None)
    error_label = ObjectProperty(None)
    ip_entry = ObjectProperty(None)
    listen_thread = None
    listen = False

    def on_pre_enter(self, *args):
        if connected:
            print("Restarting message thread...")
            self.listen_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
            self.listen_thread.start()

    def listen_for_messages(self):
        global connected
        print("Listening for messsages...")

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

                speak_thread = threading.Thread(target=speak, args=("Warning! A person was detected in your vehicle. I repeat, a person was detected in your vehicle.",),
                                                daemon=True)
                speak_thread.start()

            print("Server has sent a message:", msg_decoded)

    def camera_feed(self):
        if connected:
            s.send(b"START FOOTAGE STREAM")
            self.listen = False
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

            # Start message recieving thread
            print("Connection established!")
            self.listen_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
            self.listen_thread.start()


class FootageScreen(Screen):
    image_widget = ObjectProperty(None)
    listen_thread = None
    listen = False

    def on_pre_enter(self, *args):
        print("Starting image streaming thread...")
        self.listen = True
        self.listen_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        self.listen_thread.start()

    def listen_for_messages(self):
        global connected
        print("Listening for messsages...")

        payload_size = struct.calcsize("Q")

        while self.listen:
            size_msg = s.recv(2048).decode("utf8")

            if not size_msg:
                self.go_back()
                break

            if size_msg.startswith("SIZE"):
                size = int(size_msg.split()[1])
                print("Received image size!")
                s.send(b"GOT SIZE")

                img_data = s.recv(4194304)  # 4 Megabytes

                with open("footage.jpg", "wb") as imagefile:
                    imagefile.write(img_data)

                s.send(b"GOT IMAGE")

            e = cv2.imread("cache.jpg")
            cv2.imshow(e, "pog")

            self.image_widget.reload()

    def go_back(self):
        print("Going back to MainScreen")
        s.send(b"STOP FOOTAGE STREAM")
        self.listen = False
        self.listen_thread.join()
        self.manager.direction = "left"
        self.manager.current = "main"


class CarSafetyApp(App):
    def build(self):
        wm = ScreenManager()
        wm.add_widget(MainScreen(name="main"))
        wm.add_widget(FootageScreen(name="footage"))
        wm.current = "main"
        return wm


if __name__ == "__main__":
    sp_thread = threading.Thread(target=speak, args=("Please turn up your volume, you will recieve alerts like this...",), daemon=True)
    sp_thread.start()

    try:
        CarSafetyApp().run()
    except KeyboardInterrupt:
        print("Keyboard Interrupt...")
    finally:
        if connected:
            s.send(b"QUIT")
        s.close()
