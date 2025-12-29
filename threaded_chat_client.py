#!/usr/bin/env python3
import socket
import threading
import sys

# CHANGE THIS to the IP of the server (if it's not on your computer)
# e.g., HOST = "192.168.1.5"
HOST = "127.0.0.1"
PORT = 65433

def receive_messages(sock):
    """
    Continually listens for messages from the server and prints them.
    Runs in a separate thread.
    """
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("\n[Server closed connection]")
                break
            print(data.decode('utf-8'))
        except:
            print("\n[Connection lost]")
            break
    sock.close()
    sys.exit()

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((HOST, PORT))
    except ConnectionRefusedError:
        print("Could not connect to server. Is it running?")
        return

    print(f"Connected to chat server at {HOST}:{PORT}")
    
    # 1. Start a thread to listen for incoming messages
    # daemon=True means this thread dies automatically when the main program exits
    receive_thread = threading.Thread(target=receive_messages, args=(client,), daemon=True)
    receive_thread.start()

    # 2. Main thread handles sending messages
    try:
        while True:
            msg = input() # Blocks waiting for user input
            if msg.lower() == 'exit':
                break
            client.sendall(msg.encode('utf-8'))
    except KeyboardInterrupt:
        print("Exiting...")
    
    client.close()

if __name__ == "__main__":
    start_client()