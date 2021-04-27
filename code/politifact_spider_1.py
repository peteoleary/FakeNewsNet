import scrapy
from urllib import parse
from bs4 import BeautifulSoup
import datetime
from dotenv import load_dotenv
import os
from util.util import make_news_id

load_dotenv()  # take environment variables from .env.

class PolitifactItem(scrapy.Item):
    _tag = scrapy.Field()
    _link = scrapy.Field()
    _ruling = scrapy.Field()
    _news_id = scrapy.Field()

class PolitifactSpider(scrapy.Spider):
    name = 'politifact'
    start_urls = [
        'https://www.politifact.com/factchecks/list/?ruling=pants-fire',
        'https://www.politifact.com/factchecks/list/?ruling=false'
    ]
    custom_settings = {
        'DOWNLOAD_DELAY': os.getenv('DOWNLOAD_DELAY'),
        'DEPTH_LIMIT': os.getenv('DEPTH_LIMIT'),
        'FEED_FORMAT': 'jsonlines',
        'FEED_URI': 'dataset/politifact_' + datetime.datetime.today().strftime('%y%m%d%H%M%S') + '_1.json'
    }


    def parse(self, response):
        url_split = parse.urlsplit(response.url)
        q_params = dict(parse.parse_qsl(url_split.query))
        links = response.css('li.o-listicle__item')

        for link in links:
            item_selector = link.css('a')
            type_soup = BeautifulSoup(item_selector[0].extract())
            link_soup = BeautifulSoup(item_selector[1].extract())
            link = "%s://%s%s" % (url_split.scheme, url_split.hostname, link_soup.find('a').attrs['href'])
            yield PolitifactItem(_tag = type_soup.text.strip(), 
                _link = link, _ruling = q_params['ruling'], _news_id = make_news_id('politifact', link))

        if (not 'page' in q_params.keys()):
            q_params['page'] = '1'

        q_params['page'] = int(q_params['page']) + 1

        next_page = "%s://%s%s?%s" % (url_split.scheme, url_split.hostname, url_split.path, parse.urlencode(q_params))
        yield response.follow(next_page, self.parse)