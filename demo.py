# coding:utf-8
import json
import time
import random
import base64
import datetime


import requests
from lxml import etree
from Crypto.Cipher import DES3


class Des(object):

    def pad(self, s):
        return s + (DES3.block_size - len(s) % DES3.block_size) * chr(DES3.block_size - len(s) % DES3.block_size)

    def unpad(self, s):
        return s[0:-ord(s[-1])]

    def encrypt(self, text, key):
        text = self.pad(text)
        iv = datetime.datetime.now().strftime('%Y%m%d').encode()
        cryptor = DES3.new(key, DES3.MODE_CBC, iv)
        x = len(text) % 8
        if x != 0: text = text + '\0' * (8 - x)
        self.ciphertext = cryptor.encrypt(text.encode('utf-8'))
        return base64.standard_b64encode(self.ciphertext).decode("utf-8")

    def decrypt(self, text, key):
        iv = datetime.datetime.now().strftime('%Y%m%d').encode()
        cryptor = DES3.new(key, DES3.MODE_CBC, iv)
        de_text = base64.standard_b64decode(text)
        plain_text = cryptor.decrypt(de_text)
        out = self.unpad(plain_text.decode('utf-8'))
        return out


class Demo(object):

    def __init__(self, api, cookie=''):
        self.api = api
        self.cookie = cookie

    def make_ciphertext(self):
        timestamp = str(int(time.time() * 1000))
        salt = ''.join([random.choice('0123456789qwertyuiopasdfghjklzxcvbnm') for _ in range(24)])
        iv = datetime.datetime.now().strftime('%Y%m%d')
        des = Des()
        enc = des.encrypt(timestamp, salt)
        strs = salt + iv + enc
        result = []
        for i in strs:
            result.append(bin(ord(i))[2:])
            result.append(' ')
        return ''.join(result[:-1])

    def start_page(self):
        headers = {
            # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            # "Host": "wenshu.court.gov.cn",
            # "Referer": "http://wenshu.court.gov.cn/website/wenshu/181217BMTKHNT2W0/index.html",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
        }
        url = 'http://wenshu.court.gov.cn/website/wenshu/181217BMTKHNT2W0/index.html'
        with requests.get(url, headers=headers) as req:
            req.raise_for_status()
            cookie_80s = req.cookies.get('HM4hUBT0dDOn80S')
            assert cookie_80s, '文书网异常，80s获取失败'
            html = req.text
        root = etree.HTML(html)
        meta = root.xpath('//meta[last()]/@content')[0]
        js_txt = root.xpath('//script[@r="m"]/text()')[0]
        with requests.post(self.api, json={'meta': meta, 'js_txt': js_txt}) as req:
            req.raise_for_status()
            cookie_80t = req.json()['cookie']
            assert cookie_80t, '80t生成失败'
            print(cookie_80t)
        self.cookie = f'HM4hUBT0dDOn80S={cookie_80s};HM4hUBT0dDOn80T={cookie_80t};HM4hUBT0dDOnenable=true'

    def get_list(self):
        if not self.cookie:
            print('没有正确生成cookie')
            return
        headers = {
            'Cookie': self.cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",
        }

        token = ''.join([random.choice('0123456789qwertyuiopasdfghjklzxcvbnm') for _ in range(24)])
        post_data = {
            'sortFields': 's50:desc',
            'ciphertext': self.make_ciphertext(),
            'pageNum': 1,
            'pageSize': 5,
            'queryCondition': [],
            'cfg': 'com.lawyee.judge.dc.parse.dto.SearchDataDsoDTO@queryDoc',
            '__RequestVerificationToken': token,
        }
        url = 'http://wenshu.court.gov.cn/website/parse/rest.q4w'
        with requests.post(url, headers=headers, data=post_data) as req:
            req.raise_for_status()
            assert req.text, "文书网接口异常"
            des = Des()
            result = des.decrypt(req.json()['result'], req.json()['secretKey'])
            print(result)
        first_doc_id = json.loads(result)['queryResult']['resultList'][0]['rowkey']
        self.get_info(first_doc_id)

    def get_info(self, doc_id):
        print('-------详情页-------')
        headers = {
            'Cookie': self.cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",
        }

        token = ''.join([random.choice('0123456789qwertyuiopasdfghjklzxcvbnm') for _ in range(24)])
        post_data = {
            'docId': doc_id,
            'ciphertext': self.make_ciphertext(),
            'cfg': 'com.lawyee.judge.dc.parse.dto.SearchDataDsoDTO@docInfoSearch',
            '__RequestVerificationToken': token,
        }
        url = 'http://wenshu.court.gov.cn/website/parse/rest.q4w'
        with requests.post(url, headers=headers, data=post_data) as req:
            req.raise_for_status()
            assert req.text, "文书网接口异常"
            des = Des()
            result = des.decrypt(req.json()['result'], req.json()['secretKey'])
            print(result)


if __name__ == '__main__':
    api = 'http://118.24.27.218:8012/wenshu'
    sss = Demo(api=api)
    sss.start_page()
    sss.get_list()
