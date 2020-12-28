import os
import socket
import threading
import urllib.request
import cv2

ADDR = '127.0.0.1'
PORT = 8000
APPLICATION_STOPPED = False

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((ADDR, PORT))
s.listen(2)

CLIENT = None


def new_client():
    print("Listening for connections at:")
    print("IP:", urllib.request.urlopen('https://ident.me').read().decode('utf8'), "Port:", PORT)
    clientsocket, clientaddr = s.accept()
    clientsocket.send(b"CONNECTED")
    print(f"Client from {clientaddr} has established a connection!")
    return clientsocket


def listen_for_messages():
    global CLIENT

    while True:
        msg = CLIENT.recv(2048).decode("utf-8")

        if msg == "QUIT":
            print("Connection closed by client!")
            CLIENT = new_client()


def main():
    global CLIENT

    # Initialize OpenCV stuff
    cap = cv2.VideoCapture(0)
    cascade_classifier = cv2.CascadeClassifier(os.path.join("server", "haar_cascade_face.xml"))

    CLIENT = new_client()

    try:
        listen_thread = threading.Thread(target=listen_for_messages, daemon=True)
        listen_thread.start()

        # Broadcasting messages
        while True:
            cam_available, img = cap.read()

            # Camera operation
            if cam_available:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                print("hmm")
                faces = cascade_classifier.detectMultiScale3(gray, minSize=(50, 50), minNeighbors=4)
                print("hmm2")

                for (x, y, w, h) in faces:
                    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 3)

                cv2.imshow("Camera Output", img)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    cap.release()
                    break

    except KeyboardInterrupt:
        cap.release()


if __name__ == "__main__":
    main()
    try:
        print("Exiting...")
        CLIENT.send(b"QUIT")
        s.close()
    except AttributeError:
        pass
