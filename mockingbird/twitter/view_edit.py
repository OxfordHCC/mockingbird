from django.shortcuts import render

from twitter.models import Profile, Tweet, add_translations, ServedTweets, build_tweet
from twitter.view_helper_functions import get_syns
from twitter.forms import UpdateTweetForm
from twitter.classifier_helpers import score_tweets


# Save the tweets specified in tweet_dict
def save_tweets(username, tweets, origin):

    # Get the most recent served tweets
    served = ServedTweets.objects.filter(username=username).order_by('-id')[0]
    served_ids = served.return_id_list()

    is_changed = False
    new_tweets = []
    for i, t in enumerate(tweets):
        if int(served_ids[i]) != -1:
            former = Tweet.objects.get(id=served_ids[i])
        else:
            former = None  # This is a new Tweet

        # Added Tweet
        if former is None and str(t) != '':
            is_changed = True
            new_tweets.append(build_tweet(username, t, former.update_version, origin=origin))

        # Edited existing Tweet
        elif former is not None and str(t) != str(former.tweet):
            former.is_active = False
            former.save()
            is_changed = True

            # Do not add a Tweet for those with no text (equivalent to deleting)
            if t != '':
                new_tweets.append(build_tweet(username, t, former.update_version, origin=origin))

    return is_changed


# General purpose function to handle all lexical edits
def lex_edit(request, username, attr, target, start_index=0):
    if attr in ['polarity', 'subjectivity']:
        if attr == 'polarity':
            p = Profile.objects.get(username=username, attr_name='sentiment', classifier='blob', is_current=True,
                                    extra_info='pattern')
            feature_name = 'polarity_score'
        else:
            p = Profile.objects.get(username=username, attr_name=attr, classifier='blob', is_current=True)
            feature_name = 'subjectivity_score'
    else:
        p = Profile.objects.get(username=username, attr_name=attr, classifier='lexicon', is_current=True)
        feature_name = attr + '_lex_score'

    if target in ['masculine', 'young', 'negative', 'objective']:
        target_index = 0
        opp_index = 1
        asc = False  # Low values indicate that Tweets are more like the target
    else:
        target_index = 1
        opp_index = 0
        asc = True

    # Get top ten Tweets
    if asc:
        tweet_list = list(Tweet.objects.filter(username=username, is_active=True).order_by(feature_name)[
                          start_index * 10:10 * (start_index + 1)])
    else:
        tweet_list = list(Tweet.objects.filter(username=username, is_active=True).order_by('-' + feature_name)[
                          start_index * 10:10 * (start_index + 1)])

    # Get translations for relevant Tweets
    translations = None
    if attr in ['gender', 'age']:
        tweet_list = add_translations(tweet_list, attr)
        if attr == 'gender' and target == 'masculine':
            translations = [t.gender_translation_f_m for t in tweet_list]
        elif attr == 'gender' and target == 'feminine':
            translations = [t.gender_translation_m_f for t in tweet_list]
        elif attr == 'age' and target == 'young':
            translations = [t.age_translation_o_y for t in tweet_list]
        elif attr == 'age' and target == 'old':
            translations = [t.age_translation_y_o for t in tweet_list]

    # Get score and explanatory words
    if attr == 'gender':
        scores = [round(float(t.gender_lex_score), 2) for t in tweet_list]
        words = [t.gender_lex_words.split('\n')[opp_index].split(',') for t in tweet_list]
    elif attr == 'age':
        scores = [round(float(t.age_lex_score), 2) for t in tweet_list]
        words = [t.age_lex_words.split('\n')[opp_index].split(',') for t in tweet_list]
    elif attr == 'sentiment':
        scores = [round(float(t.sentiment_lex_score), 3) for t in tweet_list]
        words = [t.sentiment_lex_words.split('\n')[opp_index].split(',') for t in tweet_list]
    elif attr == 'polarity':
        scores = [round(float(t.polarity_score), 3) for t in tweet_list]
        words = [t.polarity_words.split('\n')[opp_index].split(',') for t in tweet_list]
    elif attr == 'subjectivity':
        scores = [round(float(t.subjectivity_score), 3) for t in tweet_list]
        words = [t.subjectivity_words.split('\n')[opp_index].split(',') for t in tweet_list]
    else:
        raise Exception("Invalid attribute name")

    # Get synonyms
    syns = [get_syns(x, target_index, attr) for x in words]

    # Fill Tweet dict
    tweet_dict = {"target": target, "start_index": start_index}
    for i in range(10):
        tweet_no = "tweet_" + str(i + 1)
        try:
            tweet_dict[tweet_no] = tweet_list[i].tweet
        except IndexError:
            tweet_dict[tweet_no] = ''
    form = UpdateTweetForm(initial=tweet_dict)

    # Pad if too short
    if len(scores) < 10:
        pad = [None] * (10 - len(scores))
        scores += pad
        words += pad
        tweet_list += pad

    # Indicate that these are the most recently served Tweets
    id_string = ','.join(['-1' if t is None else str(t.id) for t in tweet_list])
    served = ServedTweets(username=username, tweet_ids=id_string)
    served.save()

    # Add the auto-generated new sentence TODO???

    return render(request, 'twitter/lex_edit.html', {
        'username': username, 'target': target, 'original_profile': p, 'target_index': target_index + 1,
        'opp_index': opp_index + 1, "form": form, "scores": scores, 'words': words, 'start_index': start_index,
        "syns": syns, "attr": attr, "translations": translations})


# General purpose function to handle all edits of profiles that do not have inherent explanations
def lime_edit(request, username, attr, target, start_index=0):
    if attr in ['nbc']:
        binary = True
    else:
        binary = False

    if attr in ['income']:
        is_categorical = False
    else:
        is_categorical = True

    if attr == 'nbc':
        p = Profile.objects.get(username=username, attr_name='sentiment', classifier='blob', is_current=True,
                                extra_info='naive bayes classifier')
        feature_name = 'sentiment_nbc'

    elif attr == 'education':
        p = Profile.objects.get(username=username, attr_name='education', is_current=True, extra_info='clf')
        if target == 'high school':
            feature_name = 'edu_hs_score'
            target_index = 0
        elif target == 'college':
            feature_name = 'edu_college_score'
            target_index = 1
        # elif target == 'undergraduate':
        #     feature_name = 'edu_ug_score'
        #     target_index = 1
        # elif target == 'graduate':
        #     feature_name = 'edu_gr_score'
        #     target_index = 2
        else:
            raise Exception("Invalid target %s for attribute education" % target)

    elif attr == 'income (categorical)':
        p = Profile.objects.get(username=username, attr_name=attr, is_current=True, extra_info='clf')
        if target == 'below average':
            feature_name = 'inc_below_score'
            target_index = 0
        elif target == 'above average':
            feature_name = 'inc_above_score'
            target_index = 1
        elif target == 'far above average':
            feature_name = 'inc_highest_score'
            target_index = 2
        else:
            raise Exception("Invalid target %s for attribute income (categorical)" % target)

    elif attr == 'income':
        p = Profile.objects.get(username=username, attr_name='income', is_current=True, extra_info='clf',
                                classifier='Neural Network Regression')
        if target == 'high income':
            feature_name = 'nn_r_income_score'
            target_index = 0
        else:
            feature_name = '-nn_r_income_score'
            target_index = 1

    elif attr == 'relationship':
        p = Profile.objects.get(username=username, attr_name=attr, is_current=True, extra_info='clf')
        if target == 'available':
            feature_name = 'rel_avail_score'
            target_index = 0
        else:
            feature_name = 'rel_taken_score'
            target_index = 1

    elif attr == 'race':
        p = Profile.objects.get(username=username, attr_name=attr, is_current=True, extra_info='clf')
        if target == 'non-white':
            feature_name = 'race_non_score'
            target_index = 0
        else:
            feature_name = 'race_white_score'
            target_index = 1

    elif attr == 'politics':
        p = Profile.objects.get(username=username, attr_name=attr, is_current=True, extra_info='clf')
        if target == 'non-political':
            feature_name = 'pol_non_score'
            target_index = 0
        else:
            feature_name = 'pol_con_score'
            target_index = 1

    elif attr == 'religion':
        p = Profile.objects.get(username=username, attr_name=attr, is_current=True, extra_info='clf')
        if target == 'non-Christian':
            feature_name = 'relig_non_score'
            target_index = 0
        else:
            feature_name = 'relig_christ_score'
            target_index = 1

    if binary:
        if target in ['negative']:
            target_index = 0
            opp_index = 1
            asc = False  # Low values indicate that Tweets are more like the target
        else:
            target_index = 1
            opp_index = 0
            asc = True

        # Get top ten Tweets
        if asc:
            tweet_list = list(Tweet.objects.filter(username=username, is_active=True).order_by(feature_name)[
                              start_index * 10:10 * (start_index + 1)])
        else:
            tweet_list = list(Tweet.objects.filter(username=username, is_active=True).order_by('-' + feature_name)[
                              start_index * 10:10 * (start_index + 1)])

        if attr == 'nbc':
            scores = [round(float(t.sentiment_nbc), 2) for t in tweet_list]
        else:
            raise Exception("Invalid attribute name")

    else:
        score_tweets(username, attr)
        tweet_list = list(Tweet.objects.filter(username=username, is_active=True).order_by(feature_name)[
                          start_index * 10:10 * (start_index + 1)])

        if feature_name == 'edu_hs_score':
            scores = [round(float(t.edu_hs_score), 3) for t in tweet_list]
        elif feature_name == 'edu_college_score':
            scores = [round(float(t.edu_college_score), 3) for t in tweet_list]
        elif feature_name == 'inc_below_score':
            scores = [round(float(t.inc_below_score), 3) for t in tweet_list]
        elif feature_name == 'inc_above_score':
            scores = [round(float(t.inc_above_score), 3) for t in tweet_list]
        elif feature_name == 'inc_highest_score':
            scores = [round(float(t.inc_highest_score), 3) for t in tweet_list]
        elif feature_name == 'rel_avail_score':
            scores = [round(float(t.rel_avail_score), 3) for t in tweet_list]
        elif feature_name == 'rel_taken_score':
            scores = [round(float(t.rel_taken_score), 3) for t in tweet_list]
        elif feature_name == 'race_non_score':
            scores = [round(float(t.race_non_score), 3) for t in tweet_list]
        elif feature_name == 'race_white_score':
            scores = [round(float(t.race_white_score), 3) for t in tweet_list]
        elif feature_name == 'relig_non_score':
            scores = [round(float(t.relig_non_score), 3) for t in tweet_list]
        elif feature_name == 'relig_christ_score':
            scores = [round(float(t.relig_christ_score), 3) for t in tweet_list]
        elif feature_name == 'pol_non_score':
            scores = [round(float(t.pol_non_score), 3) for t in tweet_list]
        elif feature_name == 'pol_con_score':
            scores = [round(float(t.pol_con_score), 3) for t in tweet_list]
        elif feature_name in ['nn_r_income_score', '-nn_r_income_score']:
            scores = [round(float(t.nn_r_income_score), 3) for t in tweet_list]
        else:
            raise Exception("Unexpected feature name %s" % feature_name)

    # Fill Tweet dict
    tweet_dict = {"target": target, "start_index": start_index}
    for i in range(10):
        tweet_no = "tweet_" + str(i + 1)
        try:
            tweet_dict[tweet_no] = tweet_list[i].tweet
        except IndexError:
            tweet_dict[tweet_no] = ''
    form = UpdateTweetForm(initial=tweet_dict)

    # Pad if too short
    if len(scores) < 10:
        pad = [None] * (10 - len(scores))
        scores += pad
        tweet_list += pad

    # Indicate that these are the most recently served Tweets
    id_string = ','.join(['-1' if t is None else str(t.id) for t in tweet_list])
    served = ServedTweets(username=username, tweet_ids=id_string)
    served.save()

    if is_categorical:
        class_index = str(p.attr_categories).split('\n').index(str(p.predicted_class))
        class_confidences = str(p.attr_values).split('\n')
        if len(class_confidences) == 1:
            class_confidences = [float(class_confidences[0]), 1-float(class_confidences[1])]
        else:
            class_confidences = [float(x) for x in class_confidences]
    else:
        class_index = 0
        class_confidences = ['N/A']
        target_index = 0

    return render(request, 'twitter/lime_edit.html', {
        'username': username, 'target': target, 'original_profile': p, 'target_index': target_index + 1,
        "form": form, "scores": scores, 'start_index': start_index, "attr": attr,
        'top_confidence': class_confidences[class_index], 'is_categorical': is_categorical})
