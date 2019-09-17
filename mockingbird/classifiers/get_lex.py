import csv
import heapq

from collections import Counter
from nltk.tokenize import TweetTokenizer


# Read lexicon into dictionary from `filename`, return dictionary
def read_lex(filename):
    lex = {}
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            lex[row['term']] = float(row['weight'])
    return lex


# Load lexicons to save time later
gender_lex = read_lex('./classifiers/lexica/gender.csv')
age_lex = read_lex('./classifiers/lexica/age.csv')
uni_lex = read_lex('./classifiers/lexica/sent_uni.csv')
bi_lex = read_lex('./classifiers/lexica/sent_bi.csv')
pol_lex = read_lex('./classifiers/lexica/polarity.csv')
sub_lex = read_lex('./classifiers/lexica/subjectivity.csv')


def name_to_lex(lex_name):
    if lex_name == 'gender':
        lex = [gender_lex]
    elif lex_name == 'age':
        lex = [age_lex]
    elif lex_name == 'sentiment':
        lex = [uni_lex, bi_lex]
    elif lex_name == 'polarity':
        lex = [pol_lex]
    elif lex_name == 'subjectivity':
        lex = [sub_lex]
    else:
        raise Exception("Invalid lex_name", lex_name)
    return lex


# Classify the text specified by `text` with lexicon `lex`. Returns the score and the `n` tokens that contributed most
# towards and against the ultimate label. If `include_weights`, largest and smallest include words and weights. Else,
# only words are returned. `biggest` is the largest weight and `smallest` the smallest, regardless of class. For the
# negative class (i.e. male or younger), `smallest` contributes most to that label and `largest` the most against it.
def lex_classify(text, lex_name, n=5, include_weights=False):
    lex_list = name_to_lex(lex_name)

    # All have at least unigram lexicon
    lex = lex_list[0]

    score = lex['_intercept'] if '_intercept' in lex else 0.0
    tokenizer = TweetTokenizer()  # Should we use Happier Fun Tokenizer instead?
    tokenized = tokenizer.tokenize(text)
    size = float(len(tokenized))
    word_weights = []
    c = Counter(tokenized)
    for word in c:
        if word in lex:
            if lex_name == 'subjectivity':
                weight = (lex[word] - 0.5) * (c[word]/size)
            else:
                weight = lex[word] * (c[word] / size)
            word_weights.append((word, weight))
            score += weight

    # If sentiment, also do bigrams
    if lex_name == 'sentiment':
        bigrams = []
        for i in range(len(tokenized)-1):
            bigrams.append(tokenized[i] + ' ' + tokenized[i+1])

        size = float(len(bigrams))
        c = Counter(bigrams)
        lex_2 = lex_list[1]
        for word in c:
            if word in lex:
                weight = lex_2[word] * (c[word] / size)
                word_weights.append((word, weight))
                score += weight

    # Get `n` words that contributed most. Remove all words that actually counted in the other direction.
    largest = [x for x in heapq.nlargest(n, word_weights, lambda x: x[1]) if x[1] >= 0] or None
    smallest = [x for x in heapq.nsmallest(n, word_weights, lambda x: x[1]) if x[1] <= 0] or None
    if not include_weights:
        largest = [x[0] for x in largest] if largest is not None else None
        smallest = [x[0] for x in smallest] if smallest is not None else None

    return score, largest, smallest


# Return the `n` smallest and largest weights from lexicon `lex`. If `include_weights`, largest and smallest include
# words and weights. Else, only words are returned.
def get_lex_extremes(lex_name, n=5, include_weights=False):
    lex = name_to_lex(lex_name)[0]

    # Rescale subjectivity
    if lex_name == 'subjectivity':
        largest = [x for x in heapq.nlargest(n, lex, lambda x: lex[x]) if lex[x] >= 0.5] or None
        smallest = [x for x in heapq.nsmallest(n, lex, lambda x: lex[x]) if lex[x] <= 0.5] or None
    else:
        largest = [x for x in heapq.nlargest(n, lex, lambda x: lex[x]) if lex[x] >= 0] or None
        smallest = [x for x in heapq.nsmallest(n, lex, lambda x: lex[x]) if lex[x] <= 0] or None
    if include_weights:
        largest = [(x, lex[x]) for x in largest] if largest is not None else None
        smallest = [(x, lex[x]) for x in smallest] if smallest is not None else None
    return largest, smallest


# Given a list of tweets `tweets`, sort from lowest to highest value of the lexicon `lex` and return a list of tuples
# where the first element in the tuple is the tweet, the second is its classification value, and the third is a list of
# the `n` words that contributed most towards this label.
def by_tweet(tweets=None, lex_name=None, n=3):
    data = []
    # Get classification and explanatory words
    for tweet in tweets:
        s, large, small = lex_classify(tweet, lex_name, n=n)
        data.append((tweet, s, large, small))

    # Sort based on classification
    data.sort(key=lambda x: x[1])

    # If in top half of results, keep largest explanatory words. Else, keep smallest.
    list_len = len(data)
    if len(tweets) >= 10:
        data = [(x[0], x[1], x[3]) if ind < list_len/2 else (x[0], x[1], x[2]) for ind, x in enumerate(data)]
    # If too small, duplicate data with reversed explanations
    else:
        data = [(x[0], x[1], x[3])for ind, x in enumerate(data)] + [(x[0], x[1], x[2]) for ind, x in enumerate(data)]
    return data



