# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class WenshuItem(scrapy.Item):

    doc_id = scrapy.Field()
    name = scrapy.Field()
    caseinfo = scrapy.Field()
    RelateInfo = scrapy.Field()
    LegalBase = scrapy.Field()
    jsonHtmlData = scrapy.Field()


class DocInfo(scrapy.Item):
    doc_id = scrapy.Field()
    doc_name = scrapy.Field()
    doc_date = scrapy.Field()


