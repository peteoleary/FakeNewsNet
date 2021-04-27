import requests
import sys
from util.twitter_crawler import TwitterCrawler
import time
from dotenv import load_dotenv
import os
import re
from util.util import open_read_write_json_file, flatten
from urllib import parse
from QueryGenerator.query_generator import query_in_one

load_dotenv()  # take environment variables from .env.

class NewsContentCrawler(TwitterCrawler):

    def handle_one_item(self, item, writer):
        # make fake tweet from news article content
        news_id = item['_news_id']
        writer.write({
            'id': news_id,
            'title': item['_title'],
            'text': item['_content'],
            'created_at': item['_date'],
            'link': item['_link'],   # not a real tweet field but we want to include it for the prop graph
            'type': 'news'
        })
        # write all items in tweets array
        flattened_list = flatten(self.crawl_content(item))
        for tweet in flattened_list:
            # find dangling conversation_ids/referenced/retweets and follow them
            # if tweet.get('conversation_id') != tweet.get('id'):
                # self.expand_conversation(writer, tweet.get('conversation_id'))
            # link this tweet back to the original story
            tweet['_news_id'] = news_id
            self.write_one_tweet(writer, tweet)
        
        # don't write anything
        return None

    def canonical_url(self, url):
        url_split = parse.urlsplit(url)
        without_query = parse.SplitResult(url_split.scheme, url_split.netloc, url_split.path, '', url_split.fragment).geturl()
        switcher = {
            "www.tiktok.com": lambda: without_query
        }
        return switcher.get(url_split.hostname, lambda: url)()

    def transform_title(self, title_string):
        ann = self.corenlp_client.annotate(title_string)
        filtered_word_list = list(filter(None, map(lambda t: t.word if t.pos in ['NN', 'NNS', 'VBZ', 'NNP', 'VB', 'JJ'] else None, ann.sentence[0].token)))
        return " ".join(filtered_word_list)

    def print_search_result(self, search_name, search_result):
        for tweet in search_result:
            print("%s %s: http://www.twitter.com/%s/status/%s" % (search_name, tweet['created_at'], tweet['user']['username'], tweet['id']) + "\n")


    def crawl_content(self, item):
        # title = self.transform_title(item['_title'])
        title = re.sub('\W+',' ', item['_title'] )
        title = query_in_one(title)
        title_search_results, next_token = self.twitter().get_query(title, None)
        self.print_search_result("title_search", title_search_results)
        canonical_url = self.canonical_url(item['_source'])
        if canonical_url:
            url_search_results, next_token = self.twitter().get_query("url:\"%s\"" % parse.quote(canonical_url), None)
            self.print_search_result("url_search", url_search_results)
            if (len(url_search_results) > 0):
                title_search_results.append(url_search_results)
        return title_search_results

    def crawl_content_from_file(self, json_file_path):
        open_read_write_json_file(json_file_path, "3", self.handle_one_item)
                    

if __name__ == "__main__":
    NewsContentCrawler().crawl_content_from_file(sys.argv[1])