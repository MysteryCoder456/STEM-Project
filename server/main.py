"""
Server script that runs on the helper device. Device must have a either a camera or a mic, or both.
Run this script from inside the server folder.
"""

import sys
import socket
import threading
import urllib.request
import cv2

CAMERA_PREVIEW = ("--camera-preview" in sys.argv)
SOUND_PREVIEW = ("--sound-preview" in sys.argv)

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
    print(f"\nClient from {clientaddr} has established a connection!\n")
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
    print("Exiting...")
    video_capture.release()

    if CONNECTED:
        CLIENT.send(b"QUIT")
        s.close()


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
                    faces = cascade_classifier.detectMultiScale(gray, scaleFactor=1.3, minSize=(100, 100), minNeighbors=4)

                    if len(faces) > 0:
                        print(f"{len(faces)} faces were detected!")
                        CLIENT.send(b"PERSON DETECTED")

                    if CAMERA_PREVIEW:
                        for (pos_x, pos_y, width, height) in faces:
                            cv2.rectangle(img, (pos_x, pos_y), (pos_x + width, pos_y + height), (255, 0, 0), 3)

                        cv2.imshow("Camera Output", img)

                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        _exit(cap)
                        return

    except KeyboardInterrupt:
        _exit(cap)
        return

    except SystemExit:
        _exit(cap)
        return


if __name__ == "__main__":
    main()
