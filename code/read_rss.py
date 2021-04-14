import feedparser
import jsonlines
import datetime

class ReadRSS:

    def transform_entry(self, entry):
        return entry

    def read(self, url, name_prefix):
        news_feed = feedparser.parse(url)
        with jsonlines.open("dataset/%s_" % name_prefix + datetime.datetime.today().strftime('%y%m%d%H%M%S') + '.json', mode='w', flush = True ) as writer:
            for entry in news_feed.entries:
                writer.write(transform_entry(entry))