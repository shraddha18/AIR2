#!/usr/bin/python
from __future__ import print_function
import codecs
import nltk
from nltk.corpus import stopwords
import re
import string
import sys
import cgitb; cgitb.enable()
import cgi
import io, os, subprocess, wave
import math, audioop, collections
import json, platform, time
import urllib

try: # try to use python2 module
    from urllib2 import Request, urlopen
except ImportError: # otherwise, use python3 module
    from urllib.request import Request, urlopen


_IS_PYTHON_3 = sys.version_info.major == 3

stop_words = stopwords.words('english')

# The low end of shared words to consider
LOWER_BOUND = .20

# The high end, since anything above this is probably SEO garbage or a
# duplicate sentence
UPPER_BOUND = .90


def u(s):
    """Ensure our string is unicode independent of Python version, since Python 3 versions < 3.3 do not support the u"..." prefix"""
    if _IS_PYTHON_3 or type(s) == unicode:
        return s
    else:
        # not well documented but seems to work
        return codecs.unicode_escape_decode(s)[0]


def is_unimportant(word):
    """Decides if a word is ok to toss out for the sentence comparisons"""
    return word in ['.', '!', ',', ] or '\'' in word or word in stop_words


def only_important(sent):
    """Just a little wrapper to filter on is_unimportant"""
    return filter(lambda w: not is_unimportant(w), sent)


def compare_sents(sent1, sent2):
    """Compare two word-tokenized sentences for shared words"""
    if not len(sent1) or not len(sent2):
        return 0
    return len(set(only_important(sent1)) & set(only_important(sent2))) / ((len(sent1) + len(sent2)) / 2.0)


def compare_sents_bounded(sent1, sent2):
    """If the result of compare_sents is not between LOWER_BOUND and
    UPPER_BOUND, it returns 0 instead, so outliers don't mess with the sum"""
    cmpd = compare_sents(sent1, sent2)
    if cmpd <= LOWER_BOUND or cmpd >= UPPER_BOUND:
        return 0
    return cmpd


def compute_score(sent, sents):
    """Computes the average score of sent vs the other sentences (the result of
    sent vs itself isn't counted because it's 1, and that's above
    UPPER_BOUND)"""
    if not len(sent):
        return 0
    return sum(compare_sents_bounded(sent, sent1) for sent1 in sents) / float(len(sents))


def summarize_block(block):
    """Return the sentence that best summarizes block"""
    if not block:
        return None
    sents = nltk.sent_tokenize(block)
    word_sents = list(map(nltk.word_tokenize, sents))
    d = dict((compute_score(word_sent, word_sents), sent)
             for sent, word_sent in zip(sents, word_sents))
    return d[max(d.keys())]


def find_likely_body(b):
    """Find the tag with the most directly-descended <p> tags"""
    return max(b.find_all(), key=lambda t: len(t.find_all('p', recursive=False)))


class Summary(object):

    def __init__(self, url, article_html, title, summaries):
        self.url = url
        self.article_html = article_html
        self.title = title
        self.summaries = summaries

    def __repr__(self):
        return u('Summary({}, {}, {}, {})').format(repr(self.url), repr(self.article_html), repr(self.title), repr(self.summaries))

    def __unicode__(self):
        return u('{} - {}\n\n{}').format(self.title, self.url, '\n'.join(self.summaries))

    def __str__(self):
        if _IS_PYTHON_3:
            return self.__unicode__()
        else:
            return self.__unicode__().encode('utf8')


def summarize_blocks(blocks):
    summaries = [re.sub('\s+', ' ', summarize_block(block) or '').strip()
                 for block in blocks]
    # deduplicate and preserve order
    summaries = sorted(set(summaries), key=summaries.index)
    return [u(re.sub('\s+', ' ', summary.strip())) for summary in summaries if any(c.lower() in string.ascii_lowercase for c in summary)]


def summarize_page(url):
    import bs4
    import requests

    html = bs4.BeautifulSoup(requests.get(url).text)
    for a in html.find_all('a'):
        html.a.decompose()
    b = find_likely_body(html)
    summaries = summarize_blocks(map(lambda p: p.text, b.find_all('p')))
    return Summary(url, b, html.title.text if html.title else None, summaries)


def summarize_text(text, block_sep='\n\n', url=None, title=None):
    return Summary(url, None, title, summarize_blocks(text.split(block_sep)))


if __name__ == '__main__':
    #if len(sys.argv) > 1:
    form = cgi.FieldStorage()    
    linkz = form.getvalue("linkname")
    try:
        exampleSearch = linkz
        encoded = urllib.quote(exampleSearch)
        rawData = urllib.urlopen('http://ajax.googleapis.com/ajax/services/search/web?v=1.0&rsz=5&q='+encoded).read()
        jsonData = json.loads(rawData)
        searchResults = jsonData['responseData']['results']

        for er in searchResults:
            title = er['title']
            link = er['url']
            #print title
            if 'Wikipedia' in title:
                thisanswer = link
    except LookupError:
        print ("error error!")    
    resm =(summarize_page(thisanswer))
    fh = open("summary.txt", "w")
    summaries = "jsidushudv"
    fh.writelines(str(resm))
    fh.close()
    #print ('Content-Type: text/html; charset=UTF-8')
    #output = header + html.format(result=result)
    #print ('resm')
    print ("Content-Type: text/html")
    print ("")
    print ("<html>")
    print ("<head>")
    print ("""
    <link rel="stylesheet" href="../htdocs/air.css">
    """)
    print ("""
    <link href='http://fonts.googleapis.com/css?family=Lato:400,700' rel='stylesheet' type='text/css'>
    """)
    print ("</head>")
    print ("<body bgcolor=#13232f>")
    print ("<font color=white>")
    print ("<centre>")
    print ("<h1><u>Summary</u></h1>\n")
    print ("</centre>")
    print ("<p>")
    print (str(resm)+"\n") 
    print ("<p>")
    #print ("<button value='Download'/>")
    print ("</font>")
    print ("</body>")
    print ("</html>")
    #print ("Content-type: text/html")
    #print with open('Button.html') as f:
    #print f.read()
    sys.exit(0)

    #print('Usage summarize.py <URL>')
    #sys.exit(1)
