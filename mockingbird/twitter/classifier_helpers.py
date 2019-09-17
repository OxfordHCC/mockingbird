# Imports
import numpy as np
import pickle
import re
import pandas as pd
from sklearn.utils import shuffle
from keras.models import load_model
from tensorflow.compat.v1 import get_default_graph, logging
# from tensorflow import logging
import os
from twitter.models import Tweet, NBC_BLOBBER

# Get tensorflow to not be annoying
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.set_verbosity(logging.ERROR)

# Load TF-IDF Vectorizer
with open('./classifiers/models/tf_idf_vectorizer.pkl', 'rb') as tf:
    TF_IDF = pickle.load(tf)

# Load keras classifiers
EDU_CLF = load_model('./classifiers/models/edu.h5')
REL_CLF = load_model('./classifiers/models/relationship.h5')
POL_CLF = load_model('./classifiers/models/politics.h5')
RELIG_CLF = load_model('./classifiers/models/religion.h5')
RACE_CLF = load_model('./classifiers/models/race.h5')

# Load keras income classifier
INC_MAX_VAL = 111413  # The highest income in the training data
INC_MIN_VAL = 8395  # The lowest income in the training data
INC_MEAN_VAL = 32516.810946232414  # The average income in the training data
INC_MEAN_RATIO = INC_MEAN_VAL/INC_MAX_VAL
INC_R_NN_CLF = load_model('./classifiers/models/income_r_nn.h5')
INC_CAT_CLF = load_model('./classifiers/models/income_cat.h5')


global graph
graph = get_default_graph()


# Get all classifier scores based on a particular string
def get_clf_scores(text, use_sensitive):
    tf = TF_IDF.transform([text]).toarray().reshape(1, -1)

    # Get predictions
    global graph
    with graph.as_default():
        inc_score_nn = INC_R_NN_CLF.predict(tf)[0]
        inc_score_nn *= INC_MAX_VAL  # Rescale the data
        inc_cat_score = INC_CAT_CLF.predict(tf)[0]
        edu_score = EDU_CLF.predict(tf)[0]
        rel_score = REL_CLF.predict(tf)[0]

    # Round when appropriate
    inc_cat_score = [round(float(x), 8) for x in inc_cat_score]
    edu_score = [round(float(x), 8) for x in edu_score]
    rel_score = [round(float(x), 8) for x in rel_score]

    if not use_sensitive:
        return [inc_score_nn, inc_cat_score, edu_score, rel_score]
    else:
        with graph.as_default():
            pol_score = POL_CLF.predict(tf)[0]
            relig_score = RELIG_CLF.predict(tf)[0]
            race_score = RACE_CLF.predict(tf)[0]

        # Round
        pol_score = [round(float(x), 8) for x in pol_score]
        relig_score = [round(float(x), 8) for x in relig_score]
        race_score = [round(float(x), 8) for x in race_score]

        return [inc_score_nn, inc_cat_score, edu_score, rel_score, pol_score, relig_score, race_score]


# Look up all Tweets, score on attribute if not already scored
def score_tweets(username, attr):

    # Load all Tweets for user
    tweets = Tweet.objects.filter(username=username, is_active=True)

    # Get all Tweets which need to be scored
    unscored = []
    for t in tweets:
        if attr == 'education':
            if t.edu_hs_score == -1.0:
                unscored.append(t)
        elif attr == 'income':
            if t.nn_r_income_score == -1.0:
                unscored.append(t)
        elif attr == 'income (categorical)':
            if t.inc_below_score == -1.0:
                unscored.append(t)
        elif attr == 'relationship':
            if t.rel_avail_score == -1.0:
                unscored.append(t)
        elif attr == 'race':
            if t.race_non_score == -1.0:
                unscored.append(t)
        elif attr == 'religion':
            if t.relig_non_score == -1.0:
                unscored.append(t)
        elif attr == 'politics':
            if t.pol_non_score == -1.0:
                unscored.append(t)
        else:
            raise Exception("Unexpected attribute %s" % attr)

    if unscored:
        # Convert all to TF-IDF
        unscored_text = [t.tweet for t in unscored]
        unscored_tf = TF_IDF.transform(unscored_text).toarray()

        # Get scores
        global graph
        with graph.as_default():
            if attr == 'education':
                edu_score = EDU_CLF.predict(unscored_tf)
                for score, tweet in zip(edu_score, unscored):
                    tweet.edu_hs_score = score[0]
                    tweet.edu_college_score = score[1]
                    # tweet.edu_ug_score = score[1]
                    # tweet.edu_gr_score = score[2]
                    tweet.save()
            elif attr == 'income':
                income_score = INC_R_NN_CLF.predict(unscored_tf)
                for score, tweet in zip(income_score, unscored):
                    tweet.nn_r_income_score = score*INC_MAX_VAL
                    tweet.save()
            elif attr == 'income (categorical)':
                inc_score = INC_CAT_CLF.predict(unscored_tf)
                for score, tweet in zip(inc_score, unscored):
                    tweet.inc_below_score = score[0]
                    tweet.inc_above_score = score[1]
                    tweet.inc_highest_score = score[2]
                    tweet.save()
            elif attr == 'relationship':
                rel_score = REL_CLF.predict(unscored_tf)
                for score, tweet in zip(rel_score, unscored):
                    tweet.rel_avail_score = score[0]
                    tweet.rel_taken_score = score[1]
                    tweet.save()
            elif attr == 'politics':
                pol_score = POL_CLF.predict(unscored_tf)
                for score, tweet in zip(pol_score, unscored):
                    tweet.pol_non_score = score[0]
                    tweet.pol_con_score = score[1]
                    tweet.save()
            elif attr == 'race':
                race_score = RACE_CLF.predict(unscored_tf)
                for score, tweet in zip(race_score, unscored):
                    tweet.race_non_score = score[0]
                    tweet.race_white_score = score[1]
                    tweet.save()
            elif attr == 'religion':
                relig_score = RELIG_CLF.predict(unscored_tf)
                for score, tweet in zip(relig_score, unscored):
                    tweet.relig_non_score = score[0]
                    tweet.relig_christ_score = score[1]
                    tweet.save()


# Convert unigram frequency count for one user provided by `data` to a vector.
# Reserves location 0 for out of vocabulary words.
# If `output_type` is `raw`, the raw unigram frequencies are returned.
# If `output_type` is `binary`, 1 is returned if the unigram appears and 0 otherwise.
# `vec_size` is the size of the dictionary + 1. By default it is 71556, the size of
# `dictionary.txt` for the income data.
def get_vec(data, output_type='binary', vec_size=71556):
    # Check that output_type is valid
    if output_type not in ['raw', 'binary']:
        raise Exception('Invalid vector type supplied. Choose raw or binary.')

    # Get scores
    scores = np.zeros(vec_size, dtype=int)
    data_list = data.split(' ')

    for row in data_list:
        index, count = row.split(':')
        if output_type == 'raw':
            scores[int(index)] = int(count)
        elif output_type == 'binary':
            scores[int(index)] = 1

    return scores


# Read from file `filename` the user_id and unigram data. Return a list of
# tuples, where each tuple has the user_id and a unigram vector.
# Default `filename` is the file location for the income data.
def get_id_uni(filename='./classifiers/data/income/jobs-unigrams.txt', output_type='binary',
               vec_size=71556):

    id_list = []
    with open(filename, 'r') as file:
        for row in file:
            # Get user_id
            user_id = re.findall('^\d+ ', row)
            if len(user_id) == 1:
                # Get vector
                user_id = int(user_id[0].strip())
                data = re.sub('^\d+ ', '', row)
                vec = get_vec(data, output_type=output_type, vec_size=vec_size)
                id_list.append((user_id, vec))

            # Two appear to be missing this data
            elif len(user_id) == 0:
                continue
            # If we can't parse properly, throw an error
            else:
                raise Exception("Unable to read user_id")

    return id_list


# Associate each unigram in the list with the label specified by `label`. Return
# a list with all of the unigrams and a list with all of the labels.
# Automatically reads data from ./income_labels.csv.
def match_label(data, label, labels_file='./income_labels.csv'):
    labels = pd.read_csv('./classifiers/data/income/income_labels.csv', index_col=0)
    X = []
    Y = []

    for row in data:
        u_id, uni = row
        X.append(uni)
        Y.append(labels[label].loc[u_id])

    return X, Y


# Get test/train split
def get_split(X, Y, train_size=5000, do_shuffle=True):
    if do_shuffle:
        X, Y = shuffle(X, Y)

    train_x = X[:train_size]
    train_y = Y[:train_size]
    test_x = X[train_size:]
    test_y = Y[train_size:]
    return train_x, train_y, test_x, test_y


# Get training data for building LIME Explainer
def get_train(attr, percentage=1):
    data = get_id_uni(output_type='binary')
    X, Y = match_label(data, attr)
    del data  # to save RAM
    x_train, _, _, _ = get_split(X, Y, int(len(Y) * percentage), do_shuffle=True)
    return x_train


# Converts to TF-IDF and scores, returns raw score
def convert_and_score(texts, classifier):
    tf = TF_IDF.transform(texts).toarray()

    if classifier == 'education':
        clf = EDU_CLF
    elif classifier == 'income (categorical)':
        clf = INC_CAT_CLF
    elif classifier == 'relationship':
        clf = REL_CLF
    elif classifier == 'religion':
        clf = RELIG_CLF
    elif classifier == 'race':
        clf = RACE_CLF
    elif classifier == 'politics':
        clf = POL_CLF
    elif classifier == 'income':
        # Handle the regression income classifier separately
        clf = INC_R_NN_CLF
        with graph.as_default():
            preds = clf.predict(tf)
            p_percentage = np.zeros((len(texts), 2))
            for i, p in enumerate(preds):
                if p <= INC_MEAN_RATIO:
                    left = ((p/INC_MEAN_RATIO)*0.5 - 1) * -1
                    assert 0.5 <= left <= 1, "Correct label (below) has bad probability %.4f" % left
                    right = 1 - left
                else:
                    right = ((p - INC_MEAN_RATIO)/(1 - INC_MEAN_RATIO))*0.5 + 0.5
                    assert 0.5 <= right <= 1, "Correct label (above) has bad probability %.4f" % right
                    left = 1 - right
                p_percentage[i, 0] = left
                p_percentage[i, 1] = right
        return p_percentage

    else:
        raise Exception("Unexpected Classifier %s" % classifier)

    with graph.as_default():
        return clf.predict(tf)


# Wrapper for each convert_and_score
def convert_and_score_edu(texts):
    return convert_and_score(texts, 'education')


def convert_and_score_inc(texts):
    return convert_and_score(texts, 'income')


def convert_and_score_inc_cat(texts):
    return convert_and_score(texts, 'income (categorical)')


def convert_and_score_rel(texts):
    return convert_and_score(texts, 'relationship')


def convert_and_score_relig(texts):
    return convert_and_score(texts, 'religion')


def convert_and_score_race(texts):
    return convert_and_score(texts, 'race')


def convert_and_score_pol(texts):
    return convert_and_score(texts, 'politics')


def convert_and_score_nbc(texts):
    scores = []
    for t in texts:
        sc = NBC_BLOBBER(t)
        scores.append([sc.sentiment.p_pos, sc.sentiment.p_neg])
    return np.array(scores)
