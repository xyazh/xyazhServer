from login_and_register import LoggingData
from login_and_register import RegisterData
from MailHellper import MailHelper
from msg import MsgData
import xyazhServer
import time
import json
import re
import os
import urllib

ANO_UUID = "96502ac1-fc9c-6637-aaa0-98a8ca597f42"

class MyWebApp:
    H = "http"
    IP_CHECK_MAIL_TIMER = {}
    user_data_manager = xyazhServer.DataManager("\\user_data\\")
    temp_mail_data_manager = xyazhServer.DataManager("\\temp_mail_data\\")
    msg_data_manager = xyazhServer.DataManager("\\msg_data\\")
    ano_img_data_manager = xyazhServer.DataManager("\\ano_img_data\\")
    mail_helper = MailHelper()

    def __init__(self):
        if MyWebApp.H == "http":
            self.app = xyazhServer.App("127.0.0.1", 80)
        elif MyWebApp.H == "https":
            self.app = xyazhServer.App("127.0.0.1", 443)

    def run(self):
        if MyWebApp.H == "http":
            self.app.runHTTP()
        elif MyWebApp.H == "https":
            self.app.runHTTPS(
                ('cert/server.crt', 'cert/server_rsa_private.pem.unsecure'))

    def load(self):
        root = "./web"
        v_root = "/res"

        def vPath(s: xyazhServer.Server):
            path = s.v_path.replace(v_root, root, 1)
            s.sendFile(path)
        xyazhServer.PageManager.addFileTree(root, v_root, vPath)

    @xyazhServer.PageManager.register("/", "GET")
    def dis(s: xyazhServer.Server):
        s.sendFileBreakpoint(".\\data\\192d9a98d782d9c74c96f09db9378d93.mp4")

    @xyazhServer.PageManager.register("/favicon.ico", "GET")
    def fav(s: xyazhServer.Server):
        s.sendFileBreakpoint(".\\web\\images\\favicon.png")

    @xyazhServer.PageManager.register("/index", "GET")
    @xyazhServer.PageManager.register("/index.html", "GET")
    def reindex(s: xyazhServer.Server):
        host = s.headers.get("Host")
        if host == None:
            s.send_error(404)
            return
        s.send_response(301, "Moved Permanently")

        s.send_header("Location", MyWebApp.H +
                      "://" + host + "/res/index.html")
        s.end_headers()

    @xyazhServer.PageManager.register("/api/send_mail_code", "POST")
    def mailCheckCodeApi(s: xyazhServer.Server):
        user_ip = s.address_string()
        t = time.time()
        if user_ip in MyWebApp.IP_CHECK_MAIL_TIMER:
            if t - MyWebApp.IP_CHECK_MAIL_TIMER[user_ip] > 55:
                MyWebApp.IP_CHECK_MAIL_TIMER[user_ip] = t
            else:
                s.send_error(403, "resetting time")
                return
        else:
            MyWebApp.IP_CHECK_MAIL_TIMER[user_ip] = t
        r_data: bytes = s.readPostDataTimeout()
        try:
            user_mail = str(r_data, encoding="utf8")
        except UnicodeDecodeError:
            s.send_error(400, "Not mail")
            return
        if not re.match(r"^\w+([\.\-]\w+)*\@\w+([\.\-]\w+)*\.\w+$", user_mail):
            s.send_error(400, "Not mail")
            return
        check_code = s.randomIntStr(6)
        tmp = MyWebApp.user_data_manager.get("user_list.json", user_mail)
        if tmp != None:
            s.send_error(409, "hased mail")
            return
        MyWebApp.temp_mail_data_manager.setMenbers(
            user_mail+".json", {"check_code": check_code, "time": t})
        xyazhServer.ConsoleMessage.printDebug(check_code)
        MyWebApp.mail_helper.sendMail(user_mail,"你的验证码是：%s, 请勿泄露给他人（十分钟有效）"%check_code)
        s.send_response(204, "No Content")
        s.end_headers()

    @xyazhServer.PageManager.register("/api/register", "POST")
    def registerApi(s: xyazhServer.Server):
        r_data: bytes = s.readPostDataTimeout()
        try:
            user_data: dict = json.loads(r_data)
        except json.decoder.JSONDecodeError as e:
            s.send_error(400, "json decoder error")
            return
        register_data = RegisterData(user_data)
        if not register_data.check():
            s.send_error(400, "incomplete data")
            return
        m = MyWebApp.temp_mail_data_manager.getMenbers(
            register_data.user_mail+".json", ("check_code", "time"), lambda x: 0)
        t = time.time()
        if len(register_data.user_name) > 20:
            s.send_error(413, "username too long")
            return
        if t - m["time"] > 600:
            s.send_error(403, "code timeout")
            return
        if register_data.check_code != m["check_code"]:
            s.send_error(401, "code error")
            return
        tmp = MyWebApp.user_data_manager.get(
            "user_mail_list.json", register_data.user_mail)
        if tmp != None:
            s.send_error(409, "hased mail")
            return
        MyWebApp.user_data_manager.set(
            "user_mail_list.json", register_data.user_mail, 1)
        tmp = MyWebApp.user_data_manager.get(
            "user_name_list.json", register_data.user_mail)
        if tmp != None:
            s.send_error(409, "hased username")
            return
        MyWebApp.user_data_manager.set(
            "user_name_list.json", register_data.user_mail, 1)
        sl = s.randomIntStr(16)
        token = s.safeHash(sl, register_data.password)
        uid = s.lzs.compressToEncodedURIComponent(register_data.user_mail)
        MyWebApp.user_data_manager.set(
            "user_token.json", register_data.user_mail, token)
        MyWebApp.user_data_manager.setMenbers(token+".json", {
            "user_name": register_data.user_name,
            "password": register_data.password,
            "token": token,
            "sl": sl,
            "email": register_data.user_mail,
            "uid": uid,
            "level": 0
        })
        s.sendTextPage(json.dumps({"token": token, "level": 0, "uid": uid,
                       "user_name": register_data.user_name}, ensure_ascii=False).encode("utf8"))

    @xyazhServer.PageManager.register("/api/logging", "POST")
    def loggingApi(s: xyazhServer.Server):
        r_data: bytes = s.readPostDataTimeout()
        try:
            user_data: dict = json.loads(r_data)
        except json.decoder.JSONDecodeError as e:
            s.send_error(400, "json decoder error")
            return
        logging_data = LoggingData(user_data)
        if not logging_data.check():
            s.send_error(400, "incomplete data")
            return
        token = MyWebApp.user_data_manager.get(
            "user_token.json", logging_data.user_mail)
        if token == None:
            s.send_error(404, "not found user")
            return
        l_data = MyWebApp.user_data_manager.getMenbers(
            token+".json", ["level", "uid", "user_name", "password"])
        if l_data["password"] != logging_data.password:
            s.send_error(401, "password error")
            return
        s.sendTextPage(json.dumps(
            {"token": token, "level": l_data["level"], "uid": l_data["uid"], "user_name": l_data["user_name"]}, ensure_ascii=False).encode("utf8"))

    @xyazhServer.PageManager.register("/api/msg_send", "POST")
    def msgSendApi(s: xyazhServer.Server):
        user_ip = s.address_string()
        t = time.time()
        if user_ip in MyWebApp.IP_CHECK_MAIL_TIMER:
            if t - MyWebApp.IP_CHECK_MAIL_TIMER[user_ip] > 5:
                MyWebApp.IP_CHECK_MAIL_TIMER[user_ip] = t
            else:
                s.send_error(403, "resetting time")
                return
        else:
            MyWebApp.IP_CHECK_MAIL_TIMER[user_ip] = t
        MyWebApp.IP_CHECK_MAIL_TIMER
        r_data: bytes = s.readPostDataTimeout()
        try:
            msg_data: dict = json.loads(r_data)
        except json.decoder.JSONDecodeError as e:
            s.send_error(400, "json decoder error")
            return
        msg = MsgData(msg_data)
        if not msg.check():
            s.send_error(400, "incomplete data")
            return
        user_name = msg.name
        if msg.token:
            user_name = MyWebApp.user_data_manager.get(
                msg.token+".json", "user_name")
            if not user_name:
                s.send_error(404, "not found user")
                return
        else:
            if 9 > time.localtime().tm_hour > 0:
                s.send_error(403, "curfew")
                return
        mid = MyWebApp.msg_data_manager.findGet("max_id.json", "max_id", 0) + 1
        MyWebApp.msg_data_manager.set("max_id.json", "max_id", mid)
        r_msg = {"msg_id": mid, "title": msg.title,
                 "user_name": user_name, "msg": msg.text, "token": msg.token}
        MyWebApp.msg_data_manager.set("msgs.json", str(mid), r_msg)
        s.sendTextPage(json.dumps(r_msg, ensure_ascii=False).encode("utf8"))

    @xyazhServer.PageManager.register("/api/msg_get", "GET")
    def msgGetApi(s: xyazhServer.Server):
        m: dict = MyWebApp.msg_data_manager.get("msgs.json")
        msgs = list(m.values())
        s.sendTextPage(json.dumps(msgs, ensure_ascii=False).encode("utf8"))

    @xyazhServer.PageManager.register("/upload", "POST")
    def upload(s: xyazhServer.Server):
        if s.headers["token"] != ANO_UUID:
            s.send_error(403,"Unauthorized")
            s.rfile.flush()
            return
        file_size = int(s.headers["Content-Length"])
        end = b""
        filename = ""
        webkit = b""
        for _ in range(100):
            line_data = s.rfile.readline(8192)
            if webkit == b"":
                webkit = line_data[:-2]
            file_size -= len(line_data)
            # 获取文件名
            if b"Content-Disposition" in line_data:
                match = re.search(b'Content-Disposition: form-data;.*filename="(?P<filename>[^"]+)"',line_data, re.DOTALL)
                if not match:
                    s.send_error(400, 'Invalid request')
                    return
                filename = match.groupdict()['filename'].decode('utf-8')
            if (line_data == b"\r\n" and end == b"\r\n") or line_data == b"":
                break
            end = line_data[-2:]
            if end != b"\r\n":
                return
        file_size -= len(webkit) + 4
        path = os.getcwd() + "/ano_img_bed"
        if not os.path.exists(path):
            os.mkdir(path)
        with open("%s/%s"%(path,filename), "wb") as f:
            while True:
                if file_size <= 0:
                    break
                line_data = s.rfile.readline(8192)
                file_size -= len(line_data)
                f.write(line_data)
        s.rfile.readline()
        MyWebApp.ano_img_data_manager.set("ano_images.json",str(time.time()),filename)
        r = {
            "code": 0,
            "msg": "",
            "data": {
                "src": ""
            }
        }
        s.sendTextPage(json.dumps(r))

    @xyazhServer.PageManager.register("/anoimgbed/*", "GET")
    def anoImgBed(s: xyazhServer.Server):
        cookie_str = s.headers["Cookie"]
        token = None
        if cookie_str != None:
            cookie = s.cookiesStrToDict(cookie_str)
            token = cookie.get("ano_token",None)
        if token != ANO_UUID:
            s.send_error(403,"Unauthorized")
            s.rfile.flush()
            return
        path_args:list[str] = xyazhServer.UrlHelper.pathSplit(s.v_path)
        file_name = path_args[1]
        file_name = urllib.parse.unquote(file_name)
        s.sendFile("./ano_img_bed/%s"%file_name)

    @xyazhServer.PageManager.register("/anoimgbed", "POST")
    def anoImgList(s: xyazhServer.Server):
        data = s.readPostData()
        try:
            token_data: dict = json.loads(data)
        except json.decoder.JSONDecodeError as e:
            s.send_error(400, "json decoder error")
            return
        token = token_data.get("ano_token",None)
        if token != ANO_UUID:
            s.send_error(403,"Unauthorized")
            s.rfile.flush()
            return
        s.sendFile("./ano_img_data/ano_images.json")


if __name__ == "__main__":
    my_web_app = MyWebApp()
    my_web_app.load()
    my_web_app.run()
