from django.db import models
from django.core.validators import int_list_validator
from classifiers.get_lex import lex_classify
from textblob import Blobber, TextBlob
from textblob.sentiments import NaiveBayesAnalyzer
from classifiers.translators import translator
import re

NBC_BLOBBER = Blobber(analyzer=NaiveBayesAnalyzer())  # Use the same analyzer to avoid training multiple times

GENDER_TRANSLATOR = translator('gender')
AGE_TRANSLATOR = translator('age')


# Get translation for all combos and return
def translate(tweet, attr):
    sub = re.split('([.!?,;] )', tweet)

    if attr == 'gender':
        trans = [GENDER_TRANSLATOR]
        strs = [['male', 'female']]
        output = [['', '']]
    elif attr == 'age':
        trans = [AGE_TRANSLATOR]
        strs = [['young', 'old']]
        output = [['', '']]
    elif attr == 'all':
        trans = [GENDER_TRANSLATOR, AGE_TRANSLATOR]
        strs = [['male', 'female'], ['young', 'old']]
        output = [['', ''], ['', '']]
    else:
        raise Exception("Unexpected attr %s" % attr)

    for phrase in sub:
        phrase = phrase.strip()
        if phrase != '':
            for i, t in enumerate(trans):
                for j, s in enumerate(strs[i]):
                    output[i][j] += ' ' + t.translate_sentence(phrase, s).strip()
    return output


# Add translations for all tweets in tweet
def add_translations(tweets, attr):
    for tweet in tweets:
        trns = translate(tweet.tweet, attr)
        if attr in ['gender', 'all']:
            tweet.gender_translation_m_f = trns[0][0]
            tweet.gender_translation_f_m = trns[0][1]
        elif attr == 'age':
            tweet.age_translation_y_o = trns[0][0]
            tweet.age_translation_o_y = trns[0][1]
        else:
            tweet.age_translation_y_o = trns[1][0]
            tweet.age_translation_o_y = trns[1][1]
        tweet.save()
    return tweets


# Convert from a list of lists of tuples to a single string to store weights
# Words are separated by a comma from their weights, and by a tab from the next word, weight pair.
# Explanations for classes are separated by a newline and they appear in the same order as the classes do in
# Attribute Categories.
def explanations_to_string(data):
    strings = []
    for exp in data:
        as_string = '\t'.join([str(x[0]) + ',' + str(x[1]) for x in exp]) if exp is not None else ','
        strings.append(as_string)
    return '\n'.join(strings)


def list_to_string(my_list, index):
    return ','.join([str(x[index]) for x in my_list]) if my_list is not None else ''


def get_lex_strings(tweet, attr_name, include_weights):
    score, l, s = lex_classify(tweet, attr_name, include_weights=include_weights)
    words = list_to_string(s, 0) + '\n' + list_to_string(l, 0)
    weights = list_to_string(s, 1) + '\n' + list_to_string(l, 1)
    return score, words, weights


# Builds Tweet from username and tweet text, saves, and returns Tweet.
def build_tweet(username, tweet, prev_number=-1, origin=None):
    if origin is None:
        origin = 'original'
    # Do gender profiling
    g_score, g_words, g_weights = get_lex_strings(tweet, 'gender', include_weights=True)

    # Do age profiling
    a_score, a_words, a_weights = get_lex_strings(tweet, 'age', include_weights=True)

    # Do sentiment Profiling
    s_score, s_words, s_weights = get_lex_strings(tweet, 'sentiment', include_weights=True)

    # Do blob profiling
    pat = TextBlob(tweet).sentiment
    sentiment_blob_pattern = pat.polarity
    _, pol_words, pol_weights = get_lex_strings(tweet, 'polarity', include_weights=True)
    subjectivity_blob = pat.subjectivity
    _, sub_words, sub_weights = get_lex_strings(tweet, 'subjectivity', include_weights=True)
    pat = NBC_BLOBBER(tweet).sentiment
    sentiment_blob_nbc = pat.p_pos

    # Get translations
    # m_f, f_m, y_o, o_y = translate(tweet)

    t = Tweet(username=username, tweet=tweet, is_active=True, update_version=prev_number+1,
              gender_lex_score=g_score, gender_lex_words=g_words, gender_lex_weights=g_weights,
              age_lex_score=a_score, age_lex_words=a_words, age_lex_weights=a_weights,
              sentiment_lex_score=s_score, sentiment_lex_words=s_words, sentiment_lex_weights=s_weights,
              polarity_score=sentiment_blob_pattern, polarity_words=pol_words, polarity_weights=pol_weights,
              sentiment_nbc=sentiment_blob_nbc,
              subjectivity_score=subjectivity_blob, subjectivity_words=sub_words, subjectivity_weights=sub_weights,
              origin=origin)
    t.save()
    return t


# This object stores one `tweet` corresponding to a given `username`.
class Tweet(models.Model):
    username = models.CharField(max_length=100)
    tweet = models.TextField()  # The text of the Tweet.
    is_active = models.BooleanField()  # If `True`, the Tweet is part of the user's current list of Tweets.
    # The number of previous versions of Tweets by this user already stored. If this Tweet is unmodified, should be 0.
    update_version = models.IntegerField()

    # Information for this Tweet for the gender lexicon
    gender_lex_score = models.FloatField()
    gender_lex_words = models.TextField()
    gender_lex_weights = models.TextField()

    # Information for this Tweet for the age lexicon
    age_lex_score = models.FloatField()
    age_lex_words = models.TextField()
    age_lex_weights = models.TextField()

    # Information for this Tweet for the sentiment lexicon
    sentiment_lex_score = models.FloatField()
    sentiment_lex_words = models.TextField()
    sentiment_lex_weights = models.TextField()

    # Information for this Tweet from Blob
    polarity_score = models.FloatField(default=0.0)
    polarity_words = models.TextField(default='')
    polarity_weights = models.TextField(default='')
    sentiment_nbc = models.FloatField(default=0.0)  # This is the probability of the positive class
    subjectivity_score = models.FloatField(default=0.0)
    subjectivity_words = models.TextField(default='')
    subjectivity_weights = models.TextField(default='')

    # Get score from classifiers
    income_score = models.FloatField(default=0.0)

    # Get "translations"
    gender_translation_m_f = models.TextField(default='')
    gender_translation_f_m = models.TextField(default='')
    age_translation_y_o = models.TextField(default='')
    age_translation_o_y = models.TextField(default='')

    # Scores for education classifier
    edu_hs_score = models.FloatField(default=-1.0)
    edu_college_score = models.FloatField(default=-1.0)
    # edu_ug_score = models.FloatField(default=-1.0)
    # edu_gr_score = models.FloatField(default=-1.0)

    # Scores for Neural Network Regression on Income
    nn_r_income_score = models.FloatField(default=-1.0)

    # Category for income
    inc_below_score = models.FloatField(default=-1.0)
    inc_above_score = models.FloatField(default=-1.0)
    inc_highest_score = models.FloatField(default=-1.0)

    # Scores for relationship
    rel_avail_score = models.FloatField(default=-1.0)
    rel_taken_score = models.FloatField(default=-1.0)

    # Scores for race
    race_non_score = models.FloatField(default=-1.0)
    race_white_score = models.FloatField(default=-1.0)

    # Scores for religion
    relig_non_score = models.FloatField(default=-1.0)
    relig_christ_score = models.FloatField(default=-1.0)

    # Scores for politics
    pol_non_score = models.FloatField(default=-1.0)
    pol_con_score = models.FloatField(default=-1.0)

    # The reason why this Tweet came to be. If it's one scraped from Twitter, this field will be `original`, else if
    # it's an edited Tweet, the field will specify the classifier and target attribute.
    origin = models.TextField(default='original')

    def __str__(self):
        return str(self.username) + '\n' + str(self.tweet)

    def get_blob_info(self, field):
        if field == 'polarity':
            pat = TextBlob(self.tweet).sentiment
            pol = pat.polarity
            # Use lex_classify to get words and weights, and ignore the score
            _, pol_words, pol_weights = get_lex_strings(self.tweet, 'polarity', include_weights=True)
            return pol, pol_words, pol_weights

        elif field == 'subjectivity':
            pat = TextBlob(self.tweet).sentiment
            sub = pat.subjectivity
            # Use lex_classify to get words and weights, and ignore the score
            _, sub_words, sub_weights = get_lex_strings(self.tweet, 'subjectivity', include_weights=True)
            return sub, sub_words, sub_weights
        elif field == 'nbc':
            pat = NBC_BLOBBER(self.tweet).sentiment
            return pat.p_pos
        else:
            raise Exception("Unexpected field %s" % field)

    # Replace all sensitive attribute scores with the default
    def clear_sensitive(self):
        # Scores for race
        self.race_non_score = -1.0
        self.race_white_score = -1.0

        # Scores for religion
        self.relig_non_score = -1.0
        self.relig_christ_score = -1.0

        # Scores for politics
        self.pol_non_score = -1.0
        self.pol_con_score = -1.0


# This object stores elements of a profile for a given user.
class Profile(models.Model):
    username = models.CharField(max_length=100)
    attr_name = models.CharField('Attribute Name', max_length=100, name='attr_name')
    classifier = models.CharField('Classifier', max_length=100, name='classifier')
    predicted_class = models.CharField('Predicted Class', max_length=100, name='predicted_class')
    class_confidence = models.FloatField('Class Confidence', name='class_confidence')
    confidence_str = models.CharField("Confidence String", max_length=100, name='confidence_str')
    attr_categories = models.TextField("Attribute Categories", name="attr_categories")
    category_desc = models.TextField("Category Descriptions", name="category_desc")
    attr_values = models.TextField("Attribute Values", name='attr_values')
    explanations = models.TextField("Explanations", name='explanations')
    global_explanations = models.TextField("Global Explanations", name='global_explanations')
    current = models.BooleanField("Is Current", name='is_current')
    is_sensitive = models.BooleanField("Is Sensitive", name='is_sensitive', default=False)
    extra_info = models.TextField("Extra Info", name='extra_info', default='')

    def __str__(self):
        return ' '.join([str(self.username), str(self.attr_name), str(self.classifier)])

    def get_class_list(self):
        return str(self.attr_categories).split('\n')

    def get_class_descriptors(self):
        return str(self.category_desc).split('\n')

    def get_values(self):
        return str(self.attr_values).split('\n')

    def get_explanations(self, index=0, weights=False):
        exp = str(self.explanations).split('\n')
        exp_list = exp[index].split('\t')

        split = [x.split(',') for x in exp_list]
        split = [x if len(x) == 2 else [',', x[2]] for x in split]

        if weights:
            return split
        else:
            return [x[0] for x in split]

    def get_global_explanations(self, index=0, weights=False):
        exp = str(self.global_explanations).split('\n')
        exp_list = exp[index].split('\t')
        # return exp_list
        if weights:
            return [x.split(',') for x in exp_list]
        else:
            return [x.split(',')[0] for x in exp_list]

    def order_and_return(self, n=2):
        # Get lexical results
        if str(self.classifier) == 'lexicon':
            if str(self.attr_name) == 'gender':
                mins = Tweet.objects.filter(username=str(self.username), is_active=True).order_by(
                    'gender_lex_score')
                # Get explanations
                sorted_tweets = []
                for t in mins:
                    if t.gender_lex_score <= 0:
                        sorted_tweets.append((t.tweet, str(t.gender_lex_words).split('\n')[0].split(',')[:n]))
                    else:
                        sorted_tweets.append((t.tweet, str(t.gender_lex_words).split('\n')[1].split(',')[:n]))

            elif str(self.attr_name) == 'age':
                mins = Tweet.objects.filter(username=str(self.username), is_active=True).order_by(
                    'age_lex_score')
                # Get explanations
                sorted_tweets = []
                for t in mins:
                    if t.age_lex_score <= 0:
                        sorted_tweets.append((t.tweet, str(t.age_lex_words).split('\n')[0].split(',')[:n]))
                    else:
                        sorted_tweets.append((t.tweet, str(t.age_lex_words).split('\n')[1].split(',')[:n]))

            elif str(self.attr_name) == 'sentiment':
                mins = Tweet.objects.filter(username=str(self.username), is_active=True).order_by(
                    'sentiment_lex_score')
                # Get explanations
                sorted_tweets = []
                for t in mins:
                    if t.sentiment_lex_score <= 0:
                        sorted_tweets.append((t.tweet, str(t.sentiment_lex_words).split('\n')[0].split(',')[:n]))
                    else:
                        sorted_tweets.append((t.tweet, str(t.sentiment_lex_words).split('\n')[1].split(',')[:n]))

            else:
                raise Exception("unexpected lexicon")

        # Get blob results
        elif str(self.classifier) == 'blob':
            if str(self.extra_info) == 'naive bayes classifier':
                # Just return the tweets
                mins = Tweet.objects.filter(username=str(self.username), is_active=True).order_by(
                    'sentiment_nbc')
                # Get explanations
                sorted_tweets = [(x.tweet, None) for x in mins]

            elif str(self.attr_name) == 'subjectivity':
                mins = Tweet.objects.filter(username=str(self.username), is_active=True).order_by(
                    'subjectivity_score')
                # Get explanations
                sorted_tweets = []
                for t in mins:
                    if t.subjectivity_score <= 0:
                        sorted_tweets.append((t.tweet, str(t.subjectivity_words).split('\n')[0].split(',')[:n]))
                    else:
                        sorted_tweets.append((t.tweet, str(t.subjectivity_words).split('\n')[1].split(',')[:n]))

            else:
                mins = Tweet.objects.filter(username=str(self.username), is_active=True).order_by(
                    'polarity_score')
                # Get explanations
                sorted_tweets = []
                for t in mins:
                    if t.polarity_score <= 0:
                        sorted_tweets.append((t.tweet, str(t.polarity_words).split('\n')[0].split(',')[:n]))
                    else:
                        sorted_tweets.append((t.tweet, str(t.polarity_words).split('\n')[1].split(',')[:n]))
        else:
            raise Exception("Invalid call to order_and_return")

        return sorted_tweets


# This class stores a list of the Tweet ids most recently provided to be modified.
class ServedTweets(models.Model):
    tweet_ids = models.CharField(max_length=10000, validators=[int_list_validator])
    username = models.CharField(max_length=100)

    def __str__(self):
        return str(self.tweet_ids)

    def return_id_list(self):
        as_list = str(self.tweet_ids).split(',')
        return [int(x) for x in as_list]


# This class stores information about user consent/preferences
class User(models.Model):
    username = models.CharField(max_length=100)
    tweet_limit = models.IntegerField(default=-1)
    scraped_tweets = models.IntegerField(default=-1)
    use_sensitive = models.BooleanField(default=False)
