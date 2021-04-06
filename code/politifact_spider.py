import scrapy
from urllib import parse
from bs4 import BeautifulSoup
import datetime

class PolitifactItem(scrapy.Item):
    _type = scrapy.Field()
    _link = scrapy.Field()
    _ruling = scrapy.Field()

class PolitifactSpider(scrapy.Spider):
    name = 'politifact'
    start_urls = [
        'https://www.politifact.com/factchecks/list/?ruling=pants-fire',
        'https://www.politifact.com/factchecks/list/?ruling=false'
    ]
    custom_settings = {
        'DOWNLOAD_DELAY': .5,
        'DEPTH_LIMIT': 10,
        'FEED_FORMAT': 'jsonlines',
        'FEED_URI': 'dataset/politifact_' + datetime.datetime.today().strftime('%y%m%d%H%M%S') + '.json'
    }


    def parse(self, response):
        url_split = parse.urlsplit(response.url)
        q_params = dict(parse.parse_qsl(url_split.query))
        links = response.css('li.o-listicle__item')

        for link in links:
            item_selector = link.css('a')
            type_soup = BeautifulSoup(item_selector[0].extract())
            link_soup = BeautifulSoup(item_selector[1].extract())
            yield PolitifactItem(_type = type_soup.text.strip(), 
                _link = "%s://%s%s" % (url_split.scheme, url_split.hostname, link_soup.find('a').attrs['href']), 
                _ruling = q_params['ruling'])

        if (not 'page' in q_params.keys()):
            q_params['page'] = '1'

        q_params['page'] = int(q_params['page']) + 1

        next_page = "%s://%s%s?%s" % (url_split.scheme, url_split.hostname, url_split.path, parse.urlencode(q_params))
        yield response.follow(next_page, self.parse)