import feedparser
import jsonlines
import datetime
import os
from serpapi import GoogleSearch

class ReadRSS:

    def __init__(self, name):
        self.name = name

    def get_source_link(self, title):
        search = GoogleSearch({
            "q": title, 
            "api_key": os.getenv('SERPAPI_KEY')
        })
        results = search.get_dict()['organic_results']
        # filter out gossipcop links
        results = list(filter(lambda r: not self.name in r['link'], results))
        return results[0]['link']

    def transform_entry(self, entry):
        return entry

    def read(self, url, limit = 1000):
        news_feed = feedparser.parse(url)
        with jsonlines.open("dataset/%s_rss_" % self.name + datetime.datetime.today().strftime('%y%m%d%H%M%S') + '_2.json', mode='w', flush = True ) as writer:
            for entry in news_feed.entries:
                writer.write(self.transform_entry(entry))
                limit = limit - 1
                if limit == 0:
                    break