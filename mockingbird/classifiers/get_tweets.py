import csv
import os
import twint


# Get tweets for username `user`. If `return_data`, return them as a Tweet object. If `save_csv`, store them as a csv
# with name `filename`. If `verbose`, print Tweets as well. `limit` is the maximum number of Tweets to return.
# Returns all available Tweets if `limit` is `None`.
def get_tweets(user, return_data=False, save_csv=False, filename=None, verbose=False, limit=200, local=False):

    if save_csv and filename is None and not local:
        filename = './classifiers/data/twint_data/' + user + '.csv'
    elif save_csv and filename is None:
        filename = './data/twint_data/' + user + '.csv'

    # Remove file if it already exists
    if os.path.exists(filename):
        os.remove(filename)

    # Configure
    c = twint.Config()
    c.Username = user
    if not verbose:
        c.Hide_output = True
    if return_data:
        c.Store_object = True
    if save_csv:
        c.Store_csv = True
        c.Output = filename
    if limit is not None:
        # Round to nearest multiple of 20
        c.Limit = limit + (limit % 20)

    twint.run.Search(c)

    if return_data:
        return [x.tweet for x in twint.output.tweets_object]


# Read Tweets from csv and return as a list
def read_tweets(filename):
    tweets = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tweets.append(row['tweet'])
    return tweets
