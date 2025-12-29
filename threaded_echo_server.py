#!/usr/bin/env python3
import socket
import threading

HOST = "0.0.0.0"  # Listen on all interfaces so others can connect!
PORT = 65432

def handle_client(conn, addr):
    """
    Worker function that runs in a separate thread for each client.
    """
    print(f"[NEW CONNECTION] {addr} connected.")
    
    connected = True
    while connected:
        try:
            # Blocking call, but only blocks THIS thread
            data = conn.recv(1024)
            if not data:
                break
            
            msg = data.decode('utf-8')
            print(f"[{addr}] {msg}")
            
            # Echo back
            conn.sendall(data)
        except ConnectionResetError:
            break

    conn.close()
    print(f"[DISCONNECTED] {addr} disconnected.")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    
    print(f"[LISTENING] Server is listening on {HOST}:{PORT}")
    
    while True:
        # 1. Wait for a new connection
        conn, addr = server.accept()
        
        # 2. Create a new thread to handle this specific connection
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        
        # 3. Start the thread (it runs handle_client in the background)
        thread.start()
        
        # 4. Print active connections (thread count - 1 for main thread)
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    print("[STARTING] Server is starting...")
    start_server()