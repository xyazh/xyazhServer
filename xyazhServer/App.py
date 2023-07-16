from .Server import Server
from .ihttp import server
import socket
import ssl
import sys
import os


class App:
    def __init__(self,host:str,port:int):
        self.host = host
        self.port = port
        self.httpd = server.ThreadingHTTPServer((self.host, port),Server)
        self.httpd.socket.settimeout(5)
        self.httpd.timeout
        self.context = None

    def pTitleVison(self,t:str):
        print(" * ---------------------------------")
        print(" * xyazhServer %s"%(Server.server_version))
        print(" * Server is runing on %s:%s"%(self.host,self.port))
        print(" * HTTP url is %s://%s:%s/ (Press CTRL+C to quit)"%(t,self.host,self.port))
        print(" * ---------------------------------\r\n\r\n")

    def runHTTP(self):
        self.pTitleVison("http")
        self.httpd.serve_forever()

    def runHTTPS(self,cert_chain=tuple[str]):
        self.context= ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)    
        self.context.load_cert_chain(*cert_chain)
        self.httpd.socket= self.context.wrap_socket(self.httpd.socket, server_side = True)
        self.pTitleVison("https")
        self.httpd.serve_forever()