from django import template
from django.http import HttpResponse
import re
import locale

register = template.Library()
locale.setlocale(locale.LC_ALL, 'en_GB')


# Pass
@register.simple_tag
def get_explanations(profile, index, weights, dec):
    data = profile.get_explanations(index-1, weights)  # Subtract one due to zero indexing

    # If the weights are returned, truncate to `dec` decimal places.
    if weights and data:
        data = [(x[0], round(float(x[1]), dec)) for x in data if x[0] != '']
    return data


@register.simple_tag
def get_global_explanations(profile, index, weights, dec):
    data = profile.get_global_explanations(index-1, weights)  # Subtract one due to zero indexing

    # If the weights are returned, truncate to `dec` decimal places.
    if weights:
        data = [(x[0], round(float(x[1]), dec)) for x in data]

    return data


@register.simple_tag
def order_and_return(profile, n=3):
    return profile.order_and_return(n=n)


@register.simple_tag
def add_tag(tweet, to_bold, tag):
    if to_bold is None:
        return tweet
    front_tag = '<' + tag + '>'
    back_tag = '</' + tag + '>'
    for word in to_bold:
        if word.isalnum():
            tweet = re.sub('((?<=(^))|(?<=(\W)))' + word + '(?=\W)', front_tag + word + back_tag, tweet)
        else:
            tweet = re.sub(re.escape(word), front_tag + word + back_tag, tweet)
    return tweet


@register.simple_tag
def call_url_from_charfield(request, data):
    return HttpResponse(request, 'twitter:tweets', {'username': str(data)})


@register.simple_tag
def float_to_percent(num, n_dec=0):
    if n_dec != 0:
        percent = round(num*100, n_dec)
    else:
        percent = round(num*100)
    return str(percent) + '%'


@register.simple_tag
def float_to_currency(num):
    return '£' + locale.format_string("%.2f", float(num), grouping=True)
