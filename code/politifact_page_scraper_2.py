from urllib import parse
from bs4 import BeautifulSoup
import requests
import jsonlines
import sys
import time
import pathlib

class PolitifactPageScraper:

    def scrape_page(self, item):
        crawl_url = requests.get(item['_link'], headers={'User-Agent': 'Mozilla/5.0'})
        crawl_url.raise_for_status()

        page_soup = BeautifulSoup(crawl_url.text)

        # get page title
        title = page_soup.select('.o-stage__inner .m-statement__quote')[0].text.strip()
        # get page content
        content = page_soup.select('article.m-textblock')[0].text
        # get page links
        sources = page_soup.select('#sources .m-superbox__content a')
        # get page date
        page_date = page_soup.select('.m-author__date')[0].text

        if (len(sources) > 0):
            source = sources[0]['href']
        else:
            source = None

        return {'_title': title, '_content': content, '_source': source, '_date': page_date}

    def scrape_pages_from_file(self, json_file_path):
        p = pathlib.PurePath(json_file_path)
        with jsonlines.open(p.with_name(p.stem + '_contents.json'), mode='w', flush = True ) as writer:
            with jsonlines.open(json_file_path) as reader:
                for obj in reader:
                    try:
                        page_contents = self.scrape_page(obj)
                        page_contents.update(obj)
                        # TODO: add proper logger here
                        print("writing page %s" % page_contents['_link'])
                        writer.write(page_contents)
                    except Exception as e:
                        print("error %s scraping page %s" % (e, page_contents['_link']))
                    time.sleep(.25)

if __name__ == "__main__":
    PolitifactPageScraper().scrape_pages_from_file(sys.argv[1])