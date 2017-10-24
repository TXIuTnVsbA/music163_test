# -*- coding: utf-8 -*-
import os.path
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import requests,json,os,base64,binascii,hashlib,re
from Crypto.Cipher import AES

session = requests.Session()
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
            'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36',
}
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

def songs_detail_new_api(music_ids, bit_rate=320000):
    action = 'http://music.163.com/weapi/song/enhance/player/url?csrf_token='  # NOQA
    cookies = dict(session.cookies)
    csrf = ''
    for cookie in cookies:
        if cookie == '__csrf':
            csrf = cookies[cookie]
    action += csrf
    data = {'ids': "[" + music_ids + "]", 'br': bit_rate, 'csrf_token': csrf}
    connection = session.post(action,
                                   data=encrypted_request(data),
                                   headers=header)
    result = json.loads(connection.text)
    return result

def id_to_url(music_ids):
    try:
        return songs_detail_new_api(str(music_ids))['data'][0]['url']
    except:
        return -1

from tornado.options import define, options
define("port", default=8000, help="run on the given port", type=int)

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        data='''<form action="/test" method="post" enctype="application/x-www-form-urlencoded">
<p><input name="arg1" type="text" /></p>
<input type="submit">'''
        self.write(data)
    def write_error(self, status_code, **kwargs):
        self.write('''<p>Fuck Error.</p><p>%d</p><a href="./">Back</a>''' % status_code)

class Test(tornado.web.RequestHandler):
    def post(self):
        arg1=self.get_argument('arg1','None')
        try:
            tmp=arg1.split("/")[-1].split("?")[-1].split("&")[0].split("=")[1]
            tmp1=id_to_url(tmp)
            data = '''<a href="{echo1}">Download</a>'''.format(echo1=tmp1)
            #data = '''<audio src="{echo1}" controls="controls"><a href="{echo1}">Download</a></audio>'''.format(echo1=tmp1)
        except:
            data = '''<p>Error,Argument: </p><p>{echo1}</p><a href="./">Back</a>'''.format(echo1=arg1)
        self.write(data)
    def write_error(self, status_code, **kwargs):
        self.write('''<p>Fuck Error.</p><p>%d</p><a href="./">Back</a>''' % status_code)

if __name__ == '__main__':
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[
            (r'/', IndexHandler),
            (r'/test', Test)
        ]
    )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
