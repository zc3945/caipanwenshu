# -*- coding: utf-8 -*-
import json
import re
import datetime
import sys

import scrapy
from scrapy.log import logger

from wenshu.items import WenshuItem, DocInfo

from wenshu.utils.vl5x import getvjkl5

if sys.version_info < (3,):
    from wenshu.utils.docid_v27 import getkey, decode_docid
else:
    from wenshu.utils.docid import getkey, decode_docid


class DocSpider(scrapy.Spider):
    name = 'doc'
    allowed_domains = ['gov.cn']
    start_urls = ['http://gov.cn/']

    def start_requests(self):
        url = 'http://wenshu.court.gov.cn/list/list/?sorttype=1&conditions=searchWord+%E5%90%88%E5%90%8C+++%E5%85%B3%E9%94%AE%E8%AF%8D:%E5%90%88%E5%90%8C'
        yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        """
        根据日期查询分类数量
        :param response:
        :return:
        """
        cookie = response.headers['Set-Cookie'].split(';')[0][6:]
        vjkl5 = getvjkl5(cookie)
        for index in range(1, 2):
            end_day = (datetime.datetime.now() - datetime.timedelta(days=index)).date().__str__()
            start_day = (datetime.datetime.now() - datetime.timedelta(days=index+1)).date().__str__()
            Param = u'上传日期:{} TO {}'.format(start_day, end_day)
            data = {'Param': Param, 'vl5x': vjkl5}
            yield scrapy.FormRequest('http://wenshu.court.gov.cn/List/TreeContent', headers={'Cookie': cookie},
                                     callback=self.get_tree_list, formdata=data,
                                     meta={'cookie': cookie, 'vjkl5': vjkl5, 'Param': Param,
                                           'type_list': [u'法院地域', u'文书类型', u'法院层级',u'审判程序', u'裁判年份', u'一级案由']})

    def get_tree_list(self, response):
        """
        根据分类数量进行循环获取数据量少于200的查询条件，并请求案件信息列表
        :param response:
        :return:
        """
        cookie = response.meta['cookie']
        vjkl5 = response.meta['vjkl5']
        try:
            html = json.loads(json.loads(response.text))
        except BaseException as exc:
            logger.error(exc)
            yield response.request
        else:
            for d in html:
                if d['Key'] == response.meta['type_list'][0]:
                    for dd in d['Child']:
                        if not dd['Key'] or not dd['IntValue']:
                            continue
                        Param = response.meta['Param'] + u',{}:{}'.format(d['Key'], dd['Key'])
                        data = {'Param': Param, 'Index': '1', 'Page': '20', 'Order': u'法院层级', 'Direction': 'asc', 'vl5x': vjkl5}
                        if dd['IntValue'] <= 200 or len(response.meta['type_list']) == 1:
                            yield scrapy.FormRequest('http://wenshu.court.gov.cn/List/ListContent', headers={'Cookie': cookie},
                                                     callback=self.get_doc_list, formdata=data,
                                                     meta={'cookie': cookie, 'vjkl5': vjkl5, 'Param': Param})
                        else:
                            yield scrapy.FormRequest('http://wenshu.court.gov.cn/List/TreeContent', headers={'Cookie': cookie},
                                                     callback=self.get_tree_list, formdata=data,
                                                     meta={'cookie': cookie, 'vjkl5': vjkl5, 'Param': Param,
                                                           'type_list': response.meta['type_list'][1:]})

    def get_doc_list(self, response):
        """
        实现翻页，解析doc_id，返回案件基本信息
        :param response:
        :return:
        """
        cookie = response.meta['cookie']
        vjkl5 = response.meta['vjkl5']
        Param = response.meta['Param']
        try:
            result = json.loads(json.loads(response.text))
        except BaseException as exc:
            logger.error(exc)
            yield response.request
        else:
            if not response.meta.get('key'):
                format_key_str = result[0]['RunEval'].encode('utf-8')
                key = getkey(format_key_str).encode('utf-8')
                page_count = int(result[0]['Count']) // 20 if int(result[0]['Count']) // 20 == 0 else int(result[0]['Count']) // 20 + 1
                for page in range(2, page_count + 1):
                    data = {'Param': Param, 'Index': str(page), 'Page': '20', 'Order': u'法院层级', 'Direction': 'asc', 'vl5x': vjkl5}
                    yield scrapy.FormRequest('http://wenshu.court.gov.cn/List/ListContent', headers={'Cookie': cookie},
                                             callback=self.get_doc_list, formdata=data,
                                             meta={'cookie': cookie, 'vjkl5': vjkl5, 'Param': Param, 'type_list': [], 'key': key})
            else:
                key = response.meta['key']

            for x in result[1:]:
                iid = x[u'文书ID'].encode('utf-8')
                docid = decode_docid(iid, key)
                item = DocInfo()
                item['doc_id'] = docid
                item['doc_name'] = x[u'案件名称']
                item['doc_date'] = x[u'裁判日期']
                yield item

                # yield scrapy.Request('http://wenshu.court.gov.cn/CreateContentJS/CreateContentJS.aspx?DocID={}'.format(docid),
                #                      callback=self.get_info)

    def get_info(self, response):
        """
        获取案件文书详情信息
        :param response:
        :return:
        """
        caseinfo = re.findall('stringify\((.*?)\);', response.text)[0]
        RelateInfo = re.findall('RelateInfo: (\[.*?\]),', response.text)[0]
        LegalBase = re.findall('LegalBase: (\[.*?\])\};', response.text)[0]
        jsonHtmlData = re.findall('var jsonHtmlData = "(\{.*?\}";)', response.text)[0]
        d1 = json.loads(caseinfo)
        d2 = re.findall('name: "(.*?)".*?value: "(.*?)"', RelateInfo)
        d3 = LegalBase
        d4 = json.loads(jsonHtmlData[:-2].replace('\\', ''))
        item = WenshuItem()
        item['doc_id'] = d1[u'文书ID']
        item['name'] = d1[u'案件名称']
        item['caseinfo'] = caseinfo
        item['RelateInfo'] = RelateInfo
        item['LegalBase'] = LegalBase
        item['jsonHtmlData'] = jsonHtmlData[:-2].replace('\\', '')
        yield item
