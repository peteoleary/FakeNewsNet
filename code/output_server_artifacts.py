import pathlib
import jsonlines 
import sys
from util.twitter_api_v2 import TwitterAPIV2
import pathlib
import re
from dotenv import load_dotenv
load_dotenv()

graph = {}

def get_parent(tweet):
    if 'conversation_id' in tweet:
        if tweet['conversation_id'] == tweet['id']:
            return None
        return tweet['conversation_id']
    if is_retweet(tweet):
        retweet = tweet.get('retweeted_status') or tweet.get('referenced_tweets')
        return retweet['id']
    raise Exception("can't find parent for %s" % tweet['id'])
    

def add_to_graph(tweet):
    if tweet['id'] in graph:
        print("tweet id %s already in graph" % tweet['id'])
        return
    tweet['_parent_id'] = None
    tweet['_children'] = []
    tweet['_node_num'] = len(graph) + 1
    graph[str(tweet['id'])] = tweet    

def traverse_graph():
    for tweet_id in list(graph):
        tweet = graph[tweet_id]
        parent_id = get_parent(tweet)
        tweet['_parent_id'] = parent_id
        if parent_id is not None:
            if str(parent_id) not in graph:
                print("parent_id %s not in graph" % parent_id)
                tweets, next_token = TwitterAPIV2().get_tweet_v2(parent_id, None)
                add_to_graph(tweets[0])
            child_list = graph[str(parent_id)]['_children']
            if not isinstance(child_list, list):
                raise Exception()
            child_list += [tweet]

def open_writer(p, stage):
    return jsonlines.open(p.with_name(p.stem + "_%s.json" % stage), mode='w', flush = True )

def is_retweet(tweet):
    return 'retweeted_status' in tweet or tweet['text'].startswith('RT')

def normalize_text(text):
    return re.sub('\W+', ' ', text ).lower()

def output_examples(p, screen_name):
    with (open_writer(p, 'examples')) as writer:
        for root_id in graph_roots():
            root = graph[root_id]
            result = {
                'id': screen_name + '_' + str(root['id']),
                'comments': [],
                'labels': 1,
                'content': root['text'],
                'created_at': root['created_at']
            }
            for child in root['_children']:
                if 'text' in child and not is_retweet(child):
                    result['comments'] += [{'comment': normalize_text(child['text'])}]
            writer.write(result)

def graph_roots():
    return filter(lambda id: graph[id]['_parent_id'] is None and not is_retweet(graph[id]), graph)

def make_nodes_and_edges(tweet):
    nodes = [{
        "id": tweet['_node_num'],
        'tweet_id': tweet['id'],
        'label': tweet['_node_num'],
        'color': "#d2b4d7", # TODO: set color based on node type
        }]
    edges = []
    if '_parent_id' in tweet and tweet['_parent_id'] is not None:
        edges += [{'from': graph[str(tweet['_parent_id'])]['_node_num'], 'to': tweet['_node_num']}]
    for child in tweet['_children']:
        child_nodes, child_edges = make_nodes_and_edges(child)
        nodes += child_nodes
        edges += child_edges
    return nodes, edges


def output_propagation_graph(p, screen_name):
    with (open_writer(p, 'propagation')) as writer:
        for root_id in graph_roots():
            root = graph[root_id]
            nodes, edges = make_nodes_and_edges(root)
            result = {
                'news_id': screen_name + '_' + root['id'],
                'graph' : {
                    'nodes': nodes,
                    'edges': edges
                }
            }
            writer.write(result)

def open_read_write_json_file(json_file_path, screen_name):
    with jsonlines.open(json_file_path) as reader:
        for item in reader:
            add_to_graph(item)
    traverse_graph()
    p = pathlib.PurePath(json_file_path)
    output_examples(p, screen_name)
    output_propagation_graph(p, screen_name)

if __name__ == "__main__":
    open_read_write_json_file(sys.argv[1], sys.argv[2])