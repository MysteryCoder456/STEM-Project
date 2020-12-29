"""
Server script that runs on the helper device. Device must have a either a camera or a mic, or both.
Run this script from inside the server folder.
"""

import sys
import socket
import threading
import urllib.request
import cv2

ADDR = '127.0.0.1'
PORT = 8000
CONNECTED = False

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((ADDR, PORT))
s.listen(2)

CLIENT = None


def new_client():
    global CONNECTED

    print("Listening for connections at:")
    print("IP:", urllib.request.urlopen('https://ident.me').read().decode('utf8'), "Port:", PORT)

    # Wait for a new connection
    clientsocket, clientaddr = s.accept()

    clientsocket.send(b"CONNECTED")
    print(f"Client from {clientaddr} has established a connection!")
    CONNECTED = True

    return clientsocket


def listen_for_messages():
    global CLIENT, CONNECTED

    while True:
        msg = CLIENT.recv(2048).decode("utf-8")

        if msg == "QUIT":
            CONNECTED = False
            print("Connection closed by client!")
            CLIENT = new_client()


def _exit(video_capture):
    video_capture.release()

    try:
        print("Exiting...")
        CLIENT.send(b"QUIT")
        s.close()
    except AttributeError:
        print()

    sys.exit()


def main():
    global CLIENT

    # Initialize OpenCV stuff
    cap = cv2.VideoCapture(0)
    cascade_classifier = cv2.CascadeClassifier("haar_cascade_face.xml")

    CLIENT = new_client()

    try:
        listen_thread = threading.Thread(target=listen_for_messages, daemon=True)
        listen_thread.start()

        # Broadcasting messages
        while True:
            if CONNECTED:
                cam_available, img = cap.read()

                # Camera operation
                if cam_available:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    faces = cascade_classifier.detectMultiScale(gray, minSize=(50, 50), minNeighbors=4)

                    for (pos_x, pos_y, width, height) in faces:
                        cv2.rectangle(img, (pos_x, pos_y), (pos_x + width, pos_y + height), (255, 0, 0), 3)

                    cv2.imshow("Camera Output", img)

                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        _exit(cap)

    except KeyboardInterrupt:
        _exit(cap)


if __name__ == "__main__":
    main()
