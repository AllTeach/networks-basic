#!/usr/bin/env python3
import socket
import threading

HOST = "0.0.0.0"
PORT = 65433  # Different port than Echo

# Global list to keep track of all connected clients
clients = []

def broadcast(message, _sender_conn):
    """
    Sends a message to all clients EXCEPT the sender.
    """
    for client in clients:
        if client != _sender_conn:
            try:
                client.sendall(message)
            except:
                # If sending fails, assume client is dead and remove
                clients.remove(client)

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    
    # 1. Ask for a nickname immediately
    conn.sendall(b"Welcome! Enter your nickname: ")
    try:
        nickname = conn.recv(1024).decode('utf-8').strip()
    except:
        conn.close()
        return

    welcome_msg = f"{nickname} has joined the chat!\n".encode('utf-8')
    broadcast(welcome_msg, conn)
    
    connected = True
    while connected:
        try:
            data = conn.recv(1024)
            if not data:
                break
            
            # Format message: "Nickname: Message"
            msg = f"{nickname}: {data.decode('utf-8')}".encode('utf-8')
            broadcast(msg, conn)
            
        except:
            break

    # Cleanup
    if conn in clients:
        clients.remove(conn)
    
    leave_msg = f"{nickname} has left the chat.\n".encode('utf-8')
    broadcast(leave_msg, conn)
    conn.close()
    print(f"[DISCONNECTED] {addr} disconnected.")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    
    print(f"[LISTENING] Chat Server is listening on {HOST}:{PORT}")
    
    while True:
        conn, addr = server.accept()
        clients.append(conn)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    start_server()