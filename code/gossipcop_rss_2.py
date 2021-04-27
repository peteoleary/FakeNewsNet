from util.read_rss import ReadRSS
from dotenv import load_dotenv
from util.util import make_news_id

class GossipCopRSS(ReadRSS):

    def transform_entry(self, entry):
        
        return {'_news_id': make_news_id('gossipcop', entry['link']), '_tag': entry['tags'][0]['term'], '_link': entry['link'],
            '_ruling': 'false', '_title': entry['title'],
                '_content': entry['summary'], '_source': self.get_source_link(entry['title']),
                '_date': entry['published'] }
                
if __name__ == "__main__":
    load_dotenv()
    GossipCopRSS("gossipcop").read("https://www.gossipcop.com/feed/")