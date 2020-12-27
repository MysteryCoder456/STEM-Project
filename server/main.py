import socket
import threading
import urllib.request

ADDR = '127.0.0.1'
PORT = 8000
APPLICATION_STOPPED = False

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((ADDR, PORT))
s.listen(2)
print("Listening for connections at:")
print("IP:", urllib.request.urlopen('https://ident.me').read().decode('utf8'), "Port:", PORT)

CLIENT = None


def new_client():
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
    CLIENT = new_client()

    listen_thread = threading.Thread(target=listen_for_messages, daemon=True)
    listen_thread.start()

    # Broadcasting messages
    while True:
        continue


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        CLIENT.send(b"QUIT")
        s.close()
