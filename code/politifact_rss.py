import feedparser
import jsonlines
import datetime

class PolitifactRSS:
    def read(self):
        news_feed = feedparser.parse("https://www.politifact.com/rss/all/")
        with jsonlines.open('dataset/politifact_' + datetime.datetime.today().strftime('%y%m%d%H%M%S') + '.json', mode='w', flush = True ) as writer:
            for entry in news_feed.entries:
                title_parts = entry['title'].split('-')
                writer.write({'_type': title_parts[0].strip(), '_link': entry['link'],
                    '_ruling': 'false', '_title': title_parts[0].strip(),
                        '_content': entry['summary'], '_source': 'source'})

if __name__ == "__main__":
    PolitifactRSS().read()