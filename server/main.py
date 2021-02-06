"""
Server script that runs on the helper device. Device must have a either a camera or a mic, or both.
Run this script from inside the server folder.
"""

import os
import sys
import time
import socket
import threading
import pickle
import struct
import urllib.request
import cv2
import pyaudio
import numpy as np
import face_recognition
from twilio.rest import Client

# Options
CAMERA_PREVIEW = ("--camera-preview" in sys.argv)
SOUND_PREVIEW = ("--sound-preview" in sys.argv)
DISABLE_MIC = ("--disable-mic" in sys.argv)

SOUND_THRESHOLD = 160

# Audio Stuff
CHUNK = 1024 * 4
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Networking stuff
ADDR = '0.0.0.0'
PORT = 8000
CONNECTED = False

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((ADDR, PORT))
s.listen(2)

CLIENT = None
CLIENT_DEVICE_NAME = None
sending_message = False

# Facial Recognition stuff
known_guard_faces = []
known_guard_names = []

CALLER_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
client = Client()
stream_image_data = False
encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]


def new_client():
    global CONNECTED, CLIENT_DEVICE_NAME

    print("Listening for connections at:")
    print("IP:", urllib.request.urlopen('https://ident.me').read().decode('utf8'), "Port:", PORT)

    # Wait for a new connection
    clientsocket, clientaddr = s.accept()

    clientsocket.send(b"CONNECTED")
    CLIENT_DEVICE_NAME = clientsocket.recv(2048).decode("UTF-8")
    print(f"\nClient from {clientaddr} has established a connection!\nClient device name: {CLIENT_DEVICE_NAME}\n")
    CONNECTED = True

    return clientsocket


def listen_for_messages():
    global CLIENT, CONNECTED, stream_image_data

    while True:
        msg = CLIENT.recv(2048).decode("utf-8")

        if msg == "QUIT":
            CONNECTED = False
            print("Connection closed by client!")
            CLIENT = new_client()

        elif msg == "START FOOTAGE STREAM":
            stream_image_data = True

        elif msg == "STOP FOOTAGE STREAM":
            stream_image_data = False


def person_detected():
    global sending_message

    sending_message = True
    CLIENT.send(b"PERSON DETECTED")
    time.sleep(20)
    sending_message = False


def call_police():
    with open("emergency_numbers.txt", "r") as emergency_file:
        numbers = emergency_file.readlines()

        for number in numbers:
            if not number.startswith("#"):
                print("Dialing " + number)
                client.calls.create(to=number, from_=CALLER_NUMBER, url="http://static.fullstackpython.com/phone-calls-python.xml", method="GET")

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

    # Initialize audio stuff
    if not DISABLE_MIC:
        p = pyaudio.PyAudio()
        stream = p.open(
            rate=RATE,
            channels=CHANNELS,
            format=FORMAT,
            input=True,
            output=True,
            frames_per_buffer=CHUNK
        )

    # Initialize face recog stuff
    for face_name in os.listdir("known_guardians"):
        if face_name != ".DS_Store":
            for filename in os.listdir(f"known_guardians/{face_name}"):
                if filename != ".DS_Store":
                    image = face_recognition.load_image_file(f"known_guardians/{face_name}/{filename}")
                    encoding = face_recognition.face_encodings(image)[0]
                    known_guard_faces.append(encoding)
                    known_guard_names.append(face_name)

    CLIENT = new_client()

    try:
        listen_thread = threading.Thread(target=listen_for_messages, daemon=True)
        listen_thread.start()

        # Broadcasting messages
        while True:
            if CONNECTED:
                # Camera operation
                people_detected = False
                guardian_detected = False

                cam_available, img = cap.read()

                if stream_image_data:
                    _, frame = cv2.imencode('.jpg', img, encode_param)
                    data = pickle.dumps(frame, 0)
                    print(len(data))
                    CLIENT.send(data)

                if cam_available:
                    face_locations = face_recognition.face_locations(img)
                    face_encodings = face_recognition.face_encodings(img, face_locations)
                    for f_enc, f_loc in zip(face_encodings, face_locations):
                        results = face_recognition.compare_faces(known_guard_faces, f_enc, tolerance=0.7)

                        if not guardian_detected:
                            guardian_detected = (True in results)

                        people_detected = True

                        if CAMERA_PREVIEW:
                            top_left = (f_loc[3], f_loc[0])
                            bottom_right = (f_loc[1], f_loc[2])
                            if True in results:
                                color = (0, 255, 0)
                            else:
                                color = (255, 0, 0)
                            cv2.rectangle(img, top_left, bottom_right, color, 3)

                    if CAMERA_PREVIEW:
                        cv2.imshow("Camera Output", img)

                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        _exit(cap)
                        return

                # Sound operation
                if not DISABLE_MIC:
                    sound_data = struct.unpack(f"{2 * CHUNK}B", stream.read(CHUNK))
                    volume = np.linalg.norm(sound_data)
                    print(volume)

                    if volume > SOUND_THRESHOLD:
                        people_detected = True

                if people_detected and not guardian_detected and not sending_message:
                    call_police()
                    pd_thread = threading.Thread(target=person_detected, daemon=True)
                    pd_thread.start()

    except KeyboardInterrupt:
        _exit(cap)
        return

    except SystemExit:
        _exit(cap)
        return

    finally:
        _exit(cap)


if __name__ == "__main__":
    main()
