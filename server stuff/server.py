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

def check_timeout(data):
    curTime = 0
    while curTime < 15:
        sleep(0.1)
        curTime += 0.1
        if data.code == None and data.outb == b"":
            #print("Stopping timeout checker")
            return
    
    if data.code != None:
        data.code = None
        data.outb = b"Timed Out"
    #print("Timeout event")

def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    conn.setblocking(False)
    timeThread = None
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", code=b"", timeoutThread=timeThread)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    timeThread = Thread(target=check_timeout, args=(data,))
    timeThread.start()


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
        
    if mask & selectors.EVENT_READ:
        try:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                data.code += recv_data
            else:
                print("closing connection to", data.addr)
                sel.unregister(sock)
                sock.close()
        except:
            data.code = b""
            data.outb = b""
            print("Failure to connect. Closing connection to", data.addr)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.code:
            #print("echoing", repr(data.outb), "to", data.addr)
            print("received data, compiling")
            if os.path.exists("code"):
                os.remove("code")
            f = open("code.s", "wb")
            f.write(data.code)
            f.close()
            printResult = b""
            if data.code[0:6] == "/*ARM*/" or data.code[0:6] == "/*arm*/":
                result = subprocess.run(['gcc', 'code.s', '-o', 'code'], capture_output=True)
            elif data.code[0:4] == "/*C*/" or data.code[0:4] == "/*c*/":
                result = subprocess.run(["gcc", "code.s", "-c", "code"], capture_output = True)
            else:
                result = "Code indicator incorrect. Please check the first line comment."
            printResult += result.stdout
            printResult += result.stderr
            #print(result.stdout.decode('utf-8'))
            try:
                result2 = subprocess.run(['./code'], capture_output=True)
                printResult += result2.stdout
                printResult += result2.stderr
                #print(result2.stdout.decode('utf-8'))
            except:
                print("Halting.")
            data.outb = printResult
            data.code = None
        if data.outb:
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]
        if data.code == None and data.outb == b"":
            print("Success. Closing connection to", data.addr)
            sel.unregister(sock)
            sock.close()

host = ''
port = 1337

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

