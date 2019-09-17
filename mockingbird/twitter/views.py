from django.shortcuts import render
from .forms import UsernameForm
from .models import Tweet, Profile, build_tweet, User
from .profile_builders import *
from classifiers.get_tweets import read_tweets, get_tweets
from twitter.view_edit import save_tweets, lex_edit, lime_edit
from twitter.view_explain import lime_explain

from twitter.view_helper_functions import clear_and_build_profile


# Collect username
def index(request):
    form = UsernameForm()

    return render(request, 'twitter/index.html', {'form': form})


# Get Tweets for username and display. A wrapper for tweets.
def username(request):
    username = request.POST['username']
    tweet_limit = int(request.POST['no_tweets'])
    use_sensitive = False
    if 'use_sensitive' in request.POST:
        use_sensitive = bool(request.POST['use_sensitive'])

    # Check to see if the username already exists
    try:
        u = User.objects.get(username=username)
        u.tweet_limit = tweet_limit
        u.use_sensitive = use_sensitive
    except Exception:
        u = User(username=username, tweet_limit=tweet_limit, use_sensitive=use_sensitive)
    u.save()
    return tweets(request, username)


# Load and display Tweets
def tweets(request, username, recalculate=False):

    # Scrape new tweets and return
    def scrape(request, user):
        # Deactivate any existing Tweets
        tweets = Tweet.objects.filter(username=user.username, is_active=True)
        if tweets:
            for t in tweets:
                t.is_active = False
                t.save()

        # Scrape Tweets
        get_tweets(username, save_csv=True, local=False, limit=user.tweet_limit)
        tweets = read_tweets('./classifiers/data/twint_data/' + str(username) + '.csv')
        new_tweets = []
        for tweet in tweets:
            new_tweets.append(build_tweet(username, tweet))
        tweet_count = len(new_tweets)
        user.scraped_tweets = tweet_count
        user.save()
        return render(request, 'twitter/username.html', {'username': username, 'tweets': tweets})

    # Attempt to read Tweets from database
    user = User.objects.get(username=username)

    # If this is the test user, load their tweets
    if user.username == 'test':
        tweets = Tweet.objects.filter(username=username, is_active=True)
        if tweets and not recalculate:
            tweets = [x.tweet for x in tweets]
        else:
            tweets = read_tweets('./classifiers/data/test.csv')
            for tweet in tweets:
                build_tweet(username, tweet)
        return render(request, 'twitter/username.html', {'username': username, 'tweets': tweets})

    # If we haven't scraped yet, or if we've already scraped but scraped too few, scrape more
    if user.scraped_tweets == -1 or (user.scraped_tweets % 20 == 0 and user.tweet_limit > user.scraped_tweets):
        return scrape(request, user)

    # Otherwise, see if we have any existing tweets
    tweets = Tweet.objects.filter(username=username, is_active=True)
    if tweets and not recalculate:
        t = [x.tweet for x in tweets]
        return render(request, 'twitter/username.html', {'username': username, 'tweets': t})
    else:
        # Attempt to read from csv file
        try:
            # If we find the file, read it, add it to the database, and proceed
            tweets = read_tweets('./classifiers/data/twint_data/' + str(username) + '.csv')
            for tweet in tweets:
                build_tweet(username, tweet)
            return render(request, 'twitter/username.html', {'username': username, 'tweets': tweets})

        except FileNotFoundError:
            return scrape(request, user)


# Display profile.
def profile(request, username, recalculate=False):
    # Check if values for each classifier exist. If they don't, build them.

    # Try lexical classifiers.

    # Try gender first.
    lex_gender = clear_and_build_profile(username, 'gender', recalculate)

    # Try age next
    lex_age = clear_and_build_profile(username, 'age', recalculate)

    # Try sentiment next
    lex_sent = clear_and_build_profile(username, 'sentiment', recalculate)

    # Try IBM (Big Five)
    ibm = clear_and_build_profile(username, 'ibm', False)  # This is to reduce API calls while testing

    # Try M3: age, gender, is_organization
    m_gen, m_age, m_corp = clear_and_build_profile(username, 'm3', False)  # Recalculate doesn't matter here

    # Try textblob
    tb_sen1, tb_subj, tb_sen2 = clear_and_build_profile(username, 'blob', recalculate)

    # Try classifier results
    inc_reg, inc_cat, edu, relationship, sensitive = clear_and_build_profile(username, 'clf', recalculate)

    gender = [lex_gender, m_gen]
    age = [lex_age, m_age]
    income = [inc_reg, inc_cat]
    education = [edu]
    rel = [relationship]

    sent = [lex_sent, tb_sen1, tb_sen2]
    subj = [tb_subj]
    ibm = ibm
    corp = [m_corp]

    if sensitive is None:
        classes = [sent, gender, age, income, rel, education, subj, corp]
    else:
        classes = [sent, gender, age, income, rel, [sensitive[0]], [sensitive[1]], [sensitive[2]], education, subj,
                   corp]

    # Return all results
    return render(request, 'twitter/profile.html', {'username': username, "classes": classes,
                                                    "ibm": ibm})


# Reset Tweets to the originals (read from csv file)
def reset_tweets(request, username):

    # Deactivate all current Tweets and previous served
    new_tweets = Tweet.objects.filter(username=username, is_active=True)
    for t in new_tweets:
        t.is_active = False
        t.save()

    # Read and save new Tweets
    if username != 'test':
        tweets = read_tweets('./classifiers/data/twint_data/' + str(username) + '.csv')
    else:
        tweets = read_tweets('./classifiers/data/test.csv')
    for tweet in tweets:
        _ = build_tweet(username, tweet)
    return profile(request, username, recalculate=True)


# Handle loading profiles and edited pages after receiving edits
def lex_edited(request, username, attr):
    target = request.POST['target']
    if 'next' in request.POST:
        value = 'next'
        prev_index = int(request.POST['start_index'])
    elif 'prev' in request.POST:
        value = 'prev'
        prev_index = int(request.POST['start_index'])
    else:
        value = 'profile'
        prev_index = -1

    # Save any Tweets from the form to the database.
    tweets = []
    for i in range(1, 11):
        tweets.append(request.POST['tweet_' + str(i)])

    is_changed = save_tweets(username, tweets, 'lex-' + target)

    # If we saw changes, clear the old profiles as they need to be recalculated
    if is_changed:
        profiles = Profile.objects.filter(username=username, is_current=True)
        for p in profiles:
            p.is_current = False
            p.save()

    if value == 'profile':
        return profile(request, username, recalculate=is_changed)
    elif value == 'prev':
        if attr in ['polarity', 'subjectivity']:
            attr_p = 'blob'
        else:
            attr_p = attr
        # Build new profiles
        clear_and_build_profile(username, attr_p, is_changed)
        # Return previous 10 Tweets
        return lex_edit(request, username, attr, target, prev_index - 1)
    else:
        if attr in ['polarity', 'subjectivity']:
            attr_p = 'blob'
        else:
            attr_p = attr
        # Move on to the next 10 Tweets to edit
        clear_and_build_profile(username, attr_p, is_changed)
        return lex_edit(request, username, attr, target, prev_index + 1)


# Handle loading profiles and edited pages after receiving edits
def lime_edited(request, username, attr):
    target = request.POST['target']
    if 'next' in request.POST:
        value = 'next'
        prev_index = int(request.POST['next'])
        tweet_id = -1
    elif 'prev' in request.POST:
        value = 'prev'
        prev_index = int(request.POST['prev'])
        tweet_id = -1
    elif 'tweet' in request.POST:
        value = 'explain'
        tweet_id = int(request.POST['tweet'])
        prev_index = int(request.POST['start_index'])
    elif 'return' in request.POST:
        value = 'return'
        tweet_id = -1
        prev_index = int(request.POST['start_index'])
    else:
        value = 'profile'
        prev_index = -1
        tweet_id = -1

    # Save any Tweets from the form to the database.
    if 'tweet_2' in request.POST:
        tweets = []
        for i in range(1, 11):
            tweets.append(request.POST['tweet_' + str(i)])
    else:
        tweets = [request.POST['tweet_1']]

    is_changed = save_tweets(username, tweets, 'lime-' + attr + '-' + target)

    # If we saw changes, clear the old profiles as they need to be recalculated
    if is_changed:
        profiles = Profile.objects.filter(username=username, is_current=True)
        for p in profiles:
            p.is_current = False
            p.save()

    if value == 'profile':
        return profile(request, username, recalculate=is_changed)
    # Return to pages to edit Tweets
    elif value in ['prev', 'next', 'return']:
        if attr == 'nbc':
            attr_p = 'blob'
        elif attr in ['education', 'income', 'income (categorical)', 'relationship', 'religion', 'race', 'politics']:
            attr_p = 'clf'
        else:
            attr_p = attr
        # Build new profiles
        clear_and_build_profile(username, attr_p, is_changed)
        if value == 'next':
            next_index = prev_index + 1
        elif value == 'prev':
            next_index = prev_index - 1
        else:
            next_index = prev_index
        return lime_edit(request, username, attr, target, next_index)
    elif value == 'explain':
        return lime_explain(request, username, attr, request.POST['tweet_' + str(tweet_id)], target, prev_index)
    else:
        raise Exception("Unexpected field %s" % value)
