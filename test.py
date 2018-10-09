# coding:'utf-8'

import requests
import json

from docid import getkey, decode_docid
from vl5x import getvjkl5

if __name__ == '__main__':
    url = 'http://wenshu.court.gov.cn/list/list/?sorttype=1&conditions=searchWord+%E5%90%88%E5%90%8C+++%E5%85%B3%E9%94%AE%E8%AF%8D:%E5%90%88%E5%90%8C'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}
    res = requests.get(url, headers=headers)
    cookie = res.headers.get('Set-Cookie').split(';')[0][6:]
    data = {'Param': u'关键词:合同', 'Index': '1', 'Page': '20', 'Order': u'法院层级',
            'Direction': 'asc', 'vl5x': getvjkl5(cookie)}
    url = 'http://wenshu.court.gov.cn/List/ListContent'
    headers['Cookie'] = 'vjkl5={}'.format(cookie)
    headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    res = requests.post(url, headers=headers, data=data)
    data = json.loads(res.json())
    k = data[0]['RunEval'].encode('utf-8')
    key = getkey(k).encode('utf-8')
    for x in json.loads(res.json())[1:]:
        iid = x[u'文书ID'].encode('utf-8')
        docid = decode_docid(iid, key)
        print x[u'案号'], docid
