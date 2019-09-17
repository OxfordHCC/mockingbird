from django.http import HttpResponse
from django.shortcuts import render

from twitter.models import Profile, Tweet
from twitter.view_helper_functions import make_plot, make_bar


# The header to use for lexicographic profiles.
lex_header = 'This profile is built on a lexicon. Put simply, the algorithm uses a dictionary of words, each with a ' \
             'specific weight. It sums up the weights of all of the words in the text and uses this to make the ' \
             'profile. It is easy to fool by removing words in its dictionary, misspelling words, or replacing words' \
             ' with their synonyms.'


# Loads the appropriate info page
def lex_info(request, username, attr):
    p = Profile.objects.get(username=username, attr_name=attr, classifier='lexicon', is_current=True)

    if attr == 'gender':
        script, div = make_plot(min_val=-2.0, max_val=2.0, score=float(str(p.attr_values).split('\n')[0]),
                                title="Your Lexicographic Gender Profile", axis_label="Raw Score",
                                left_label="←\nMasculine", right_label="Feminine→", box=[-1.25, -.25, .25, 1.25],
                                right_label_loc=1.07)
        adjs = ['masculine', 'feminine', 'more masculine', 'more feminine', 'most masculine', 'most feminine']
        p2 = "On the right you'll see a plot of your profile on a scale from most masculine to most feminine. At 0, " \
             "the algorithm is unable to decide if your profile is male or female. The further right you " \
             "are," + 'the more "confident" it is that you are female; likewise, the further left you are, ' \
                      'the more "confident" it is that you are male. The different colored regions are meant to ' \
                      'reflect this level of confidence.'
        p3 = "Below is some information on why the algorithm predicted the gender it did for your Tweets. First is a " \
             "list of the top five words that contributed most to your score. If a word has a weight of .2, that mean" \
             "s that if you removed all instances of that word from your Tweets, your predicted gender score would " \
             "fall by about .2. Below these words are your top five Tweets that are most indicative of each gender. " \
             "The most important words are bolded. Click on the button below these Tweets to see how you can change " \
             "your algorithmic profile."
        dec = 2  # number of decimal points to keep

    elif attr == 'age':
        script, div = make_plot(min_val=0.0, max_val=60.0, score=float(str(p.attr_values).split('\n')[0]),
                                title="Your Lexicographic Age Profile", axis_label="Raw Score",
                                left_label="←\nYounger", right_label="Older→", box=[13, 25, 35, 50],
                                right_label_loc=50.6)
        adjs = ['young', 'old', 'younger', 'older', 'youngest', 'oldest']
        p2 = "On the right you'll see a plot of your profile on a scale from youngest to oldest. " \
             "As" + ' this is a sliding scale of age, there is no measure of "confidence" as in the gender ' \
                    'classifier. The colored regions are meant to represent different age ranges.'
        p3 = "Below is some information on why the algorithm predicted the age it did for your Tweets. " \
             "First is a list of the top five words that contributed most to your score. If a word has a weight of .2," \
             " that means that if you removed all instances of that word from your Tweets, your predicted age would " \
             "fall by about .2. Below these words are your " + 'top five Tweets that sound the "oldest" or "youngest". ' \
                                                               'The most important words are bolded. Click on the ' \
                                                               'button below these Tweets to see how you can change ' \
                                                               'your algorithmic profile.'
        dec = 2  # number of decimal points to keep

    elif attr == 'sentiment':
        script, div = make_plot(min_val=-.75, max_val=.75, score=float(str(p.attr_values).split('\n')[0]),
                                title="Your Lexicographic Sentiment Profile", axis_label="Raw Score",
                                left_label="←\nNegative", right_label="Positive→", box=[-.55, -.1, .1, .55],
                                right_label_loc=.44)
        adjs = ['negative', 'positive', 'more negative', 'more positive', 'most negative', 'most positive']
        p2 = "On the right you'll see a plot of your profile on a scale from most negative to most positive. At 0, " \
             "the " + 'algorithm is unable to decide if your profile is negative or positive. The further right you ' \
                      'are, the more "confident" it is that you are positive; likewise, the further left ' \
                      'you are, the more "confident" it is that you are negative. The different colored regions are ' \
                      'meant to reflect this level of confidence.'
        p3 = "Below is some information on why the algorithm predicted the sentiment it did for your Tweets. First is a" \
             " list of the top five words that contributed most to your score. If a word has a weight of .2, that " \
             "means that if you removed all instances of that word from your Tweets, your predicted sentiment score" \
             " would fall by about .2. Below these words are your top five Tweets that are most indicative of " \
             "each sentiment. The most important words are bolded. Click on the button below these Tweets to see how " \
             "you can change your algorithmic profile."
        dec = 3  # number of decimal points to keep
    else:
        raise Exception("invalid attribute %s" % attr)
    return render(request, 'twitter/lex_info.html', {'script': script, "div": div, 'username': username, 'dec': dec,
                                                     "attr": attr,
                                                     "classifier": p, "paragraphs": [lex_header, p2, p3], "adjs": adjs})


# Allow user to see Big Five Profile based on IBM results.
def ibm_info(request, username):
    profile_list = Profile.objects.filter(username=username, classifier='ibm', is_current=True)

    # Gt openness
    o = profile_list.get(attr_name='openness')
    o_script, o_div = make_plot(min_val=0.0, max_val=100.0, score=float(o.attr_values)*100,
                                title="Your IBM Openness Profile", axis_label='Percentile',
                                left_label="←Less Open", right_label="More Open→", box=[25, 45, 55, 75],
                                right_label_loc=73.5)
    o_desc = "Openness describes how open you are to new experiences. Open people tend to be curious and adventurous," \
             " whereas less open people prefer routine and known experiences. Highly open people (in the dark red " \
             "region) often think abstractly and can be more artistic, as well as more willing to challenge authority."\
             " People with low openness are more concrete and literal and tend to follow the status quo."

    # Get conscientiousness
    c = profile_list.get(attr_name='conscientiousness')
    c_script, c_div = make_plot(min_val=0.0, max_val=100.0, score=float(c.attr_values)*100,
                                title="Your IBM Conscientiousness Profile", axis_label='Percentile',
                                left_label="←Less Conscientious", right_label="More Conscientious→",
                                box=[25, 45, 55, 75],
                                right_label_loc=55)
    c_desc = "Conscientiousness describes how organized and thoughtful you are. Conscientious people are often " \
             "confident and well organized. Less conscientious people are more impulsive and flexible. Highly " \
             "conscientious people are driven and cautious, with strong senses of duty. People with low " \
             "conscientiousness are more easy going and willing to take risks."

    # Get extraversion
    e = profile_list.get(attr_name='extraversion')
    e_script, e_div = make_plot(min_val=0.0, max_val=100.0, score=float(e.attr_values)*100,
                                title="Your IBM Extraversion Profile", axis_label='Percentile',
                                left_label="←More Introverted", right_label="More Extraverted→",
                                box=[25, 45, 55, 75],
                                right_label_loc=61)
    e_desc = "Extraversion describes how often you tend to seek the company of others. Extraverts get energy from " \
             "social situations and are outgoing and busy. Introverts (the opposite of extraverts) need to spend time" \
             " alone and are less likely to seek out social situations. Highly extraverted people enjoy crowds, are " \
             "assertive, and live fast-paced lives. Highly introverted people enjoy quieter settings, stay out of " \
             "the spotlight, and lead more relaxed lives."

    # Get agreeableness
    a = profile_list.get(attr_name='agreeableness')
    a_script, a_div = make_plot(min_val=0.0, max_val=100.0, score=float(a.attr_values)*100,
                                title="Your IBM Agreeableness Profile", axis_label='Percentile',
                                left_label="←Less Agreeable", right_label="More Agreeable→",
                                box=[25, 45, 55, 75],
                                right_label_loc=64)
    a_desc = "Agreeableness describes your tendency to be cooperative and compassionate towards others. Agreeable " \
             "people are empathetic and prefer harmonious atmospheres. Less agreeable people prioritize their own " \
             "opinions over others and tend to be more direct. Highly agreeable people may avoid conflict, even at the" \
             "expense of their own well-being, but are also modest and enjoy helping others. People with low " \
             "agreeableness are argumentative, skeptical, and principled."

    # Get neuroticism
    n = profile_list.get(attr_name='neuroticism')
    n_script, n_div = make_plot(min_val=0.0, max_val=100.0, score=float(n.attr_values)*100,
                                title="Your IBM Neuroticism Profile", axis_label='Percentile',
                                left_label="←Less Neurotic", right_label="More Neurotic→",
                                box=[25, 45, 55, 75],
                                right_label_loc=67)
    n_desc = "Neuroticism, also called emotional range, describes how much your emotions change relative to your " \
             "environment. Neurotic people can be more sensitive and experience emotional highs and lows more " \
             "frequently. Less neurotic people tend to be more emotionally steady and don't let many things change " \
             "their mood. Highly neurotic people can be anxious or easy to anger but also more self-aware and able to" \
             " get more joy from small pleasures. People with low neuroticism handle stress and emergencies well, and " \
             "tend to think more in the long term."

    return render(request, 'twitter/ibm_info.html', {'username': username,
                                                     'scripts': [o_script, c_script, e_script, a_script, n_script],
                                                     "divs": [o_div, c_div, e_div, a_div, n_div],
                                                     "descriptions": [o_desc, c_desc, e_desc, a_desc, n_desc]})


# Allow user to see M3 results of profile of Twitter profile
def m3_info(request, username, attr):
    p = Profile.objects.get(username=username, attr_name=attr, classifier='m3', is_current=True)
    scores = p.attr_values.split('\n')
    scores = [float(x) * 100 for x in scores]

    p1 = "This profile was generated using the M3 Twitter Inference Model. This classifier looks at Twitter account" \
         " information such as username, display name, profile picture, and bio. It profiles age, gender, and " \
         "organizational status together using a large neural network. This network uses several techniques from deep " \
         "learning which are often especially difficult for humans to interpret. Additionally, as all three profiles " \
         "are estimated together, it may be difficult to separate how each one is generated individually."

    if attr == 'gender':
        title = 'M3 Gender Profile'
        p2 = "On the right is your gender profile. 100% confidence indicates maximal certainty. If each category has " \
             "50% confidence, then the classifier is completely unsure as to which gender you are."
        p3 = ""
        dec = 2  # number of decimal points to keep

    elif attr == 'organization':
        title = 'M3 Organization Profile'
        p2 = "On the right is your organization profile. This attribute is meant to tell if the Twitter account is " \
             "personal or one run by an organization. Non-organization means a personal account, whereas organization " \
             "means an account run by a corporation or institution. " \
             "100% confidence means that the classifier is fully confident in its prediction. If each category " \
             "has 50% confidence, then the classifier is completely unsure as to whether or not you are an " \
             "organization."
        p3 = ""
        dec = 2  # number of decimal points to keep

    elif attr == 'age':
        title = 'M3 Age Profile'
        p2 = "On the right is your age profile. 100% confidence indicates maximal certainty. If each category has 25% " \
             "confidence, then the classifier is completely unsure as to which age group you are."
        p3 = ""
        dec = 2  # number of decimal points to keep
    else:
        raise Exception("Unexpected attribute %s" % attr)

    script, div = make_bar(scores=scores, categories=p.attr_categories.split('\n'), title=title)

    return render(request, 'twitter/m3_info.html', {'script': script, "div": div, 'username': username, 'dec': dec,
                                                    "attr": attr,
                                                    "classifier": p, "paragraphs": [p1, p2, p3]})


# Allow user to see results from TextBlob
def blob_info(request, username, attr):
    if attr == 'polarity':
        p = Profile.objects.get(username=username, attr_name='sentiment', classifier='blob', extra_info='pattern',
                                is_current=True)

        script, div = make_plot(min_val=-1.0, max_val=1.0, score=float(p.attr_values),
                                title="Your Pattern Sentiment Profile", axis_label="Raw Score",
                                left_label="←\nNegative", right_label="Positive→", box=[-0.85, -.15, .15, .85],
                                right_label_loc=.58)
        adjs = ['negative', 'positive', 'more negative', 'more positive', 'most negative', 'most positive']
        p1 = 'Here are your sentiment results for the Pattern profiling. This tool relies on a dictionary of words,' \
             ' each with specific weights indicating sentiment. It is more complex than a simple lexical analysis ' \
             'as it also uses part of speech information to determine a bit more about the sense of the words being ' \
             'used.'
        p2 = "On the right you'll see a plot of your profile on a scale from most negative to most positive. This " \
             "represents the algorithm's predicted probability of your profile being positive. A value of 0.5 means " \
             "that the algorithm is unsure which class you are and is basically flipping a coin. A value of 1.0 means " \
             "that the algorithm has no doubt that your profile is positive, similarly a value of 0.0 means that the " \
             "algorithm has no doubt that your profile is negative."
        p3 = "Below is some information on why the algorithm predicted the sentiment it did for your Tweets. First is a" \
             " list of the top five words that contributed most to your score. If a word has a weight of .2, that " \
             "means that if you removed all instances of that word from your Tweets, your predicted sentiment score" \
             " would fall by about .2. Below these words are your top five Tweets that are most indicative of " \
             "each sentiment. The most important words are bolded. Click on the button below these Tweets to see how " \
             "you can change your algorithmic profile."
        dec = 4  # number of decimal points to keep

    elif attr == 'subjectivity':
        p = Profile.objects.get(username=username, attr_name='subjectivity', classifier='blob', extra_info='pattern',
                                is_current=True)
        script, div = make_plot(min_val=0, max_val=1.0, score=float(p.attr_values),
                                title="Your Pattern Subjectivity Profile", axis_label="Raw Score",
                                left_label="←\nObjective", right_label="Subjective→", box=[.15, .4, .6, .85],
                                right_label_loc=.65)
        adjs = ['objective', 'subjective', 'more objective', 'more subjective', 'most objective', 'most subjective']
        p1 = 'Here are your subjectivity results for the Pattern profiling. This tool relies on a dictionary of words,' \
             ' each with specific weights indicating subjectivity. It is more complex than a simple lexical analysis ' \
             'as it also uses part of speech information to determine a bit more about the sense of the words being ' \
             'used. A subjective profile means you tend to express opinions, whereas an objective profile means you ' \
             'tend to report facts.'
        p2 = "On the right you'll see a plot of your profile on a scale from most objective to most subjective. At 0, " \
             "the " + 'algorithm is unable to decide if your profile is objective or subjective. The further right you ' \
                      'are, the more "confident" it is that you are objective; likewise, the further left ' \
                      'you are, the more "confident" it is that you are subjective. The different colored regions are ' \
                      'meant to reflect this level of confidence.'
        p3 = "Below is some information on why the algorithm predicted the subjectivity it did for your Tweets. First is a" \
             " list of the top five words that contributed most to your score. If a word has a weight of .2, that " \
             "means that if you removed all instances of that word from your Tweets, your predicted subjectivity score" \
             " would fall by about .2. Below these words are your top five Tweets that are most indicative of " \
             "each class. The most important words are bolded. Click on the button below these Tweets to see how " \
             "you can change your algorithmic profile."
        dec = 4  # number of decimal points to keep

    elif attr == 'nbc':
        p = Profile.objects.get(username=username, attr_name='sentiment', classifier='blob',
                                extra_info='naive bayes classifier', is_current=True)
        script, div = make_plot(min_val=0, max_val=100, score=float(p.class_confidence)*100,
                                title="Your NBC Sentiment Profile", axis_label="Percent Confidence",
                                left_label="←\nNegative", right_label="Positive→", box=[15, 40, 60, 85],
                                right_label_loc=79)
        adjs = ['negative', 'positive', 'more negative', 'more positive', 'most negative', 'most positive']
        p1 = 'Here are your sentiment results for the Naive Bayes Classifier profiling. This tool relies on a ' \
             'machine learning algorithm trained over two thousand movie reviews. It learns to how different words ' \
             'are associated to specific types of profiles. To get a profile, it considers all words, finds the ' \
             'likelihood the profile belongs to each type based on these words, and then predicts the type with the ' \
             'highest probability.'
        p2 = "On the right you'll see a plot of your profile on a scale from most negative to most positive. At 50%, " \
             "the " + 'algorithm is unable to decide if your profile is negative or positive. The further right you ' \
                      'are, the more "confident" it is that you are positive; likewise, the further left ' \
                      'you are, the more "confident" it is that you are negative. The different colored regions are ' \
                      'meant to reflect this level of confidence.'
        p3 = "Below are the Tweets for which the classifier has the highest confidence. Individual explanations of " \
             "Tweets are available from the editing pages."
        dec = 2  # number of decimal points to keep

    else:
        raise Exception("Unexpected value %s" % attr)

    return render(request, 'twitter/blob_info.html', {'script': script, "div": div, 'username': username, 'dec': dec,
                                                      "attr": attr,
                                                      "classifier": p, "paragraphs": [p1, p2, p3], "adjs": adjs})


# Allow user to see results from classifiers
def clf_info(request, username, attr):
    if attr == 'income':
        p = Profile.objects.get(username=username, attr_name=attr, extra_info='clf', is_current=True)

        script, div = make_plot(min_val=0, max_val=100, score=float(p.attr_values)/1000,
                                title="Your Income Profile", axis_label="Predicted Income in Thousands of Pounds",
                                left_label="←\nLower", right_label="Higher→", box=[20, 28, 37, 60],
                                right_label_loc=82)
        adjs = [['low income', 'high income'], ['lower income', 'higher income'], ['lowest income', 'highest income']]
        p1 = 'Here are the results for your income profiling. The number predicted is your annual income. The ' \
             'regression model is a feed-forward neural network based on the frequency of words in your Tweets. Neural ' \
             'networks are the most complex classifiers included in this experiment and it is in general very difficult' \
             ' for humans to understand how they make the profiling decisions they do.'
        p2 = "To train this regression model, occupations were determined from Twitter bios and each user was assigned " \
             "the average income for their profession according to the UK Office of National Statistics. The average " \
             "income in the data was £32,516. The colored sections are meant to represent your predicted income's " \
             "distance from the average."
        p3 = ""
        dec = 4  # number of decimal points to keep

    elif attr == 'income (categorical)':
        p = Profile.objects.get(username=username, attr_name=attr, extra_info='clf', is_current=True)

        vals = p.attr_values.split('\n')
        vals = [float(x)*100 for x in vals]

        script, div = make_bar(vals, p.attr_categories.split('\n'), 'Income Level Profile')
        adjs = [['below average', 'above average', 'far above average'],
                ['more below average', 'more above average', 'more far above average'],
                ['most below average', 'most above average', 'most far above average']]
        p1 = 'Here are the results for your income profiling. The category prediction represents your predicted  ' \
             'annual income. For reference, the average annual income when calculating this profile was £32,516.' \
             'The classifier is a feed-forward neural network based on ' \
             'the frequency of words in your Tweets. Neural networks are the most complex classifiers included in this' \
             ' experiment and it is in general very difficult for humans to understand how they make the profiling ' \
             'decisions they do.'
        p2 = "On the right is a bar graph of the probability of you being in each class. At 100%, the classifiers is " \
             "certain that you are in that class, at 33% each, the classifier is completely unsure which class you " \
             "belong to."
        p3 = "You can click above to see an explanation of your profile. Click the boxes below to see your Tweets " \
             "and how each one relates to each class. Note that there may be no Tweets related to a particular class." \
             " This may take a bit of time to load."
        dec = 4  # number of decimal points to keep

    elif attr == 'education':
        p = Profile.objects.get(username=username, attr_name=attr, extra_info='clf', is_current=True)

        vals = p.attr_values.split('\n')
        vals = [float(x)*100 for x in vals]

        script, div = make_bar(vals, p.attr_categories.split('\n'), 'Education Level Profile')
        # adjs = [['high school', 'undergraduate', 'graduate'], ['more high school', 'more undergraduate',
        #                                                        'more graduate'],
        #         ['most high school', 'most undergraduate', 'most graduate']]
        adjs = [['high school', 'college'], ['more high school', 'more college'], ['most high school', 'most college']]
        p1 = 'Here are the results for your education profiling. The category prediction represents the highest ' \
             'educational level you have attained. The classifier is a feed-forward neural network based on ' \
             'the frequency of words in your Tweets. Neural networks are the most complex classifiers included in this' \
             ' experiment and it is in general very difficult for humans to understand how they make the profiling ' \
             'decisions they do.'
        p2 = "On the right is a bar graph of the probability of you being in each class. At 100%, the classifiers is " \
             "certain that you are in that class, at 50% each, the classifier is completely unsure which class you " \
             "belong to."
        p3 = "You can click above to see an explanation of your profile. Click the boxes below to see your Tweets " \
             "and how each one relates to each class. Note that there may be no Tweets related to a particular class." \
             " This may take a bit of time to load."
        dec = 4  # number of decimal points to keep

    elif attr == 'relationship':
        p = Profile.objects.get(username=username, attr_name=attr, extra_info='clf', is_current=True)

        vals = p.attr_values.split('\n')
        vals = [float(x) * 100 for x in vals]

        script, div = make_bar(vals, p.attr_categories.split('\n'), 'Relationship Status Profile')
        adjs = [['available', 'taken'], ['more available', 'more taken'],
                ['most available', 'most taken']]
        p1 = 'Here are the results for your relationship status profiling. A prediction of "available" means that you' \
             ' are not currently in a relationship (single or divorced) and a prediction of "taken" means that you ' \
             'are in a romantic relationship or ' \
             '"it' + "'" + 's complicated." The classifier is a feed-forward neural ' \
                           'network based on the frequency of words in your Tweets. Neural networks are the most ' \
                           'complex classifiers included in this experiment and it is in general very difficult for ' \
                           'humans to understand how they make the profiling decisions they do.'
        p2 = "On the right is a bar graph of the probability of you being in each class. At 100%, the classifiers is " \
             "certain that you are in that class, at 50% each, the classifier is completely unsure which class you " \
             "belong to."
        p3 = "You can click above to see an explanation of your profile. Click the boxes below to see your Tweets " \
             "and how each one relates to each class. Note that there may be no Tweets related to a particular class." \
             " This may take a bit of time to load."
        dec = 4  # number of decimal points to keep

    elif attr == 'politics':
        p = Profile.objects.get(username=username, attr_name=attr, extra_info='clf', is_current=True)

        vals = p.attr_values.split('\n')
        vals = [float(x) * 100 for x in vals]

        script, div = make_bar(vals, p.attr_categories.split('\n'), 'Politics Profile')
        adjs = [['non-political', 'political'], ['less political', 'more political'],
                ['least political', 'most political']]
        p1 = 'Here are the results for your political profiling. A prediction of "political" means that you' \
             ' are generally politically active and a prediction of "non-political" means that you ' \
             'do not care about politics. The classifier is a feed-forward neural " \
                        "network based on the frequency of words in your Tweets. Neural networks are the most complex " \
                        "classifiers included in this experiment and it is in general very difficult for humans to " \
                        "understand how they make the profiling decisions they do.'
        p2 = "On the right is a bar graph of the probability of you being in each class. At 100%, the classifiers is " \
             "certain that you are in that class, at 50% each, the classifier is completely unsure which class you " \
             "belong to."
        p3 = "You can click above to see an explanation of your profile. Click the boxes below to see your Tweets " \
             "and how each one relates to each class. Note that there may be no Tweets related to a particular class." \
             " This may take a bit of time to load."
        dec = 4  # number of decimal points to keep

    elif attr == 'religion':
        p = Profile.objects.get(username=username, attr_name=attr, extra_info='clf', is_current=True)

        vals = p.attr_values.split('\n')
        vals = [float(x) * 100 for x in vals]

        script, div = make_bar(vals, p.attr_categories.split('\n'), 'Religion Profile')
        adjs = [['non-Christian', 'Christian'], ['less Christian', 'more Christian'],
                ['least Christian', 'most Christian']]
        p1 = 'Here are the results for your religion profiling. A prediction of "Christian" means that you' \
             ' identify as a Christian denomination and a prediction of "non-Christian" means that you ' \
             'do not. A label of non-Christian includes other religions such as Judiaism, Islam, and Hinduism as well ' \
             'as athiest, non-religions, or agnostic belief systems. The classifier is a feed-forward neural " \
                        "network based on the frequency of words in your Tweets. Neural networks are the most complex " \
                        "classifiers included in this experiment and it is in general very difficult for humans to " \
                        "understand how they make the profiling decisions they do.'
        p2 = "On the right is a bar graph of the probability of you being in each class. At 100%, the classifiers is " \
             "certain that you are in that class, at 50% each, the classifier is completely unsure which class you " \
             "belong to."
        p3 = "You can click above to see an explanation of your profile. Click the boxes below to see your Tweets " \
             "and how each one relates to each class. Note that there may be no Tweets related to a particular class." \
             " This may take a bit of time to load."
        dec = 4  # number of decimal points to keep

    elif attr == 'race':
        p = Profile.objects.get(username=username, attr_name=attr, extra_info='clf', is_current=True)

        vals = p.attr_values.split('\n')
        vals = [float(x) * 100 for x in vals]

        script, div = make_bar(vals, p.attr_categories.split('\n'), 'Race Profile')
        adjs = [['non-white', 'white'], ['less white', 'more white'],
                ['least white', 'most white']]
        p1 = 'Here are the results for your race profiling. A prediction of "white" means that you' \
             ' consider yourself ethnicity as Caucasian or white and a prediction of "non-white" means that you ' \
             'do not. The classifier is a feed-forward neural " \
                        "network based on the frequency of words in your Tweets. Neural networks are the most complex " \
                        "classifiers included in this experiment and it is in general very difficult for humans to " \
                        "understand how they make the profiling decisions they do.'
        p2 = "On the right is a bar graph of the probability of you being in each class. At 100%, the classifiers is " \
             "certain that you are in that class, at 50% each, the classifier is completely unsure which class you " \
             "belong to."
        p3 = "You can click above to see an explanation of your profile. Click the boxes below to see your Tweets " \
             "and how each one relates to each class. Note that there may be no Tweets related to a particular class." \
             " This may take a bit of time to load."
        dec = 4  # number of decimal points to keep

    return render(request, 'twitter/clf_info.html', {'script': script, "div": div, 'username': username, 'dec': dec,
                                                     "attr": attr,
                                                     "classifier": p, "paragraphs": [p1, p2, p3], "adjs": adjs})
