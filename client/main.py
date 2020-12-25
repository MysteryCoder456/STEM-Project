from logging import fatal
import socket
import threading
import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
PORT = 8000
APPLICATION_STOPPED = False


def check_for_message():
    print("Listening for messsages...")

    while True:
        if APPLICATION_STOPPED:
            return

        msg = s.recv(2048).decode("utf-8")
        print(msg)


class MainGrid(Widget):
    ip = ObjectProperty(None)

    def btn(self):
        print(f"Attempting to establish a connection with {self.ip.text}...")

        try:
            s.connect((self.ip.text, PORT))
        except ConnectionRefusedError:
            print("Server has not started!")
            return
        except socket.gaierror:
            print("Invalid IP address!")
            return
        except OSError:
            print("Invalid IP address!")
            return

        msg = s.recv(2048).decode("utf-8")

        if msg == "CONNECTED":
            self.ip.text = ""
            print("Connection established!")
            msg_thread = threading.Thread(target=check_for_message)
            msg_thread.start()


class STEMApp(App):
    def build(self):
        return MainGrid()


if __name__ == "__main__":
    # TODO: Program a way to notify server that client has stopped
    STEMApp().run()
    APPLICATION_STOPPED = True
    s.close()
