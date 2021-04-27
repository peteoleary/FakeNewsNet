import dateparser
from util.twitter_api_v2 import TwitterAPIV2

# handles bridging Twitter data and our own internal data format, mostly by decorating Twitter objects
# with attributes which are common across all data sources, iterating through pages of results and
# recursing into lists to get all retweets and replies for each object
# all public methods with suffix _g return generators 
class TwitterCrawler:
    def __init__(self):
            self.__twitter = TwitterAPIV2()

    def twitter(self):
        return self.__twitter

    def get_retweets_g(self, tweet_id):
        return self.__generator(self.__twitter.get_retweets(tweet_id))

    def get_replies_g(self, user_id, tweet_id):
        return self.__generator(self.__twitter.get_replies(user_id, tweet_id))

    # decorate Tweet objects
    def __map_tweet(self, tweet, merge_hash = {}):
        tweet.update(merge_hash)
        self.print_tweet_url(tweet['user']['screen_name'], tweet['id'])
        return tweet

    # decorate a list of tweet objects
    def __map_tweet_list(self, tweet_list, tag = None):
        print("mapping tweet_list len=%d tag=%s" % (len(tweet_list), tag))
        return list(map(lambda tweet: self.map_tweet(tweet, {'_tag': tag, '_replies': self.get_retweets_and_replies(tweet)}), tweet_list))

    def parse_date(self, date_string):
        date_string = date_string.replace('+0000', '')
        new_date  = dateparser.parse(date_string)
        return new_date.strftime('%y%m%d%H%M%S')

    def __generator(self, func):
        next_token = None
        while True:
            result, next_token = func(next_token)
            yield result
            if next_token is None: break 

    def get_user_timeline_g(self, screen_name, tag):
        user = self.__twitter.get_user_by_screen_name(screen_name)
        return self.__generator(self.__twitter.get_user_timeline(user['id']))

    def write_one_tweet(self, writer, tweet):
        for retweets_page in self.get_retweets_g(tweet['id']):
            self.write_one_tweet_page(writer, retweets_page, "retweet")
        for reply_page in self.get_replies_g(tweet['user']['id'], tweet['id']):
            self.write_one_tweet_page(writer, reply_page, "reply")
        writer.write(tweet)

    def write_one_tweet_page(self, writer, tweet_page, page_type = None):
        page_list = list(tweet_page)
        print("page len = %d" % len(page_list), flush=True)
        for tweet in page_list:
            if page_type:
                tweet['_type'] = page_type
            self.write_one_tweet(writer, tweet)

    def expand_conversation(self, writer, conversation_id):
        tweet, next_token = self.__twitter.get_tweet_v2(conversation_id, None)
        if len(tweet) > 0:
            self.write_one_tweet(writer, tweet[0])
