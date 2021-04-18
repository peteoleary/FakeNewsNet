from twython import Twython, TwythonRateLimitError
from dotenv import load_dotenv
import os
from util.twitter_crawler import TwitterCrawler
import jsonlines
import datetime
load_dotenv()

class TimelineCrawler(TwitterCrawler):

    def twitter_timeline(self, screen_name, tag = None):
        return self.get_user_timeline_g(screen_name, tag)

    def write_one_tweet(self, writer, tweet):
        for retweets_page in self.get_retweets_g(tweet['id']):
            self.write_one_tweet_page(writer, retweets_page)
        for reply_page in self.get_replies_g(tweet['user']['id'], tweet['id']):
            self.write_one_tweet_page(writer, reply_page)
        writer.write(tweet)

    def write_one_tweet_page(self, writer, tweet_page):
        for tweet in list(tweet_page):
            self.write_one_tweet(writer, tweet)

    def load_timeline(self, screen_name):
        depth_limit = os.getenv('DEPTH_LIMIT', 10)
        with jsonlines.open("dataset/twitter_%s_%s_3.json" % (screen_name,  datetime.datetime.today().strftime('%y%m%d%H%M%S')), mode='w', flush = True ) as writer:
            for tweet_page in self.twitter_timeline(screen_name):
                self.write_one_tweet_page(writer, tweet_page)
                depth_limit -= 1
                if depth_limit == 0: break

if __name__ == "__main__":
    TimelineCrawler().load_timeline('cnn')