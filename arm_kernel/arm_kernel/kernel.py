from tokenize import String
from ipykernel.kernelbase import Kernel
import socket
import selectors
import types
from io import StringIO

messages = []


def start_connections(host, port, sel, readOnly=False):
    server_addr = (host, port)
    connid = 1
    print("starting connection", connid, "to", server_addr)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(True)
    try:
        sock.connect(server_addr)
        checkErr = 0
        sock.setblocking(False)
    except Exception as err:
        print("Error: ", err)
        checkErr = -1
    if readOnly:
        events = selectors.EVENT_READ
    else:
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
    data = types.SimpleNamespace(
        connid=connid,
        msg_total=sum(len(m) for m in messages),
        recv_total=0,
        messages=list(messages),
        outb=b"",
    )
    sel.register(sock, events, data=data)
    return checkErr


def service_connection(key, mask, outString, sel):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            # print("received", repr(recv_data), "from connection", data.connid)
            # print("\n---------------\n", recv_data.decode("utf-8"), "\n---------------")
            outString.write(recv_data.decode("utf-8"))
            data.recv_total += len(recv_data)
        if not recv_data or data.recv_total == data.msg_total:
            print("closing connection", data.connid)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if not data.outb and data.messages:
            data.outb = data.messages.pop(0)
        if data.outb:
            print("sending source code to connection", data.connid)
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]

def connectToPi(host, port, code):
    contents = bytes(code, 'utf-8')
    messages.clear()
    messages.append(contents)
    sel = selectors.DefaultSelector()
    checkErr = start_connections(host, int(port), sel)
    if checkErr == 0:
        file_str = StringIO()
        try:
            while True:
                events = sel.select(timeout=1)
                if events:
                    for key, mask in events:
                        service_connection(key, mask, file_str, sel)
                # Check for a socket being monitored to continue.
                if not sel.get_map():
                    break
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")
        finally:
            sel.close()
        return file_str.getvalue()
    else:
        sel.close()
        return "Error connecting to Raspberry Pi"

def getPiAddress(host, port):
    sel = selectors.DefaultSelector()
    checkErr = start_connections(host, int(port), sel, True)
    if checkErr == 0:
        file_str = StringIO()
        try:
            while True:
                events = sel.select(timeout=1)
                if events:
                    for key, mask in events:
                        service_connection(key, mask, file_str, sel)
                # Check for a socket being monitored to continue.
                if not sel.get_map():
                    break
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")
        finally:
            sel.close()
        return file_str.getvalue().strip()
    else:
        sel.close()
        return "Error connecting to Raspberry Pi Head Node"

class ArmKernel(Kernel):
    implementation = 'ARM Assembly'
    implementation_version = '1.0'
    language = 'no-op'
    language_version = '0.1'
    language_info = {
        'name': 'Any text',
        'mimetype': 'text/plain',
        'file_extension': '.txt',
    }
    banner = "ARM kernel"

    def do_execute(self, code, silent, store_history=True, user_expressions=None,
                   allow_stdin=False):
        secondLine = code.splitlines()[1]
        if secondLine[0:5].lower() == "/*ip:" and secondLine[-2:] == "*/":
            piAdress = secondLine[5:-2].strip()
        else:
            piAdress = getPiAddress('162.210.90.78', 1338)
        output = connectToPi(piAdress, 1337, code)
        if output == None:
            output = "Error connecting to Raspberry Pi"
        if not silent:
            stream_content = {'name': 'stdout', 'text': output}
            self.send_response(self.iopub_socket, 'stream', stream_content)

        return {'status': 'ok',
                # The base class increments the execution count
                'execution_count': self.execution_count,
                'payload': [],
                'user_expressions': {},
               }
