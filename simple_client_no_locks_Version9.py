#!/usr/bin/env python3
# simple_client_no_locks.py -- minimal threaded client to receive while you type

import socket
import threading
import sys

HOST = '127.0.0.1'  # change to server IP if needed
PORT = 65433

def listener(sock):
    """Read lines from the socket and print them immediately."""
    f = sock.makefile('r', encoding='utf-8', newline='\n')
    try:
        for line in f:
            line = line.rstrip('\n').rstrip('\r')
            print("\r" + line)
            print("> ", end='', flush=True)
    except Exception:
        pass
    finally:
        try:
            sock.close()
        except Exception:
            pass
        sys.exit(0)

def main():
    name = input("Your name: ").strip() or "Anon"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    # send name as first line
    s.sendall((name + '\n').encode('utf-8'))

    # start listener thread
    t = threading.Thread(target=listener, args=(s,), daemon=True)
    t.start()

    print("Connected. Type messages and press Enter. Type EXIT to quit.")
    try:
        while True:
            line = input("> ")
            if not line:
                continue
            s.sendall((line + '\n').encode('utf-8'))
            if line.strip().upper() == 'EXIT':
                break
    except KeyboardInterrupt:
        pass
    finally:
        try:
            s.close()
        except Exception:
            pass

if __name__ == '__main__':
    main()