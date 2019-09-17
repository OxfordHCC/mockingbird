from django.shortcuts import render
from django.http import HttpResponse
import numpy as np
from lime.lime_text import LimeTextExplainer


from twitter.forms import UpdateTweetForm
from twitter.models import *
from twitter.classifier_helpers import *

NBC_EXPLAINER = LimeTextExplainer(class_names=['positive', 'negative'])
# EDU_EXPLAINER = LimeTextExplainer(class_names=['high school', 'undergraduate', 'graduate'])
EDU_EXPLAINER = LimeTextExplainer(class_names=['high school', 'college'])
INC_EXPLAINER = LimeTextExplainer(class_names=['below average', 'above average'])
INC_CAT_EXPLAINER = LimeTextExplainer(class_names=['below average', 'above average', 'far above average'])
REL_EXPLAINER = LimeTextExplainer(class_names=['available', 'taken'])
POL_EXPLAINER = LimeTextExplainer(class_names=['non-political', 'political'])
RELIG_EXPLAINER = LimeTextExplainer(class_names=['non-Christian', 'Christian'])
RACE_EXPLAINER = LimeTextExplainer(class_names=['non-white', 'white'])


# Get LIME explanation for a given Tweet
def lime_explain(request, username, attr, tweet, target, start_index, n_words=3):
    if attr == 'nbc':
        # Generate the LIME output
        exp = NBC_EXPLAINER.explain_instance(tweet, convert_and_score_nbc, num_features=n_words)

    elif attr == 'income':
        exp = INC_EXPLAINER.explain_instance(tweet, convert_and_score_inc, num_features=n_words)

    elif attr == 'education':
        exp = EDU_EXPLAINER.explain_instance(tweet, convert_and_score_edu, num_features=n_words)

    elif attr == 'income (categorical)':
        exp = INC_CAT_EXPLAINER.explain_instance(tweet, convert_and_score_inc_cat, num_features=n_words,
                                                 labels=[0, 1, 2])
    elif attr == 'relationship':
        exp = REL_EXPLAINER.explain_instance(tweet, convert_and_score_rel, num_features=n_words)

    elif attr == 'politics':
        exp = POL_EXPLAINER.explain_instance(tweet, convert_and_score_pol, num_features=n_words)

    elif attr == 'religion':
        exp = RELIG_EXPLAINER.explain_instance(tweet, convert_and_score_relig, num_features=n_words)

    elif attr == 'race':
        exp = RACE_EXPLAINER.explain_instance(tweet, convert_and_score_race, num_features=n_words)

    # Fill Tweet dict
    tweet_dict = {"target": target, "start_index": start_index, "tweet_1": tweet}
    form = UpdateTweetForm(initial=tweet_dict)

    # Indicate that which Tweet we're editing
    id_string = str(Tweet.objects.get(username=username, tweet=tweet, is_active=True).id) + ',-1'*9
    served = ServedTweets(username=username, tweet_ids=id_string)
    served.save()

    return render(request, 'twitter/lime_explanation.html', {'username': username, "exp": exp.as_html(), 'form': form,
                                                             'attr': attr, "target": target,
                                                             "start_index": start_index})


# Use LIME to explain *all* active Tweets
def lime_explain_all(request, username, attr, n_words=25):
    # Get all Tweets
    tweets = Tweet.objects.filter(username=username, is_active=True)
    tweet_string = '\n'.join([str(t.tweet) for t in tweets])
    is_m3 = False

    # Get explanation
    if attr == 'nbc':
        # Generate the LIME output
        exp = NBC_EXPLAINER.explain_instance(tweet_string, convert_and_score_nbc, num_features=n_words)

    elif attr == 'education':
        exp = EDU_EXPLAINER.explain_instance(tweet_string, convert_and_score_edu, num_features=n_words)

    elif attr == 'income (categorical)':
        exp = INC_CAT_EXPLAINER.explain_instance(tweet_string, convert_and_score_inc_cat, num_features=n_words,
                                                 labels=[0, 1, 2])

    elif attr == 'income':
        exp = INC_EXPLAINER.explain_instance(tweet_string, convert_and_score_inc, num_features=n_words)

    elif attr == 'relationship':
        exp = REL_EXPLAINER.explain_instance(tweet_string, convert_and_score_rel, num_features=n_words)

    elif attr == 'politics':
        exp = POL_EXPLAINER.explain_instance(tweet_string, convert_and_score_pol, num_features=n_words)

    elif attr == 'religion':
        exp = RELIG_EXPLAINER.explain_instance(tweet_string, convert_and_score_relig, num_features=n_words)

    elif attr == 'race':
        exp = RACE_EXPLAINER.explain_instance(tweet_string, convert_and_score_race, num_features=n_words)

    exp = exp.as_html()

    return render(request, 'twitter/lime_explain_all.html', {'username': username, "exp": exp, 'attr': attr})
