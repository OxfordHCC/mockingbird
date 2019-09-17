# From libraries
# import nltk
# nltk.download('wordnet')
from nltk.corpus import wordnet
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import Label, BoxAnnotation
from bokeh.palettes import RdBu, Category10

# From local files
from twitter.profile_builders import *


# Get most useful synonyms
def get_syns(words, target, attr_name, n=5):

    # Ensure that popping doesn't change the original word list
    words_copy = words.copy()

    # Get lexicon
    lex = name_to_lex(attr_name)[0]

    # Compile list of synonyms
    per_word = []
    for word in words_copy:
        syns = []
        for syn in wordnet.synsets(word):
            for lm in syn.lemmas():
                syns.append(lm.name())
        # Add weight to words which are frequently listed as synonyms
        syns_weighted = [(key, value*lex[key]) for key, value in Counter(syns).most_common() if key in lex]
        # Get rid of synonyms with weights working against target
        if target == 0:
            syns_weighted = [(x[0], x[1]) for x in syns_weighted if float(x[1]) <= 0]
            syns_weighted.sort(key=lambda x: x[1])
        else:
            syns_weighted = [(x[0], x[1]) for x in syns_weighted if float(x[1]) >= 0]
            syns_weighted.sort(key=lambda x: x[1], reverse=True)
        per_word.append(syns_weighted)

    # Get five "best" synonyms
    synonym_list = []
    while len(synonym_list) < n and len(words_copy) > 0:
        word = words_copy.pop(0)
        syns = per_word.pop(0)
        if syns:
            syn, _ = syns.pop(0)
            synonym_list.append((word + "→" + syn))
            # Don't bother to check this word again if it's empty
            if syns:
                words_copy.append(word)
                per_word.append(syns)

    return synonym_list


# Make a plot based on the input parameters
def make_plot(min_val, max_val, score, title, axis_label, left_label, right_label, box, right_label_loc):
    adjusted_score = min(max_val, max(min_val, score))  # Shrink any possible extremes

    plot = figure(x_range=(min_val, max_val), title=title)
    # Add data point and configure rest of plot
    plot.xaxis.axis_label = axis_label
    plot.circle([adjusted_score], [0.5], size=10, color="black")
    plot.yaxis.visible = False
    plot.grid.visible = False
    plot.plot_height = 200
    plot.plot_width = 350
    plot.outline_line_color = None

    # Add box annotations
    pal = RdBu[5]
    alpha = 0.4
    box_1 = BoxAnnotation(left=min_val, right=box[0], fill_alpha=alpha, fill_color=pal[0])
    box_2 = BoxAnnotation(left=box[0], right=box[1], fill_alpha=alpha, fill_color=pal[1])
    box_3 = BoxAnnotation(left=box[1], right=box[2], fill_alpha=alpha, fill_color=pal[2])
    box_4 = BoxAnnotation(left=box[2], right=box[3], fill_alpha=alpha, fill_color=pal[3])
    box_5 = BoxAnnotation(left=box[3], right=max_val, fill_alpha=alpha, fill_color=pal[4])
    plot.add_layout(box_1)
    plot.add_layout(box_2)
    plot.add_layout(box_3)
    plot.add_layout(box_4)
    plot.add_layout(box_5)

    # Add labels
    left = Label(x=min_val, y=-.5, x_units='data', y_units='data', text=left_label, render_mode='canvas',
                 text_font_size='10pt', text_color='black', text_font_style='bold')
    right = Label(x=right_label_loc, y=-.5, text=right_label, render_mode='canvas', text_font_size='10pt',
                  text_color='black', text_font_style='bold')
    profile = Label(x=adjusted_score, y=0.6, text="Your Profile",
                    render_mode='css', text_font_size='10pt')
    plot.add_layout(left)
    plot.add_layout(right)
    plot.add_layout(profile)

    return components(plot)


# Make a plot based on the input parameters
def make_bar(scores, categories, title):

    plot = figure(y_range=(0, 100), x_range=categories, plot_height=250, title=title, toolbar_location=None, tools="")

    # Add data point and configure rest of plot
    plot.xaxis.axis_label = "Category"
    plot.yaxis.axis_label = "Percent Confidence"

    plot.vbar(x=categories, top=scores, width=0.9, color=Category10[10][:len(scores)])

    plot.xgrid.grid_line_color = None

    plot.grid.visible = False
    plot.plot_height = 200
    plot.plot_width = 350
    plot.outline_line_color = None

    return components(plot)


# Clear and build profile if necessary
def clear_and_build_profile(username, attr_name, recalculate):
    if attr_name in ['gender', 'age', 'sentiment']:
        lex = Profile.objects.filter(username=username, attr_name=attr_name, classifier='lexicon', is_current=True)

        # Clear out old if necessary
        if recalculate and lex:
            for p in lex:
                p.is_current = False
                p.save()

        # If it exists and we don't need to recalculate, return old value
        if lex and not recalculate:
            return lex[0]

        # Otherwise, build a new profile and return
        else:
            return build_lex_profile(username, attr_name)

    elif attr_name == 'ibm':
        res = Profile.objects.filter(username=username, classifier='ibm', is_current=True)

        # Clear out old if necessary
        if recalculate and res:
            for p in res:
                p.is_current = False
                p.save()

        # If it exists and we don't need to recalculate, return old value
        if res and not recalculate:
            return res  # Note this will be a list of Profiles

        # Otherwise, build a new profile and return
        else:
            return build_ibm(username)

    elif attr_name == 'm3':
        res = Profile.objects.filter(username=username, classifier='m3', is_current=True)

        # Will never need to rebuild these because we don't allow user to edit them
        if res:
            return res
        else:
            return build_m3(username)

    elif attr_name == 'blob':
        res = Profile.objects.filter(username=username, classifier='blob', is_current=True)

        # Clear out old if necessary
        if recalculate and res:
            for p in res:
                p.is_current = False
                p.save()

        # If it exists and we don't need to recalculate, return old value
        if res and not recalculate:
            return res  # Note this will be a list of Profiles

        # Otherwise, build a new profile and return
        else:
            return build_blob(username)

    elif attr_name == 'clf':
        u = User.objects.get(username=username)
        res = Profile.objects.filter(username=username, extra_info='clf', is_current=True)

        # Clear out old if necessary
        if recalculate and res:
            for p in res:
                p.is_current = False
                p.save()

        # If it exists and we don't need to recalculate, return old value
        if res and not recalculate:
            if not u.use_sensitive:
                # Remove any sensitive ones if they exist
                sen = res.filter(is_sensitive=True)
                for s in sen:
                    s.is_active = False
                    s.save()
                res = list(res.filter(is_sensitive=False))
                res.append(None)
                return tuple(res)  # Note this will be a list of Profiles
            else:
                sen = list(res.filter(is_sensitive=True))
                non = list(res.filter(is_sensitive=False))
                # If this list is empty, we switched from non-sensitive to sensitive and need to calculate more profiles
                if not sen:
                    return build_clf(username)
                non.append(sen)
                return tuple(non)
        # Otherwise, build a new profile and return
        else:
            return build_clf(username)

    else:
        raise Exception("Invalid attribute name %s" % attr_name)
