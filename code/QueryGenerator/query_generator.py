import spacy
import re
from nltk.tokenize import word_tokenize
from argparse import ArgumentParser


# name entity extraction
nlp = spacy.load("en_core_web_sm")
# remove stop_words
STOPWORDS = nlp.Defaults.stop_words
# These labels are from nlp.pipe_labels['ner']
ENTITIES_KEEP_LIST = ["ORG", "LOC", "PRODUCT", "PERSON"]

def get_name_entities(input_text):
   doc = nlp(
      u'{}'.format(input_text))
   for ent in doc.ents:
      print(ent.text, ent.start_char, ent.end_char, ent.label_)
   entity_list = [ent.text for ent in doc.ents if any([ent.label_ == ent_type for ent_type in ENTITIES_KEEP_LIST])]
   return entity_list


def get_text_within_quotes(input_text):
   quotes_string = re.findall('["“](.*?)["”]', input_text)
   return quotes_string

def remove_negation_words(input_text):
   doc = nlp(u"{}".format(input_text))
   keep_words = [tok.text for tok in doc if tok.dep_ != "neg"]
   return " ".join(keep_words)

def remove_stop_words(input_text):
   text_tokens = word_tokenize(input_text)
   tokens_without_sw = [word for word in text_tokens if not word in STOPWORDS]
   return " ".join(tokens_without_sw)

def query_in_one(input_text):
   # improved from https://github.com/mdepak/fake_news_crawler
   if input_text.count('“') > 0 or input_text.count('"') > 0:
      # keep the quoated text
      quotes_text = get_text_within_quotes(input_text)
      named_entities = get_name_entities(input_text)
      search_terms = []
      for term in quotes_text:
         search_terms.append((term, input_text.find(term)))

      for term in named_entities:
          search_terms.append((term, input_text.find(term)))

      sorted_search_terms = sorted(search_terms, key=lambda tup: tup[1])

      search_terms = []

      for term in sorted_search_terms:
          search_terms.append(term[0])

      search_query = " ".join(search_terms)
   else:
      # remove stop_words and negation text
      text = remove_negation_words(input_text)
      text = remove_stop_words(text)
      search_query = text

   return search_query

def file_main(args):
   input_text_list = open(args.input_file,'r').readlines()
   query_list = [query_in_one(i.strip()) for i in input_text_list]
   with open(args.output_file, 'w') as f1:
      for line in query_list:
         f1.write(line+"\n")


if __name__ == '__main__':
   parser = ArgumentParser()
   parser.add_argument("--input_text", type=str, default="'Apple will release new IPAD this year at USA' mick told me")
   parser.add_argument("--input_file", type=str, help="Input file, separated by line", default=None)
   parser.add_argument("--output_file", type=str, help="Output file, separated by line", default=None)
   args = parser.parse_args()
   assert (args.input_file is None) + (args.output_file is None) != 2, "Please set the --input_file and --output_file at the same time"
   if args.input_file is not None:
      file_main(args)
   else:
      print(query_in_one(args.input_text))



