from urllib import parse
from bs4 import BeautifulSoup
import requests
import jsonlines
import sys
import time
import pathlib
from twython import Twython, TwythonRateLimitError
from dotenv import load_dotenv
import os
import corenlp
from datetime import datetime
import re

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
        # this doesn't work as archive pages are blocked by Captcha
        return None

    def canonical_url(self, url):
        url_split = parse.urlsplit(url)
        without_query = parse.SplitResult(url_split.scheme, url_split.netloc, url_split.path, '', url_split.fragment).geturl()
        switcher = {
            "archive.ph": lambda: self.follow_archive_link(url),
            "www.tiktok.com": lambda: without_query
        }
        return switcher.get(url_split.hostname, lambda: url)()

    def twitter_result(self, search_string, tag = None):
        search_result = None
        while search_result is None:
            try:
                search_result = self.twitter.search(q = search_string)
            except TwythonRateLimitError as e:
                try_sleep = int(e.retry_after) - time.time_ns()/1000000000
                print("Twitter rate limit, sleeping for %d seconds" % try_sleep)
                time.sleep(try_sleep)

        return list(map(lambda tweet: {
                '_tweet_user': tweet['user']['screen_name'], 
                '_tweet_id': tweet['id'],
                '_tag': tag
            }, search_result['statuses']))

    def transform_title(self, title_string):
        ann = self.corenlp_client.annotate(title_string)
        filtered_word_list = list(filter(None, map(lambda t: t.word if t.pos in ['NN', 'NNS', 'VBZ', 'NNP', 'VB', 'JJ'] else None, ann.sentence[0].token)))
        return " ".join(filtered_word_list)

    def print_search_result(self, search_name, search_result):
        for tweet in search_result:
            print("%s: http://www.twitter.com/%s/status/%s" % (search_name, tweet['tweet_user'], tweet['tweet_id']) + "\n")

    def crawl_content(self, item):
        # remove special characters
        # search for URL
        # shorten Twitter URL
        # title = self.transform_title(item['_title'])
        title = re.sub('\W+',' ', item['_title'] )
        title_search_results = self.twitter_result(title, 'title')
        print("title: " + title)
        self.print_search_result("title_search", title_search_results)
        # canonical_url = self.canonical_url(item['_source'])
        canonical_url = item['_source']
        if canonical_url:
            url_search_results = self.twitter_result("url:%s" % parse.quote(canonical_url), 'url')
            self.print_search_result("url_search", url_search_results)
            if (len(url_search_results) > 0):
                title_search_results.append(url_search_results)
        return title_search_results

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
                        item['tweets'] = page_contents
                        # TODO: add proper logger here
                        # print("writing page %s" % page_contents['_link'])
                        writer.write(item)
                    except Exception as e:
                        print("error %s scraping page %s" % (e, link))
                    time.sleep(.5)

if __name__ == "__main__":
    ContentCrawler().crawl_content_from_file(sys.argv[1])