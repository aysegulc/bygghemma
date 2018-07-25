# -*- coding: utf-8 -*-
import scrapy
import json

extract_list_extract_columns = [
    u'ProductUrl',
    u'RecommendedListPrice',
    u'RecommendedListPriceString',
    u'PercentCheaper',
    u'PresentationUnit',
    u'ProductId',
    u'ListPrice',
    u'ListPriceString',
    u'DisplayName',
    u'IsInStock',
    u'BrandLogoUrl',
]
details_extract_columns = [
    u'name',
    u'description',
    u'image',
]

product_main_columns = [
    u'Brand',
    u'CompareArtGrp',
    u'ImageName',
    u'ImageUrlBase',
    u'LimitOtherBrands',
    u'Series',
    u'Videos',
]

product_columns = [
    u'ProductImage',
    u'ExtraImages',
    u'ArtNbr',
    u'LowestQuantity',
    u'MultiQuantityFactor',
    u'SalesUnit',
]

product_attribute_columns = [
    u'Brand',
    u'CompareArtGrp',
    u'ImageName',
    u'ImageUrlBase',
    u'Series',
    u'Videos',
]


class BygghemmaSpider(scrapy.Spider):
    name = 'bygghemma'
    allowed_domains = ['bygghemma.se']
    #start_urls = ['http://bygghemma.se/']

    def start_requests(self):
        #request = scrapy.Request('https://www.bygghemma.se/golv-och-vagg/golv/laminatgolv/', self.parse_page)
        request = scrapy.Request(
            'https://www.bygghemma.se/apptuscategory/productsjson/'
            '?path=%2Fgolv-och-vagg%2Fgolv%2Flaminatgolv%2F&page=1&'
            'size=36&searchPhrase=&appliedFilters=sort%3D2&order=2',
            self.parse_page)
        request.meta['page'] = '1'
        yield request

    def parse_page(self, response):
        page_dict = json.loads(response.text)
        product_list = page_dict['jsonProducts']
        for product in product_list:
            item = dict()
            for i in extract_list_extract_columns:
                if not isinstance(product.get(i, ''), unicode):
                    item[i] = str(product.get(i, '')).strip()
                else:
                    item[i] = product.get(i, '').strip()
            item['ProductUrl'] = response.urljoin(item.get('ProductUrl', ''))
            item_request = scrapy.Request(item['ProductUrl'], callback=self.parse_product)
            item_request.meta['item'] = item
            yield item_request

        if response.meta['page'] == '1':

            size = 36
            number_of_products = page_dict[u'numberOfHits']
            number_of_pages = number_of_products//size + 1 if number_of_products % size != 0 else number_of_products//size

            for i in xrange(2, number_of_pages + 1):
                page_request = scrapy.Request(response.url.replace('&page=1', '&page=' + str(i)),
                                              self.parse_page)
                page_request.meta['page'] = str(i)
                yield page_request

    def parse_product(self, response):
        item = response.meta['item']
        details = response.xpath(
            '//script[contains(text(),"@type") and contains(text(),"Product")]/'
            'text()').extract_first(default='')
        details_dict = json.loads(details)
        for i in details_extract_columns:
            item[i] = details_dict.get(i, '').strip()

        product_data = response.xpath(
            '//script[contains(text(),"var productData") and contains('
            'text(),"ImageName")]/text()').extract_first(default='')
        try:
            product_main_dict = json.loads(product_data.split('var productData =')[-1].split(';')[0])
        except Exception:
            product_main_dict = dict()

        for i in product_main_columns:
            if not isinstance(product_main_dict.get(i, ''), unicode):
                item[i] = str(product_main_dict.get(i, '')).strip()
            else:
                item[i] = product_main_dict.get(i, '').strip()

        product_dict = product_main_dict.get(u'Product', {}) if product_main_dict.get(u'Product', {}) is not None else {}

        for i in product_columns:
            item[i] = str(product_dict.get(i, '')).strip()

        attribute_list = product_dict.get(u'Attributes', []) if product_dict.get(u'Attributes', []) is not None else []

        for attribute in attribute_list:
            key = attribute.get(u'Id', '')
            if key and key is not None:
                value = ' '.join([attribute.get(u'Caption', ''), attribute.get(u'Value', ''), attribute.get(u'Unit', '')]).strip()
                item[key.strip()] = value

        item['pdfDocuments'] = ', '.join(response.xpath(
            '//*[contains(@class,"productDescription_pdfs")]//a/@href').extract()).strip()

        description_list = response.xpath(
            '//*[contains(@class,"productDescription_textContainer")]//text()').extract()
        description_text_list = [i.strip() for i in description_list if i.strip() and i.strip() != u'L\xe4s mer']

        item['longDescription'] = '\n\n'.join(description_text_list).strip()
        item['breadcrumbs'] = ''.join(response.xpath(
            '//*[contains(@class,"breadcrumb_item")]/text()').extract()).strip()
        yield item
