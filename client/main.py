import socket
import threading
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
PORT = 8000


class MainGrid(Widget):
    status_label = ObjectProperty(None)
    error_label = ObjectProperty(None)
    ip_entry = ObjectProperty(None)

    def listen_for_messages(self):
        print("Listening for messsages...")

        while True:
            try:
                msg = s.recv(2048).decode("utf-8")
            except OSError:
                return

            if msg == "QUIT":
                s.close()
                self.status_label.text = "Connection closed by helper device"
                self.status_label.color = "#FF0000"
                return

            print(msg)

    def connect_btn(self):
        global s

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
            s.settimeout(None)

            # Update GUI
            self.ip_entry.text = ""
            self.error_label.text = ""
            self.status_label.text = "Connected"
            self.status_label.color = "#00FF00"

            # Start message recieving thread
            print("Connection established!")
            listen_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
            listen_thread.start()


class STEMApp(App):
    def build(self):
        return MainGrid()


if __name__ == "__main__":
    STEMApp().run()

    try:
        s.send(b"QUIT")
        s.close()
    except OSError:
        pass
