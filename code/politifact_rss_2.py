from util.read_rss import ReadRSS
from dotenv import load_dotenv
from util.util import make_news_id

class PolitifactRSS(ReadRSS):

    def transform_entry(self, entry):
        title_parts = entry['title'].split('-')
        title = title_parts[1].strip()
        return {'news_id': make_news_id("politifact", entry['link']), '_type': title_parts[0].strip(), '_link': entry['link'],
            '_ruling': 'false', '_title': title,
                '_content': entry['summary'], '_source': self.get_source_link(title)}
                
if __name__ == "__main__":
    load_dotenv()
    PolitifactRSS('politifact').read('https://www.politifact.com/rss/all/')