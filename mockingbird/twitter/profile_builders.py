# Libraries
from ibm_watson import PersonalityInsightsV3
import locale
from m3inference import M3Twitter
from textblob import TextBlob

# Local files
from classifiers.get_lex import *
from twitter.models import Profile, Tweet, explanations_to_string, NBC_BLOBBER, User
from .classifier_helpers import get_clf_scores, graph


# Build a Big Five profile using IBM API
def build_ibm(username):
    # Prepare authentication
    personality_insights = PersonalityInsightsV3(
        version='2017-10-13',
        iam_apikey=,  # add your own key here
        url='https://gateway-lon.watsonplatform.net/personality-insights/api'
    )

    # Read tweets
    tweets = Tweet.objects.filter(username=username, is_active=True)
    tweets = '\n'.join([x.tweet for x in tweets])

    profile = personality_insights.profile(
        tweets,
        'application/json',
        consumption_preferences=True,
        raw_scores=True,
        csv_headers=True
    ).get_result()

    # Save profile results based on this
    traits = []
    for trait in profile['personality']:
        name = trait['name']
        if name == 'Emotional range':
            name = 'neuroticism'  # Rename this to be more similar to other Big Five names
            prediction = 'Neurotic' if float(trait['percentile']) > 0.5 else 'Not Neurotic'
            categories = 'Not Neurotic\nNeurotic'
            category_desc ='Less Neurotic\nMore Neurotic'

        elif name == 'Openness':
            name = 'openness'
            prediction = 'Open' if float(trait['percentile']) > 0.5 else 'Not Open'
            categories = 'Not Open\nOpen'
            category_desc ='Less Open\nMore Open'

        elif name == 'Conscientiousness':
            name = 'conscientiousness'
            prediction = 'Conscientious' if float(trait['percentile']) > 0.5 else 'Not Conscientious'
            categories = 'Not Conscientious\nConscientious'
            category_desc ='Less Conscientious\nMore Conscientious'

        elif name == 'Extraversion':
            name = 'extraversion'
            prediction = 'Extraverted' if float(trait['percentile']) > 0.5 else 'Introverted'
            categories = 'Introverted\nExtraverted'
            category_desc ='Introverted\nExtraverted'

        elif name == 'Agreeableness':
            name = 'agreeableness'
            prediction = 'Agreeable' if float(trait['percentile']) > 0.5 else 'Not Agreeable'
            categories = 'Not Agreeable\nAgreeable'
            category_desc ='Less Agreeable\nMore Agreeable'

        else:
            raise Exception("Unexpected name %s" % name)

        p = Profile(username=username, attr_name=name, classifier='ibm', predicted_class=prediction,
                    attr_categories=categories, category_desc=category_desc,
                    attr_values=trait['percentile'],
                    confidence_str=min(100, int(float(trait['percentile'])*100)),
                    explanations='',
                    global_explanations='', is_current=True, class_confidence=trait['raw_score'], is_sensitive=False)
        p.save()
        traits.append(p)
    return traits


# Get profile from Twitter profile data from M3Insights
def build_m3(username):
    # Gather info
    m3twitter = M3Twitter()
    res = m3twitter.infer_screen_name(username)

    # Separate profile elements
    prfs = []
    for attr in res['output']:
        keys = list(res['output'][attr].keys())
        vals = list(res['output'][attr].values())

        if attr == 'gender':
            category_desc = 'more masculine\nmore feminine'
        elif attr == 'age':
            category_desc = 'eighteen or younger\ntwenties\nthirties\nover forty'
        elif attr == 'org':
            attr = 'organization'
            category_desc = 'less like an organization\nmore like an organization'
            keys[0] = 'non-organization'
            keys[1] = 'organization'
        else:
            raise Exception("Unexpected M3 category %s" % attr)

        score = max(vals)
        if score < 0.6:
            conf_str = 'low'
        elif 0.6 <= score <= .85:
            conf_str = 'moderate'
        else:
            conf_str = 'high'

        p = Profile(username=username, attr_name=attr, classifier='m3', predicted_class=keys[vals.index(max(vals))],
                    class_confidence=max(vals), confidence_str=conf_str, attr_categories='\n'.join(keys),
                    attr_values='\n'.join([str(x) for x in vals]), category_desc=category_desc,
                    explanations='', global_explanations='', is_current=True, is_sensitive=False)
        p.save()
        prfs.append(p)

    # Return profiles
    return tuple(prfs)


# Build a new lexicographic profile
def build_lex_profile(username, attr_name):

    # Read and score tweets
    tweets = '\n'.join([x.tweet for x in Tweet.objects.filter(username=username, is_active=True)])
    score, largest, smallest = lex_classify(tweets, attr_name, include_weights=True)
    l, s = get_lex_extremes(attr_name, include_weights=True)

    if attr_name == 'gender':
        prediction = 'male' if score < 0 else 'female'
        attr_categories = 'male\nfemale'
        category_desc = 'most masculine\nmost feminine'
        if score < -1.25 or score > 1.25:
            confidence_str = "high"
        elif -1.25 < score < -.25 or .25 < score < 1.25:
            confidence_str = "moderate"
        else:
            confidence_str = 'low'

    elif attr_name == 'age':
        prediction = int(score)
        attr_categories = 'young\nold'
        category_desc = 'youngest\noldest'
        confidence_str = 'N/A'

    elif attr_name == 'sentiment':
        prediction = 'negative' if score < 0 else 'positive'
        attr_categories = 'negative\npositive'
        category_desc = 'most negative\nmost positive'
        if score < -.55 or score > .55:
            confidence_str = "high"
        elif -.55 < score < -.1 or .1 < score < .55:
            confidence_str = "moderate"
        else:
            confidence_str = 'low'
    else:
        raise Exception("Invalid attribute name", attr_name)

    p = Profile(username=username, attr_name=attr_name, classifier='lexicon', predicted_class=prediction,
                attr_categories=attr_categories, category_desc=category_desc,
                attr_values=str(score) + '\n' + str(score), confidence_str=confidence_str,
                explanations=explanations_to_string([smallest, largest]),
                global_explanations=explanations_to_string([s, l]), is_current=True, class_confidence=score,
                is_sensitive=False)
    p.save()
    return p


# Get sentiment analysis info from textblob
def build_blob(username):

    # Read tweets
    tweets = Tweet.objects.filter(username=username, is_active=True)
    tweets = '\n'.join([x.tweet for x in tweets])

    # Get basic analysis from pattern library
    pat = TextBlob(tweets).sentiment
    pat_sent = pat.polarity
    prediction = 'negative' if pat_sent <= 0 else 'positive'
    if pat_sent < -0.85 or pat_sent > 0.85:
        conf_str = 'high'
    elif -0.85 < pat_sent < 0.1 or 0.1 < pat_sent < 0.85:
        conf_str = 'moderate'
    else:
        conf_str = 'low'
    _, largest, smallest = lex_classify(tweets, 'polarity', include_weights=True)
    l, s = get_lex_extremes('polarity', include_weights=True)
    p_pat_sent = Profile(username=username, attr_name='sentiment', classifier='blob', predicted_class=prediction,
                         attr_categories='negative\npositive', category_desc='most negative\nmost positive',
                         attr_values=pat_sent,
                         confidence_str=conf_str,
                         explanations=explanations_to_string([smallest, largest]), extra_info='pattern',
                         global_explanations=explanations_to_string([s, l]), is_current=True, class_confidence=pat_sent,
                         is_sensitive=False)
    p_pat_sent.save()

    # Get subjectivity from pattern library
    pat_sub = pat.subjectivity
    prediction = 'objective' if pat_sub <= 0 else 'subjective'
    if pat_sub < .15 or pat_sub > 0.85:
        conf_str = 'high'
    elif .15 <= pat_sub < 0.4 or 0.6 < pat_sub <= 0.85:
        conf_str = 'moderate'
    else:
        conf_str = 'low'
    _, largest, smallest = lex_classify(tweets, 'subjectivity', include_weights=True)

    l, s = get_lex_extremes('subjectivity', include_weights=True)
    p_pat_sub = Profile(username=username, attr_name='subjectivity', classifier='blob', predicted_class=prediction,
                        attr_categories='objective\nsubjective', category_desc='most objective\nmost subjective',
                        attr_values=pat_sub,
                        confidence_str=conf_str,
                        explanations=explanations_to_string([smallest, largest]), extra_info='pattern',
                        global_explanations=explanations_to_string([s, l]), is_current=True, class_confidence=pat_sub,
                        is_sensitive=False)
    p_pat_sub.save()

    # Get analysis from NaiveBayes
    pat = NBC_BLOBBER(tweets).sentiment
    pat_nbc = pat.p_pos

    prediction = 'negative' if pat.classification == 'neg' else 'positive'
    if pat_nbc < 0.6:
        conf_str = 'low'
    elif .6 <= pat_nbc < 0.85:
        conf_str = 'moderate'
    else:
        conf_str = 'high'
    p_nbc = Profile(username=username, attr_name='sentiment', classifier='blob', predicted_class=prediction,
                    attr_categories='negative\npositive', category_desc='most negative\nmost positive',
                    attr_values=str(pat.p_neg) + '\n' + str(pat_nbc),
                    confidence_str=conf_str,
                    explanations='', extra_info='naive bayes classifier',
                    global_explanations='', is_current=True, class_confidence=pat_nbc,
                    is_sensitive=False)
    p_nbc.save()

    return p_pat_sent, p_pat_sub, p_nbc


# Build profiles from trained classifiers
def build_clf(username):
    # Remove any potentially active profiles
    active = Profile.objects.filter(username=username, is_current=True)
    for a in active:
        a.is_current = False
        a.save()

    # Read tweets
    tweets = Tweet.objects.filter(username=username, is_active=True)
    tweets = '\n'.join([x.tweet for x in tweets])

    # See if we have permission for sensitive profiles
    u = User.objects.get(username=username)
    score = get_clf_scores(tweets, u.use_sensitive)

    locale.setlocale(locale.LC_ALL, 'en_GB')

    inc = Profile(username=username, attr_name='income', classifier='Neural Network Regression',
                  predicted_class='£' + locale.format_string("%d", score[0], grouping=True),
                  attr_categories='low income\nhigh income', category_desc='lowest income\nhighest income',
                  attr_values=int(score[0]),
                  confidence_str='N/A',
                  explanations='', extra_info='clf',
                  global_explanations='', is_current=True, class_confidence=int(score[0]),
                  is_sensitive=False)
    inc.save()

    inc_cat_probs = score[1]
    confidence = max(inc_cat_probs)
    if inc_cat_probs.index(confidence) == 0:
        predicted_class = 'below average'
    elif inc_cat_probs.index(confidence) == 1:
        predicted_class = 'above average'
    else:
        predicted_class = 'far above average'

    if confidence <= 0.6:
        confidence_str = 'low'
    elif confidence >= 0.8:
        confidence_str = 'high'
    else:
        confidence_str = 'medium'

    inc_cat = Profile(username=username, attr_name='income (categorical)', classifier='Neural Network',
                      predicted_class=predicted_class,
                      attr_categories='below average\nabove average\nfar above average',
                      category_desc='lower income\nupper income\nhighest income',
                      attr_values='\n'.join([str(x) for x in inc_cat_probs]), confidence_str=confidence_str,
                      explanations='', extra_info='clf',
                      global_explanations='', is_current=True, class_confidence=confidence,
                      is_sensitive=False)
    inc_cat.save()

    edu_probs = score[2]
    confidence = max(edu_probs)
    if edu_probs.index(confidence) == 0:
        predicted_class = 'high school'
    else:
        predicted_class = 'college'
    # elif edu_probs.index(confidence) == 1:
    #     predicted_class = 'undergraduate degree'
    # else:
    #     predicted_class = 'graduate degree'

    if confidence <= 0.6:
        confidence_str = 'low'
    elif confidence >= 0.8:
        confidence_str = 'high'
    else:
        confidence_str = 'medium'

    edu = Profile(username=username, attr_name='education', classifier='Neural Network',
                  predicted_class=predicted_class, attr_categories='high school\ncollege',
                  category_desc='least educated\nmost educated',
                  attr_values='\n'.join([str(x) for x in edu_probs]), confidence_str=confidence_str,
                  explanations='', extra_info='clf',
                  global_explanations='', is_current=True, class_confidence=confidence, is_sensitive=False)
    edu.save()

    # edu = Profile(username=username, attr_name='education', classifier='Neural Network',
    #               predicted_class=predicted_class, attr_categories='high school\nundergraduate degree\ngraduate degree',
    #               category_desc='least educated\nsomewhat educated\nmost educated',
    #               attr_values='\n'.join([str(x) for x in edu_probs]), confidence_str=confidence_str,
    #               explanations='', extra_info='clf',
    #               global_explanations='', is_current=True, class_confidence=confidence, is_sensitive=False)
    # edu.save()

    # Get relationship status information
    rel_probs = score[3]
    confidence = max(rel_probs)
    if rel_probs.index(confidence) == 0:
        predicted_class = 'available'
    elif rel_probs.index(confidence) == 1:
        predicted_class = 'taken'

    if confidence <= 0.6:
        confidence_str = 'low'
    elif confidence >= 0.8:
        confidence_str = 'high'
    else:
        confidence_str = 'medium'

    rel = Profile(username=username, attr_name='relationship', classifier='Neural Network',
                  predicted_class=predicted_class, attr_categories='available\ntaken',
                  category_desc='most available\nmost taken',
                  attr_values='\n'.join([str(x) for x in rel_probs]), confidence_str=confidence_str,
                  explanations='', extra_info='clf',
                  global_explanations='', is_current=True, class_confidence=confidence,
                  is_sensitive=False)
    rel.save()

    # Get sensitive information
    if u.use_sensitive:
        # Get politics information
        pol_probs = score[4]
        confidence = max(pol_probs)
        if pol_probs.index(confidence) == 0:
            predicted_class = 'non-political'
        elif pol_probs.index(confidence) == 1:
            predicted_class = 'politial'

        if confidence <= 0.6:
            confidence_str = 'low'
        elif confidence >= 0.8:
            confidence_str = 'high'
        else:
            confidence_str = 'medium'

        pol = Profile(username=username, attr_name='politics', classifier='Neural Network',
                      predicted_class=predicted_class, attr_categories='non-political\npolitical',
                      category_desc='least political\nmost political',
                      attr_values='\n'.join([str(x) for x in pol_probs]), confidence_str=confidence_str,
                      explanations='', extra_info='clf',
                      global_explanations='', is_current=True, class_confidence=confidence, is_sensitive=True)
        pol.save()

        # Get religion information
        relig_probs = score[5]
        confidence = max(relig_probs)
        if relig_probs.index(confidence) == 0:
            predicted_class = 'non-Christian'
        elif relig_probs.index(confidence) == 1:
            predicted_class = 'Christian'

        if confidence <= 0.6:
            confidence_str = 'low'
        elif confidence >= 0.8:
            confidence_str = 'high'
        else:
            confidence_str = 'medium'

        relig = Profile(username=username, attr_name='religion', classifier='Neural Network',
                        predicted_class=predicted_class, attr_categories='non-Christian\nChristian',
                        category_desc='least Christian\nmost Christian',
                        attr_values='\n'.join([str(x) for x in relig_probs]), confidence_str=confidence_str,
                        explanations='', extra_info='clf',
                        global_explanations='', is_current=True, class_confidence=confidence, is_sensitive=True)
        relig.save()

        # Get race information
        race_probs = score[6]
        confidence = max(race_probs)
        if race_probs.index(confidence) == 0:
            predicted_class = 'non-white'
        elif race_probs.index(confidence) == 1:
            predicted_class = 'white'

        if confidence <= 0.6:
            confidence_str = 'low'
        elif confidence >= 0.8:
            confidence_str = 'high'
        else:
            confidence_str = 'medium'

        race = Profile(username=username, attr_name='race', classifier='Neural Network',
                       predicted_class=predicted_class, attr_categories='non-white\nwhite',
                       category_desc='least white\nmost white',
                       attr_values='\n'.join([str(x) for x in race_probs]), confidence_str=confidence_str,
                       explanations='', extra_info='clf',
                       global_explanations='', is_current=True, class_confidence=confidence, is_sensitive=True)
        race.save()

        sen = [pol, relig, race]
    else:
        sen = None

    return inc, inc_cat, edu, rel, sen
