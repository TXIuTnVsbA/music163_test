# -*- coding: utf-8 -*-
import threading,Queue
import mp3play,requests,json,os,base64,binascii,hashlib,re,time
from Crypto.Cipher import AES
from pprint import pprint
from threading import Timer
q = Queue.Queue()
T=None
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

        # 私人FM
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
            name = result['data'][0]['name']
            artists=[]
            for tmp in result['data'][0]['artists']:
                artists.append(tmp['name'])
            return id,name,artists
        except:
            #log.error(e)
            return -1

        # like
    def like(self, songid, like=True, time=25, alg='itembased'):
        action = 'http://music.163.com/api/radio/like?alg={}&trackId={}&like={}&time={}'.format(  # NOQA
            alg, songid, 'true' if like else 'false', time)

        try:
            data = self.httpRequest('GET', action)
            if data['code'] == 200:
                return data
            else:
                return -1
        except requests.exceptions.RequestException as e:
            #log.error(e)
            return -1

        # FM trash
    def trash(self, songid, time=25, alg='RT'):
        action = 'http://music.163.com/api/radio/trash/add?alg={}&songId={}&time={}'.format(  # NOQA
            alg, songid, time)
        try:
            data = self.httpRequest('GET', action)
            if data['code'] == 200:
                return data
            else:
                return -1
        except requests.exceptions.RequestException as e:
            #log.error(e)
            return -1
    def songs_detail_new_api(self, music_ids, bit_rate=320000):
        action = 'http://music.163.com/weapi/song/enhance/player/url?csrf_token='  # NOQA
        cookies = dict(self.session.cookies)
        csrf = ''
        for cookie in cookies:
            if cookie == '__csrf':
                csrf = cookies[cookie]
        action += csrf
        data = {'ids': "["+music_ids+"]", 'br': bit_rate, 'csrf_token': csrf}
        connection = self.session.post(action,
                                       data=encrypted_request(data),
                                       headers=self.header, )
        result = json.loads(connection.text)
        return result
    def id_to_url(self,music_ids):
        try:
            return self.songs_detail_new_api(str(music_ids))['data'][0]['url']
        except:
            return -1

def func():
    q.put(['next'])

class MyThread(threading.Thread):
    def __init__(self,queue):
        threading.Thread.__init__(self)

    def run(self):
        global T
        n = netease()
        mp3 = None
        list = None
        while True:
            tmp = q.get()
            str_tmp = str(tmp[0]).lower()
            if str_tmp == 'exit':
                break
            if str_tmp == 'next':
                try:
                    mp3.stop()
                    T.cancel()
                except:
                    pass
                list = n.fm()
                print list
                url = n.id_to_url(list[0])
                print url
                req = n.like(list[0])
                print(req)
                mp3=mp3play.load(url)
                mp3.play()
                T = Timer(mp3.seconds(), func)
                T.start()
            if str_tmp == 'trash':
                try:
                    mp3.stop()
                    T.cancel()
                except:
                    pass
                req = n.trash(list[0])
                print(req)
                req = n.like(songid=list[0], like=False)
                print(req)
                list = n.fm()
                print(list)
                url = n.id_to_url(list[0])
                print(url)
                req = n.like(list[0])
                print(req)
                mp3 = mp3play.load(url)
                mp3.play()
                T = Timer(mp3.seconds(), func)
                T.start()
            if str_tmp == 'login':
                n.login(tmp[1], tmp[2], tmp[3])
            if str_tmp == 'stop':
                try:
                    mp3.stop()
                    T.cancel()
                except:
                    pass

if __name__ == '__main__':
    MyThread(q).start()
    q.put(['login','手机号','明文密码',False])
    while True:
        input_str = raw_input().lower()
        if input_str == 'exit' or input_str == 'stop':
            q.put(['stop'])
            q.put(['exit'])
            break
        if input_str == 'next' or input_str == 'play':
            q.put(['next'])
        if input_str == 'trash' or input_str == 'del' or input_str == 'delete':
            q.put(['trash'])
        if input_str == 'help':
            print('\tplay or next\r\n\tpause or unpause\r\n\ttrash or delete or del\r\n\tstop or exit\r\n')
