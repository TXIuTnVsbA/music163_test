# -*- coding: utf-8 -*-
import requests
import json
import os
import base64
import binascii
import hashlib
import re,time
from Crypto.Cipher import AES
from pprint import pprint
session = requests.Session()
#proxies = {'http':'http://localhost:8888','https':'https://localhost:8888'} #debug
modulus = ('00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7'
           'b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280'
           '104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932'
           '575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b'
           '3ece0462db0a22b8e7')
nonce = '0CoJUm6Qyw8W8jud'
pubKey = '010001'
header = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip,deflate,sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'music.163.com',
            'Referer': 'http://music.163.com/',
            'Origin':'http://music.163.com',
            'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36',
}
#test={"logs":"[{\"action\":\"play\",\"json\":{\"type\":\"song\",\"wifi\":0,\"download\":0,\"id\":36990233,\"time\":214,\"end\":\"ui\"}}]","csrf_token":"9b46911e2b864b0bd3282bda2bb26c16"}
default_timeout = 10
def aesEncrypt(text, secKey):
    pad = 16 - len(text) % 16
    text = text + chr(pad) * pad
    encryptor = AES.new(secKey, 2, '0102030405060708')
    ciphertext = encryptor.encrypt(text)
    ciphertext = base64.b64encode(ciphertext).decode('utf-8')
    return ciphertext

def rsaEncrypt(text, pubKey, modulus):
    text = text[::-1]
    rs = pow(int(binascii.hexlify(text), 16), int(pubKey, 16), int(modulus, 16))
    return format(rs, 'x').zfill(256)

def createSecretKey(size):
    return binascii.hexlify(os.urandom(size))[:16]

# 歌曲加密算法, 基于https://github.com/yanunon/NeteaseCloudMusic脚本实现
def encrypted_id(id):
    magic = bytearray('3go8&$8*3*3h0k(2)2', 'u8')
    song_id = bytearray(id, 'u8')
    magic_len = len(magic)
    for i, sid in enumerate(song_id):
        song_id[i] = sid ^ magic[i % magic_len]
    m = hashlib.md5(song_id)
    result = m.digest()
    result = base64.b64encode(result)
    result = result.replace(b'/', b'_')
    result = result.replace(b'+', b'-')
    return result.decode('utf-8')

# 登录加密算法, 基于https://github.com/stkevintan/nw_musicbox脚本实现
def encrypted_request(text):
    text = json.dumps(text)
    secKey = createSecretKey(16)
    encText = aesEncrypt(aesEncrypt(text, nonce), secKey)
    encSecKey = rsaEncrypt(secKey, pubKey, modulus)
    data = {'params': encText, 'encSecKey': encSecKey}
    return data

class netease():
    def __init__(self):
        self.session=session
        self.header=header

    def httpRequest(self,
                    method,
                    action,
                    query=None,
                    urlencoded=None,
                    callback=None,
                    timeout=None):
        connection = json.loads(
            self.rawHttpRequest(method, action, query, urlencoded, callback, timeout)
        )
        return connection

    def rawHttpRequest(self,
                       method,
                       action,
                       query=None,
                       urlencoded=None,
                       callback=None,
                       timeout=None):
        if method == 'GET':
            url = action if query is None else action + '?' + query
            connection = self.session.get(url,
                                          headers=self.header,
                                          timeout=default_timeout)

        elif method == 'POST':
            connection = self.session.post(action,
                                           data=query,
                                           headers=self.header,
                                           timeout=default_timeout)

        elif method == 'Login_POST':
            connection = self.session.post(action,
                                           data=query,
                                           headers=self.header,
                                           timeout=default_timeout)
            #self.session.cookies.save()

        connection.encoding = 'UTF-8'
        return connection.text

    def login(self,username,password,remember):
        pattern = re.compile(r'^0\d{2,3}\d{7,8}$|^1[34578]\d{9}$')
        if pattern.match(username):
            return self.login_phone(username, password,remember)
        action = 'http://music.163.com/weapi/login?csrf_token='
        text = {
            'username': username,
            'password': hashlib.md5(password.encode()).hexdigest(),
            'rememberLogin': 'true' if remember==True else 'false'
        }
        data = encrypted_request(text)
        try:
            return self.httpRequest('Login_POST', action, data)
        except requests.exceptions.RequestException as e:
            #log.error(e)
            return {'code': 501}
    def login_phone(self,username,password,remember):
        action = 'http://music.163.com/weapi/login/cellphone'
        text = {
            'phone': username,
            'password': hashlib.md5(password.encode()).hexdigest(),
            'rememberLogin': 'true' if remember==True else 'false'
        }
        data = encrypted_request(text)
        try:
            return self.httpRequest('Login_POST', action, data)
        except requests.exceptions.RequestException as e:
            #log.error(e)
            return {'code': 501}
    def weblog(self,sid):
        action = 'http://music.163.com/weapi/feedback/weblog?csrf_token='
        cookies = dict(self.session.cookies)
        data = None
        csrf = ''
        for cookie in cookies:
            if cookie == '__csrf':
                csrf = cookies[cookie]
                #data = {"logs":"[{\"action\":\"play\",\"json\":{\"type\":\"song\",\"id\":"+str(sid)+"}}]","csrf_token":csrf}
                data = {"logs":"[{\"action\":\"play\",\"json\":{\"type\":\"song\",\"wifi\":0,\"download\":0,\"id\":"+str(sid)+",\"time\":320,\"end\":\"ui\"}}]","csrf_token":csrf}
                data = encrypted_request(data)
                action += csrf
        try:
            connection = self.session.post(action,data=data,headers=self.header)
            result = json.loads(connection.text)
            return result
        except:
            return -1
    def send(self,count):
        for i in range(count):
            sid=self.fm()
            print sid,self.weblog(sid)
            time.sleep(1)
    
    def fm(self):
        action = 'http://music.163.com/api/radio/get?limit=1'
        cookies = dict(self.session.cookies)
        data=None
        csrf = ''
        for cookie in cookies:
            if cookie == '__csrf':
                csrf = cookies[cookie]
                data = {'csrf_token': csrf}
                data = encrypted_request(data)
        try:
            connection = self.session.post(action,
                                           data=data,
                                           headers=self.header)
            result = json.loads(connection.text)
            id = result['data'][0]['id']
            return id
            #return result
        except:
            #log.error(e)
            return -1

if __name__ == '__main__':
    n = netease()
    n.login(手机号或者用户名,明文密码,False)
    n.send(10)
