from typing import Iterable
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import Selector
from pathlib import Path
import scrapy
import pandas


class CatalogSpider(scrapy.Spider):
    name = "catalog"
    start_urls = ["https://order-nn.ru/kmo/catalog"]

    category_names = ["Краски и материалы специального назначения",
                      "Краски для наружных работ",
                      "Лаки"]


    def parse(self, response):

        df = pandas.DataFrame([], columns = ['url', 'name', 'price', 'description', 'characteristics'])
        df.to_csv('tovary.csv', sep= ';', mode='w', index= False, header= True)

        for cat_name in self.category_names:
            cat_url = response.xpath('//div[@class="sections-block-level-2-item"]//a[text() = "'+cat_name+'"]/@href').get()
            yield scrapy.Request(response.urljoin(cat_url), callback=self.parse_pages)



    def parse_pages(self, response):

        for item_url in response.xpath('//div[@class="horizontal-product-item-block_3_2"]//a[span[@itemprop="name"]]/@href').getall():
            yield scrapy.Request(response.urljoin(item_url), callback=self.parse_item)

        next_page_url = response.xpath('//li[a[i[@class="fa fa-angle-right"]]]/a/@href').get()
        if next_page_url is not None:
             yield scrapy.Request(response.urljoin(next_page_url), callback=self.parse_pages)
    

    def parse_item(self, response):
        name = response.xpath('//div[h1[@itemprop="name"]]/h1/text()').get()
        price= response.xpath('//div[span[@itemprop="price"]]/span/text()').getall()
        if not price:
            price = [response.xpath('//div[@class="block-3-row element-buy-row"]/div/text()').get()]
        description= response.xpath('//div[@id="block-description"]//text()').getall()
        pdprice = ''
        for pr in price:
            pdprice = pdprice + pr + ' '
        flag = 1
        pddes = ''
        for des in description:
            des = des.replace('\xa0', ' ')
            des = des.replace('    ', '')
            des = des.replace('\r', '')
            if flag:
                des = des.lstrip('\n')
                if des and not des.isspace():
                    flag = 0
                else:
                    des = des.replace('\n', '')
            else:
                if des != des.lstrip('\n'):
                    des = des.lstrip('\n')
                    des = '\n' + des
            if des != des.rstrip('\n'):
                des = des.rstrip('\n')
                des = des + '\n'
                flag = 1
            pddes = pddes + des
        if not flag:
            pddes = pddes + des

        charact = response.xpath('//div[@class="table-character"]//text()').getall()

        df = pandas.DataFrame({'url': [response.url],
                               'name': [name],
                               'price': [pdprice],
                               'description': [pddes],
                               'characteristics': ['-']})
        
        df.to_csv('tovary.csv', sep= ';', mode='a', index= False, header= False, )
