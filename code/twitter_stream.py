from twython import Twython, TwythonRateLimitError
from dotenv import load_dotenv
import os
from util.twitter_crawler import TwitterCrawler
import jsonlines
import datetime
load_dotenv()

class TimelineCrawler(TwitterCrawler):

    def twitter_timeline(self, screen_name, tag = None):
        return self.twitter_result(lambda: self.twitter.cursor(self.twitter.get_user_timeline, screen_name = screen_name), tag)

    def load_timeline(self, screen_name):
        with jsonlines.open("dataset/twitter_%s_%s_3.json" % (screen_name,  datetime.datetime.today().strftime('%y%m%d%H%M%S')), mode='w', flush = True ) as writer:
            for tweet in self.twitter_timeline(screen_name):
                writer.write(tweet)

if __name__ == "__main__":
    TimelineCrawler().load_timeline('@cnn')