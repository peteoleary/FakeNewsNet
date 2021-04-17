from twython import Twython, TwythonRateLimitError
import os
import dateparser
import time
from inspect import signature
import requests
from os import getenv
import json

class TwitterCrawler:
    def __init__(self):
            self.twitter = Twython(os.getenv('TWITTER_APP_KEY'), access_token=os.getenv('TWITTER_BEARER_TOKEN'))

    def twitter_api_v_2(self, query):
        headers = {"Authorization": "Bearer %s" % getenv('TWITTER_BEARER_TOKEN')}
        return requests.get("https://api.twitter.com/2/%s" % query, headers=headers)

    def get_tweet_replies(self, user_id, tweet_id):
        expansions = "author_id,entities.mentions.username,geo.place_id,in_reply_to_user_id,referenced_tweets.id,referenced_tweets.id.author_id"
        tweet_fields = "author_id,conversation_id,created_at,entities,geo,id,in_reply_to_user_id,referenced_tweets,text"
        user_fields = "name,username"
        query = "tweets/search/recent?query=conversation_id:%s&expansions=%s&tweet.fields=%s&user.fields=%s" % (tweet_id, expansions, tweet_fields, user_fields)
        tweet_response = self.twitter_api_v_2(query)
        if tweet_response.status_code == 200:
            tweet_data = json.loads(tweet_response.text)
            if 'data' in tweet_data:
                # TODO: check next_token for paging
                tweet_data['meta']['next_token']
                replies_list = []
                for tweet in tweet_data['data']:
                    if 'includes' in tweet_data and 'users' in tweet_data['includes']:
                        filtered_users = list(filter(lambda user: user['id'] == tweet['author_id'], tweet_data['includes']['users']))
                        if len(filtered_users) > 0:
                            tweet['user'] = {'id': filtered_users[0]['id'], 'screen_name': filtered_users[0]['username']}
                    replies_list.append(tweet)
                return self.map_tweet_list(replies_list)
        else:
            print(tweet_response.text)
        return []


    def get_retweets_and_replies(self, tweet):
        retweets =  self.twitter_result(lambda: self.twitter.get_retweets(id = tweet['id']))
        # retweets =  self.twitter.get_retweets(id = tweet['id'])
        replies = self.get_tweet_replies(tweet['user']['id'], tweet['id'])
        return retweets + replies

    def print_tweet_url(self, screen_name, id):
        print("http://www.twitter.com/%s/status/%s" % (screen_name, id))

    def map_tweet(self, tweet, merge_hash = {}):
        tweet.update(merge_hash)
        self.print_tweet_url(tweet['user']['screen_name'], tweet['id'])
        return tweet

    def map_tweet_list(self, tweet_list, tag = None):
        print("mapping tweet_list len=%d tag=%s" % (len(tweet_list), tag))
        return list(map(lambda tweet: self.map_tweet(tweet, {'_tag': tag, '_replies': self.get_retweets_and_replies(tweet)}), tweet_list))

    def twitter_search(self, search_string, tag = None):
        return self.twitter_result(self, lambda: self.twitter.search(q = search_string), tag)

    def twitter_result(self, operation, result_tag = None):
        search_result = None
        while search_result is None:
            try:
                sig = signature(operation)

                # print("%s %s" % (operation, sig.parameters.values()))
                search_result = operation()
                time.sleep(.25)

            except TwythonRateLimitError as e:
                try_sleep = int(e.retry_after) - time.time_ns()/1000000000
                print("Twitter rate limit, sleeping for %d seconds" % try_sleep)
                time.sleep(try_sleep)

        if 'statuses' in search_result:
            search_result = search_result['statuses']

        return self.map_tweet_list(search_result, result_tag)

    def parse_date(self, date_string):
        date_string = date_string.replace('+0000', '')
        new_date  = dateparser.parse(date_string)
        return new_date.strftime('%y%m%d%H%M%S')