from urllib import parse
from bs4 import BeautifulSoup
import requests
import jsonlines
import sys
import time
import pathlib
from twython import Twython
from dotenv import load_dotenv
import os
import corenlp

load_dotenv()  # take environment variables from .env.

class ContentCrawler:

    def __init__(self):
        self.twitter = Twython(os.getenv('TWITTER_APP_KEY'), access_token=os.getenv('TWITTER_ACCESS_TOKEN'))
        self.corenlp_client = corenlp.CoreNLPClient(annotators="tokenize ssplit pos lemma ner depparse".split())
    #{
        # "_title": "“Government imposed lockdowns do NOT reduce [COVID-19] cases or stop spikes.”",
        # "_content": "Blah blah\n",
        # "_source": "https://twitter.com/J_GallagherAD3/status/1334616185195749376",
        # "_type": "James Gallagher",
        # "_link": "https://www.politifact.com/factchecks/2020/dec/16/james-gallagher/yes-government-shutdowns-help-slow-covid-19-when-c/",
        # "_ruling": "false"
    #}

    def follow_archive_link(self, url):
        page_html = requests.get(url,  headers={'User-Agent': 'Mozilla/5.0'})
        page_soup = BeautifulSoup(page_html.text)
        return None

    def canonical_url(self, url):
        url_split = parse.urlsplit(url)
        without_query = parse.SplitResult(url_split.scheme, url_split.netloc, url_split.path, '', url_split.fragment).geturl()
        switcher = {
            "archive.ph": lambda: self.follow_archive_link(url),
            "www.facebook.com": lambda: url,
            "www.tiktok.com": lambda: without_query
        }
        return switcher.get(url_split.hostname, lambda: url)()

    def check_twitter_result(self, search_result):
        if len(search_result['statuses']) > 0:
            for tweet in search_result['statuses']:
                yield "http://www.twitter.com/%s/status/%s" % (tweet['user']['screen_name'], tweet['id'])

    def crawl_content(self, item):
        # remove special characters
        # search for URL
        # shorten Twitter URL
        title_search = self.twitter.search(q = item['_title'])
        print("title_search: " + "\n".join(self.check_twitter_result(title_search)))
        canonical_url = self.canonical_url(item['_source'])
        if canonical_url:
            url_search = self.twitter.search(q = "url:%s" % parse.quote(canonical_url))
            print("url_search: " + "\n".join(self.check_twitter_result(url_search)))
        return title_search

    def crawl_content_with_old_code(self, json_file_path):
        # TODO: transform data and try out old code!   
        return

    # TODO: this function can be moved to a shared file
    def crawl_content_from_file(self, json_file_path):
        p = pathlib.PurePath(json_file_path)
        with jsonlines.open(p.with_name(p.stem + '_details.json'), mode='w', flush = True ) as writer:
            with jsonlines.open(json_file_path) as reader:
                for item in reader:
                    link = item['_link']
                    try:
                        page_contents = self.crawl_content(item)
                        page_contents.update(item)
                        # TODO: add proper logger here
                        # print("writing page %s" % page_contents['_link'])
                        writer.write(page_contents)
                    except Exception as e:
                        print("error %s scraping page %s" % (e, link))
                    time.sleep(.25)

if __name__ == "__main__":
    ContentCrawler().crawl_content_from_file(sys.argv[1])