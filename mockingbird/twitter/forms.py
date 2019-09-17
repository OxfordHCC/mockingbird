from django import forms


class UsernameForm(forms.Form):
    username = forms.CharField(label='', max_length=100, widget=forms.TextInput(
        attrs={'type': 'text_form', 'name': 'username', 'placeholder': "Enter username"}))
    no_tweets = forms.IntegerField(label='', initial=200, widget=forms.NumberInput(
        attrs={'type': 'integer_form', 'name': 'no_tweets', 'placeholder': "Number of Tweets"}
    ))
    use_sensitive = forms.BooleanField(label='', initial=False, required=False, widget=forms.CheckboxInput())

    # Return username as a string
    def get_username(self):
        return str(self.fields['username'])


class UpdateTweetForm(forms.Form):
    tweet_1 = forms.CharField(required=False, label='Tweet 1',
                              widget=forms.Textarea(attrs={'type': 'text_form', 'name': 'tweet_1'}))
    tweet_2 = forms.CharField(required=False, label='Tweet 2',
                              widget=forms.Textarea(attrs={'type': 'text_form', 'name': 'tweet_2'}))
    tweet_3 = forms.CharField(required=False, label='Tweet 3',
                              widget=forms.Textarea(attrs={'type': 'text_form', 'name': 'tweet_3'}))
    tweet_4 = forms.CharField(required=False, label='Tweet 4',
                              widget=forms.Textarea(attrs={'type': 'text_form', 'name': 'tweet_4'}))
    tweet_5 = forms.CharField(required=False, label='Tweet 5',
                              widget=forms.Textarea(attrs={'type': 'text_form', 'name': 'tweet_5'}))
    tweet_6 = forms.CharField(required=False, label='Tweet 6',
                              widget=forms.Textarea(attrs={'type': 'text_form', 'name': 'tweet_6'}))
    tweet_7 = forms.CharField(required=False, label='Tweet 7',
                              widget=forms.Textarea(attrs={'type': 'text_form', 'name': 'tweet_7'}))
    tweet_8 = forms.CharField(required=False, label='Tweet 8',
                              widget=forms.Textarea(attrs={'type': 'text_form', 'name': 'tweet_8'}))
    tweet_9 = forms.CharField(required=False, label='Tweet 9',
                              widget=forms.Textarea(attrs={'type': 'text_form', 'name': 'tweet_9'}))
    tweet_10 = forms.CharField(required=False, label='Tweet 10',
                               widget=forms.Textarea(attrs={'type': 'text_form', 'name': 'tweet_10'}))
    target_class = forms.CharField(required=True, label='target', widget=forms.HiddenInput())
    start_index = forms.IntegerField(required=True, label='start_index', widget=forms.HiddenInput())
