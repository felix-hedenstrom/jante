#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import re

from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import hashlib
import random
import base64
import ssl

class WebJanteRequestHandler(BaseHTTPRequestHandler):
    def send_http_response_code(self, code):
        self.send_response(code)

    def send_http_header(self, key, value):
        assert self.headers_ended == False
        self.send_header(key, value)

    def send_http_output(self, data, raw=False):
        if self.headers_ended == False:
            self.end_headers()
            self.headers_ended = True

        if raw == True:
            self.wfile.write(data)
        else:
            self.wfile.write(data.encode('utf-8'))

    def do_GET(self):
        self.headers_ended = False

        cookie = self.headers.get('Cookie')
        cookie_dict = {}

        if cookie != None:
            cookie_dict = urllib.parse.parse_qs(cookie)

        # if the session id is present and can be validated, proceed using webrespond
        if 'sessid' in cookie_dict\
         and cookie_dict['sessid'][0] in self.server.jantehttpd.authenticated_sessions\
         and self.server.jantehttpd.authenticated_sessions[cookie_dict['sessid'][0]] == self.client_address[0]: # TODO: use more client identifiers, not just IP address
            # authenticated users can play with jante
            self.server.jantehttpd.requestcallback(self)
        else:
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

            # did the client try to auth?
            if self.client_address[0] in self.server.jantehttpd.preauth_challenge and 'response' in query:
                # calculate the expected response
                THE_PASSWORD = self.server.jantehttpd.password
                hash = hashlib.sha256()
                hash.update((self.server.jantehttpd.preauth_challenge[self.client_address[0]] + THE_PASSWORD).encode('utf-8'))
                good_response = hash.hexdigest()

                del self.server.jantehttpd.preauth_challenge[self.client_address[0]]

                # send a status code indicating redirection
                self.send_http_response_code(303)

                # if the client sent a good response, create a session token
                # TODO: should probably set a timeout on session tokens
                if query['response'][0] == good_response:
                    self.server.jantehttpd.logger.log('httpd: good auth from {}'.format(self.client_address[0]))

                    sessid = base64.b64encode((self.client_address[0] + str(random.random())).encode('utf-8')).decode('ascii')
                    self.server.jantehttpd.authenticated_sessions[sessid] = self.client_address[0]
                    self.send_http_header('Set-Cookie', 'sessid={}'.format(sessid))
                else:
                    self.server.jantehttpd.logger.log('httpd: bad auth from {}'.format(self.client_address[0]))

                # get rid of the response= part of the query string
                redirect_location = re.sub(r'(?<=\?|&)response=[a-z0-9]+', '', self.path)

                # get rid of potential empty trailing query string fragment
                while redirect_location.endswith('?') or redirect_location.endswith('&'):
                    redirect_location = redirect_location[:-1]

                # redirect the client
                self.send_http_header('Location', redirect_location)
                self.send_http_output('Redirect')
            elif not self.path.endswith('/favicon.ico'):
                # generate a challenge for the client address
                # TODO: use more client identifiers, not just IP address
                self.server.jantehttpd.preauth_challenge[self.client_address[0]] = str(random.random()) + str(random.random())

                self.server.jantehttpd.logger.log('httpd: generating preauth challenge for {}'.format(self.client_address[0]))

                # send the authentication page/form
                self.send_http_response_code(200)
                self.send_http_header('Content-type', 'text/html; charset=utf-8')
                self.send_http_output('''
<!DOCTYPE html>
<html>
    <head>
        <title>Authentication</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/crypto-js/3.1.9-1/crypto-js.min.js"></script>
        <script>
            hash_response = function()
            {{
                document.getElementById('authform').response.value = CryptoJS.SHA256('{challenge}' + document.getElementById('authform').response.value)
            }};
        </script>
    </head>
    <body>
        <form id="authform" method="get" action="" onsubmit="hash_response(); return true;">
            <input type="text" name="response" value="" />
            <!-- apparently calling this.form.submit() doesnt trigger onsubmit on the form? -->
            <input type="button" name="ok" value="auth" onclick="hash_response(); this.form.submit();" />
        </form>
    </body>
</html>'''.format(challenge=self.server.jantehttpd.preauth_challenge[self.client_address[0]]))
            else:
                self.send_http_response_code(404)
                self.send_http_header('Content-type', 'text/plain; charset=utf-8')
                self.send_http_output('Not found')

    def log_message(self, format, *args):
        # self.server.jante._io.log(format.format(*args))
        pass

class JanteHTTPD:
    def __init__(self, port, password, requestcallback, logger, _keyfile='ssl/key.pem', _certfile='ssl/cert.pem'):
        self.httpd = HTTPServer(('', port), WebJanteRequestHandler)
        self.httpd.socket = ssl.wrap_socket(self.httpd.socket, keyfile=_keyfile, certfile=_certfile, server_side=True)
        self.httpd.jantehttpd = self

        # the request handler will read the password
        self.password = password

        # the request handler will call requestcallback(self)
        self.requestcallback = requestcallback

        # the request handler will call logger.log()
        self.logger = logger

        # the request handler will read and write to preauth_challenge
        self.preauth_challenge = dict()

        # the request handler will read and write to authenticated_sessions
        self.authenticated_sessions = dict()

    def start(self):
        self.httpd.serve_forever()

    def start_in_thread(self):
        t = threading.Thread(target=self.start, name="JanteWebHost - Hosts the JanteWeb!")
        t.start()

    def shutdown(self):
        self.httpd.shutdown()
