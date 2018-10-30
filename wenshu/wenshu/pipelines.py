# -*- coding: utf-8 -*-

import pymysql

from wenshu.items import WenshuItem


class WenshuPipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, WenshuItem):
            sql = 'INSERT into doc_info (docid, name, caseinfo, RelateInfo, LegalBase, jsonHtmlData) values (%s, %s, %s, %s, %s, %s)'
            self.cur.execute(sql, (item['doc_id'], item['name'], item['caseinfo'], item['RelateInfo'], item['LegalBase'], item['jsonHtmlData']))
        else:
            sql = 'insert into doc(doc_id, doc_name, doc_date) values (%s, %s, %s)'
            self.cur.execute(sql, (item['doc_id'], item['doc_name'], item['doc_date']))
        self.client.commit()

    def open_spider(self, spider):
        self.client = pymysql.Connection(host='127.0.0.1', user='root', password='root',
                                         database='wenshu', port=3306, charset='utf8')
        self.cur = self.client.cursor()

    def close_spider(self, spider):
        self.cur.close()
        self.client.close()
