import pathlib
import jsonlines 
import sys
from util.twitter_api_v2 import TwitterAPIV2
import pathlib
import re
import dateparser
from dotenv import load_dotenv
load_dotenv()

graph = {}
node_num = 1

COLORS = {
    'news': '#77ab59',
    'retweet': '#87cefa',
    'reply': '#735144'
}

def get_color(node_type):
    return COLORS.get(node_type, '#d2b4d7')

def get_parent(tweet):
    if '_news_id' in tweet:
        return tweet['_news_id']
    if 'conversation_id' in tweet:
        if tweet['conversation_id'] == tweet['id']:
            return None
        return tweet['conversation_id']
    if is_retweet(tweet):
        retweet = tweet.get('retweeted_status') or tweet.get('referenced_tweets')
        return retweet['id']
    print("can't find parent for %s" % tweet['id'])
    return None
    

def add_to_graph(tweet):
    global graph
    global node_num
    if tweet['id'] in graph:
        print("tweet id %s already in graph" % tweet['id'])
        return
    tweet['_parent_id'] = None
    tweet['_children'] = []
    tweet['_node_num'] = node_num
    node_num += 1
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
    text = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', text)
    text = re.sub('[^\w\.]', ' ', text ).lower()
    text = text.replace("\\n", " ")
    return  text

def output_examples(p, screen_name, label):
    with (open_writer(p, 'examples')) as writer:
        for root_id in graph_roots():
            root = graph[root_id]
            result = {
                'id': root['id'],
                'labels': label,
                'title': root['title'],
                'content':  normalize_text(root['text']),
                'created_at': dateparser.parse(root['created_at']).strftime('%Y-%m-%d'),
                'comments': []
            }
            for child in root['_children']:
                if 'text' in child and not is_retweet(child):
                    result['comments'] += [{'comment': normalize_text(child['text']), 'username': child['user']['username']}]
            writer.write(result)

def should_output(node):
    return len(node['_children']) > 0

def graph_roots():
    return filter(lambda id: graph[id]['_parent_id'] is None and not is_retweet(graph[id]) and should_output(graph[id]), graph)

def make_nodes_and_edges(tweet):
    nodes = [{
        "id": tweet['_node_num'],
        "link": tweet.get('link'),
        'tweet_id': tweet['id'],
        'label': tweet['_node_num'],
        'color': get_color(tweet.get('_type')), # TODO: set color based on node type
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
                'news_id': root['id'],
                'graph' : {
                    'nodes': nodes,
                    'edges': edges
                }
            }
            writer.write(result)

def process_flat_tweet_file(json_file_path, screen_name, label):
    with jsonlines.open(json_file_path) as reader:
        for item in reader:
            add_to_graph(item)
    traverse_graph()
    p = pathlib.PurePath(json_file_path)
    output_examples(p, screen_name, label)
    output_propagation_graph(p, screen_name)

if __name__ == "__main__":
    process_flat_tweet_file(sys.argv[1], sys.argv[2], sys.argv[3])