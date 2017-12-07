import tweepy
from tweepy import OAuthHandler
import os
import sys
import string
from collections import Counter, defaultdict
import itertools
import re
from nltk.corpus import stopwords
import nltk
from operator import itemgetter
from pprint import pprint
import random
import time


nltk.download("stopwords")
consumer_key = os.environ.get("CONSUMER_KEY")
consumer_secret = os.environ.get("CONSUMER_SECRET")
access_token = os.environ.get("ACCESS_TOKEN")
access_secret = os.environ.get("ACCESS_SECRET")
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)


class Tokens:
    def __init__(self):
        self.tokens = None
        self.hashtags = None
        self.bigrams = None


class TwitterScraper:
    def __init__(self):

        # Tokenizing tweets with regex taken from macobonzanini.com
        emoticons_str = r"""
            (?:
                [:=;]
                [oO\-]?
                [D\)\]\(\]/\\OpP]
            )"""

        regex_str = [
            emoticons_str,
            r'<[^>]+>',  # HTML tags
            r'(?:@[\w_]+)',  # @-mentions
            r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)",  # hash-tags
            # URLs
            r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&amp;+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+',

            r'(?:(?:\d+,?)+(?:\.?\d+)?)',  # numbers
            r"(?:[a-z][a-z'\-_]+[a-z])",  # words with - and '
            r'(?:[\w_]+)',  # other words
            r'(?:\S)'  # anything else
        ]

        self.tokens_re = re.compile(
            r'(' + '|'.join(regex_str) + ')', re.VERBOSE | re.IGNORECASE)
        self.emoticon_re = re.compile(
            r'^' + emoticons_str + '$', re.VERBOSE | re.IGNORECASE)
        self.stopwords = stopwords.words(
            'english') + list(string.punctuation) + ['rt', 'via', '…', '’']
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_secret)
        self.api = tweepy.API(auth)
        self.tweets = 0

    def preprocess(self, text, lower=False):
        text = text.translate(non_bmp_map)
        text = "".join(i for i in text if ord(i) < 128)
        tokenized = self.tokens_re.findall(text)
        if lower:
            tokenized = [token if emoticon_re.search(
                token) else token.lower() for token in tokens]
        tokenized = [token for token in tokenized if token.lower()
                     not in self.stopwords]
        words = Tokens()
        words.tokens = tokenized
        words.hashtags = [t for t in words.tokens if t.startswith("#")]
        words.terms = [t for t in words.tokens if not t.startswith(
            "#") and not t.startswith("@")]
        words.bigrams = nltk.bigrams(tokenized)
        return words

    def count(self, token_list):
        counter = Counter()
        for tokens in token_list:
            counter.update(tokens)
        return counter.most_common(5)

    def search(self, query, limit=50):
        tweets = []
        i = 1
        for index, tweet in enumerate(tweepy.Cursor(self.api.search, q=query, rpp=100).items(limit)):
            if tweet.lang == "en":

                tweets.append(tweet)
                self.tweets += 1
        return tweets

    def test_sentiment(self, tweets):
        BASE = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(BASE, "positive-words.txt")) as p_words_f:
            p_words = [word.strip() for word in p_words_f.readlines()]
        with open(os.path.join(BASE, "negative-words.txt")) as n_words_f:
            n_words = [word.strip() for word in n_words_f.readlines()]
        negative_tweets = []
        positive_tweets = []
        neutral_tweets = []
        overall_positive = 0
        overall_negative = 0
        for t in tweets:
            positive = False
            negative = False
            for word in p_words:
                if " " + word + " " in t.text:
                    overall_positive += 1
                    positive = True
                if positive:
                    break
            for word in n_words:
                if " " + word + " " in t.text:
                    # Test to make sure its not a double negative
                    words = t.text.split()
                    n_index = words.index(word)
                    if words[n_index - 1] in n_words:
                        overall_positive += 1
                        positive = True
                    else:
                        overall_negative += 1
                        negative = True
                if negative:
                    break

            if positive and negative:
                neutral_tweets.append(t.text.translate(non_bmp_map))
            elif negative:
                negative_tweets.append(t.text.translate(non_bmp_map))
            elif positive:
                positive_tweets.append(t.text.translate(non_bmp_map))
            else:
                neutral_tweets.append(t.text.translate(non_bmp_map))
        try:
            neu = round(
                ((len(tweets) - (overall_positive + overall_negative)) / len(tweets)) * 100)
            neg = round((overall_negative / len(tweets)) * 100)
            pos = round((overall_positive / len(tweets)) * 100)
            information = ["{}% positive tweets".format(pos),
                           "{}% negative tweets".format(neg),
                           "{}% unopinionated tweets".format(neu),
                           overall_positive / overall_negative]
            return information
        except ZeroDivisionError:
            return False


def scrape(searchq):
    out_str = ""
    if searchq == "":
        quit()
    scraper = TwitterScraper()
    try:
        tweets = scraper.search(searchq, limit=50)
    except tweepy.error.TweepError as e:
        return [str(e)]

    sentiment = scraper.test_sentiment(tweets)
    if not sentiment:
        return ["Could not find any tweets for {}".format(searchq)]
    return sentiment
