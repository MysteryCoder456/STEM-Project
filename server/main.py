import socket
import urllib.request

ADDR = '127.0.0.1'
PORT = 8000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((ADDR, PORT))
s.listen(2)
print("Listening for connections at:")
print("IP:", urllib.request.urlopen('https://ident.me').read().decode('utf8'), "Port:", PORT)


def new_client():
    while True:
        clientsocket, clientaddr = s.accept()
        clientsocket.send(b"CONNECTED")


def main():
    client = new_client()


if __name__ == "__main__":
    main()
