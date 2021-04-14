import ReadRss from 'read_rss'

class PolitifactRSS(ReadRss):

    def transform_entry(self, entry):
        title_parts = entry['title'].split('-')
        return {'_type': title_parts[0].strip(), '_link': entry['link'],
            '_ruling': 'false', '_title': title_parts[0].strip(),
                '_content': entry['summary'], '_source': 'source'}

    def read(self):
        news_feed = feedparser.parse("https://www.politifact.com/rss/all/")
        with jsonlines.open('dataset/politifact_' + datetime.datetime.today().strftime('%y%m%d%H%M%S') + '.json', mode='w', flush = True ) as writer:
            for entry in news_feed.entries:
                

if __name__ == "__main__":
    PolitifactRSS().read()