import requests
from os import getenv
import json 
import time
from util.currying import curry
from twython import Twython, TwythonRateLimitError

# hide some of the complexity of the V2 API
# all public methods return an array of objects and a pagination token
# unless otherwise specified

class TwitterAPIV2:
    def __init__(self):
        self.__twitter_bearer_token = getenv('TWITTER_BEARER_TOKEN')
        self.__headers = {"Authorization": "Bearer %s" % getenv('TWITTER_BEARER_TOKEN')}
        self.__sleep = float(getenv("TWITTER_SLEEP", .25))

    def __twitter_api_get(self, query, version = '2'):
        return requests.get("https://api.twitter.com/%s/%s" % (version, query), headers=self.__headers)

    def __print_tweet_url(self, screen_name, id):
        print("http://www.twitter.com/%s/status/%s" % (screen_name, id))

    # handle an api call to Twitter with rate limiting, unwrapping and merging the response
    def __twitter_result_v2(self, query, next_token, result_tag = None, next_token_key = 'pagination_token'):
        twitter_result = None
        while twitter_result is None:
            # print("%s %s" % (operation, sig.parameters.values()))
            if next_token is not None:
                query += "&%s=%s" % (next_token_key, next_token)
            twitter_result = self.__twitter_api_get(query)
            if twitter_result.status_code == 200:
                tweet_data = json.loads(twitter_result.text)
                if 'data' in tweet_data:
                    if 'meta' in tweet_data:
                        next_token = tweet_data['meta'].get('next_token')
                    replies_list = []
                    for tweet in tweet_data['data']:
                        if 'includes' in tweet_data and 'users' in tweet_data['includes']:
                            filtered_users = list(filter(lambda user: user['id'] == tweet['author_id'], tweet_data['includes']['users']))
                            if len(filtered_users) > 0:
                                tweet['user'] = filtered_users[0]
                        replies_list.append(tweet)
                    return replies_list, next_token
                else:
                    # TODO: check for {"meta":{"result_count":0}}
                    pass
            elif twitter_result.status_code == 429:
                try_sleep = int(twitter_result.headers['x-rate-limit-reset']) - time.time_ns()/1000000000
                print("Twitter rate limit, sleeping for %d seconds" % try_sleep)
                time.sleep(try_sleep)
            else:
                raise Exception(twitter_result.text)
            
            time.sleep(self.__sleep)

        return [], None

    def __twitter_result(self, query, next_token, result_tag = None):
        twitter_result = None
        while twitter_result is None:
            try:
                twitter_result = self.__twitter_api_get(query, version = '1.1')
            except TwythonRateLimitError as e:
                try_sleep = int(e.retry_after) - time.time_ns()/1000000000
                print("Twitter rate limit, sleeping for %d seconds" % try_sleep)
                time.sleep(try_sleep)

        if twitter_result.status_code == 200:
            tweet_data = json.loads(twitter_result.text)
        else:
            tweet_data = []

        time.sleep(self.__sleep)

        return tweet_data, None

    def add_stuff(self):
        expansions = "author_id,entities.mentions.username,geo.place_id,in_reply_to_user_id,referenced_tweets.id,referenced_tweets.id.author_id"
        tweet_fields = "author_id,conversation_id,created_at,geo,id,in_reply_to_user_id,referenced_tweets,text"
        user_fields = "name,username"
        return "expansions=%s&tweet.fields=%s&user.fields=%s" % (expansions, tweet_fields, user_fields)

    @curry
    def get_replies(self, user_id, tweet_id, next_token):
        query = "tweets/search/recent?query=conversation_id:%s&%s" % (tweet_id, self.add_stuff())
        return self.__twitter_result_v2(query, next_token, next_token_key = 'next_token')
        
    # TODO: don't know how to do this with V2?
    @curry
    def get_retweets_v2(self, tweet_id, next_token):
        query = "tweets/%s?%s" % (tweet_id, self.add_stuff())
        return self.__twitter_result_v2(query, next_token)

    @curry
    def get_retweets(self, tweet_id, next_token):
        query = "statuses/retweets/%s.json?trim_user=false" % tweet_id
        return self.__twitter_result(query, next_token)

    @curry
    def get_user_timeline(self, user_id, next_token):
        return self.__twitter_result_v2("users/%s/tweets?%s" % (user_id, self.add_stuff()), next_token)

    def get_user_by_screen_name(self, screen_name):
        result, next = self.__twitter_result_v2("users/by?usernames=%s" % screen_name, None)
        return result[0] if len(result) > 0 else None