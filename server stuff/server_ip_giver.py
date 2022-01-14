#!/usr/bin/env python3

import sys
import socket
import selectors
import types
import subprocess
import os
from threading import Thread
from time import sleep

sel = selectors.DefaultSelector()
ipList = [b'162.210.90.81', b'162.210.90.83', b'162.210.90.85', b'162.210.90.78']
currentIndex = 0

# def check_timeout(data):
#     curTime = 0
#     while curTime < 15:
#         sleep(0.1)
#         curTime += 0.1
#         if data.done == True:
#             #print("Stopping timeout checker")
#             return
    
#     if data.code != None:
#         data.code = None
#         data.outb = b"Timed Out"
#     #print("Timeout event")

def accept_wrapper(sock):
    global currentIndex
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", done=False)
    data.outb = ipList[currentIndex]
    currentIndex = (currentIndex + 1) % len(ipList)
    events = selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    # timeThread = Thread(target=check_timeout, args=(data,))
    # timeThread.start()


def service_connection(key, mask):
    global currentIndex
    
    sock = key.fileobj
    data = key.data
        
    # if mask & selectors.EVENT_READ:
    #     try:
    #         recv_data = sock.recv(1024)  # Should be ready to read
    #         if recv_data:
    #             data.code += recv_data
    #         else:
    #             print("closing connection to", data.addr)
    #             sel.unregister(sock)
    #             sock.close()
    #     except:
    #         data.code = b""
    #         data.outb = b""
    #         print("Failure to connect. Closing connection to", data.addr)
    #         sel.unregister(sock)
    #         sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]
            if data.outb == b"":
                data.done = True
        if data.done == True:
            print("Success. Closing connection to", data.addr)
            sel.unregister(sock)
            sock.close()

host = ''
port = 1338

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
lsock.bind((host, port))
lsock.listen()
print("listening on", (host, port))
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask)
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()

