#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse


def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class HTTPClient(object):
    #def get_host_port(self,url):

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    def get_code(self, data):
        '''Return response status code as integer'''
        if data:
            return int(data.split('\r\n')[0].split()[1])
        else:
            return 404

    def get_headers(self,data):
        '''Return response headers in a dictionary'''
        headers = {}
        if data:
            for header in data.split('\r\n\r\n')[0].split('\r\n')[1:]:
                idx = re.search(":", header).start()
                headers[header[0:idx]] = header[idx+2:]
            print(headers)
        else:
            return ""

    def get_body(self, data):
        '''Return response body as a string'''
        if data:
            return data.split('\r\n\r\n')[1]
        else:
            return ""
    
    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))
        
    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')
    
    def header_builder(self, method, host, path, headers_dict, args = "", query = ""):
        '''Header builder for GET and POST'''

        # setting up query if it exists
        if query != "":
            path += "?{}".format(query)
        headers = "{} {} HTTP/1.1\r\n".format(method, path)
        headers += "Host: {}\r\n".format(host)
        
        for header in headers_dict:
            headers += "{}: {}\r\n".format(header, headers_dict[header])
        
        headers += '\r\n'
        
        # args provided through forms
        if args:
            headers += args
        else:
            headers += urllib.parse.urlencode("")

        return headers

    def GET(self, url, args=None):
        code = 500
        body = ""

        # parsed URL
        parsed = urllib.parse.urlparse(url)

        host = parsed.netloc.split(':')[0]
        
        # HTTP requirement
        port = parsed.port
        if port is None:
            port = 80
        
        # path fixing
        path = parsed.path
        if path == "":
            path = "/"

        # args encoding
        if args:
            args = urllib.parse.urlencode(args)
        
        # exception handling if host is invalid or any other exceptions
        try:
            self.connect(host, port)
            headers = self.header_builder("GET", host, path, {
                'Accept': '*/*',
                'Connection': 'close'
            }, args, query=parsed.query)
            self.sendall(headers)
            res = self.recvall(self.socket)
            
            # As a user when I GET or POST I want the result printed to stdout
            print(res)

            # setting up for return at the end
            code = self.get_code(res)
            body = self.get_body(res)

        except Exception as e:
            print("ERROR:", e)
            code = 404
        
        # closing socket
        self.close()

        return HTTPResponse(code, body)

    def POST(self, url, args=None):
        code = 500
        body = ""

        # parsed URL
        parsed = urllib.parse.urlparse(url)

        host = parsed.netloc.split(':')[0]

        # HTTP requirement
        port = parsed.port
        if port is None:
            port = 80
        
        # path fixing
        path = parsed.path
        if path == "":
            path = "/"

        # encoding args and getting length
        args_length = 0
        if args:
            args = urllib.parse.urlencode(args)
            args_length = len(args)

        # exception handling if host is invalid or any other exceptions
        try:
            self.connect(host, port)

            # content length included
            headers = self.header_builder("POST", host, path, {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Content-Length': '{}'.format(args_length),
                'Connection': 'close'
            }, args, query=parsed.query)
            self.sendall(headers)
            res = self.recvall(self.socket)

            # As a user when I GET or POST I want the result printed to stdout
            print(res)

            code = self.get_code(res)
            body = self.get_body(res)

        except Exception as e:
            print("ERROR:", e)
            code = 404

        # closing socket
        self.close()

        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
