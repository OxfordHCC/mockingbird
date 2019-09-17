from nltk.tokenize import word_tokenize
import numpy as np
import re
import torch
import torch.nn as nn
from classifiers.A4NT.models.char_translator import CharTranslator
from classifiers.A4NT.token_dicts import *
from emoji import UNICODE_EMOJI


# General helper functions
# Clears whitespace but retains character for re.sub
def strip_match(match):
    return match.group(0).strip()


# Joins together decimals
def fix_decimals(match):
    match = match.group(0)
    return re.sub('\s', '', match)


# Cleans text by removing unnecessary whitespace and substituting back in some symbols
def clean_text(text):
    text = re.sub('-lrb-', '(', text)
    text = re.sub('-rrb-', ')', text)
    text = re.sub('-lsb-', '[', text)
    text = re.sub('-rsb-', ']', text)
    text = re.sub('-lcb-', '{', text)
    text = re.sub('-rcb-', '}', text)
    text = re.sub('\'\'', '\"', text)
    text = re.sub('\si\s', ' I ', text)
    text = re.sub('^i\s', 'I ', text)
    text = re.sub('\sna\s', 'na ', text)
    text = re.sub('\$\s', strip_match, text)
    text = re.sub('[-#]\s|\s([-.!,\':;?]|n\'t)', strip_match, text)
    text = re.sub('\d+. \d+', fix_decimals, text)
    return text


# Class to contain "translator"
class translator(nn.Module):
    # Initialize model
    def __init__(self, filename):
        super(translator, self).__init__()
        self.type = filename
        if filename == 'gender':
            device = torch.device('cpu')
            saved_model = torch.load('./classifiers/A4NT/models/gender_cpu_sd.pth', map_location=device)
            self.cp_params = GENDER_DICT
            self.auth_to_index = G_A_2_I
            self.index_to_auth = G_I_2_A

        elif filename == 'age':
            device = torch.device('cpu')
            saved_model = torch.load('./classifiers/A4NT/models/age_cpu_sd.pth', map_location=device)
            self.cp_params = AGE_DICT
            self.auth_to_index = A_A_2_I
            self.index_to_auth = A_I_2_A
        else:
            raise Exception("Invalid translator specified: try 'gender' or 'age'")
        self.word_to_index = W_2_I
        self.index_to_word = I_2_W
        self.model = CharTranslator(self.cp_params)
        self.model.eval()
        self.startc = 'START'
        self.endc = 'END'
        append_tensor = np.zeros((1, 1), dtype=np.int)
        append_tensor[0, 0] = self.word_to_index[self.startc]
        self.append_tensor = torch.LongTensor(append_tensor)
        self.model.load_state_dict(saved_model)
        self.model.init_hidden(1)
        self.jc = '' if self.cp_params.get('atoms', 'char') == 'char' else ' '
        self.maxlen = self.cp_params['max_seq_len']

    # Translate a single sentence (sen) from class (class_name) to the opposite class
    def translate_sentence(self, sen, class_name, verbose=False):

        # Switch class names to fit original model
        if self.type == 'age':
            if class_name == 'young':
                original = '<20'
            elif class_name == 'old':
                original = '<50'
            else:
                raise Exception("Invalid class specified: try 'young' or 'old'")
        elif class_name not in ['male', 'female']:
            raise Exception("Invalid class specified: try 'male' or 'female'")
        else:
            original = class_name

        # Get other class name
        o_class = self.auth_to_index[original]
        n_class = 1 - o_class
        n_class_name = self.index_to_auth[n_class]
        if n_class_name == '<20':
            n_class_name = 'young'
        elif n_class_name == '<50':
            n_class_name = 'old'

        # Clean string before tokenization
        s = re.sub('http(s|):.*$', 'URL', sen)
        s = re.sub('(pic.twitter).*$', 'TWIT_PIC', s)
        s = re.sub('\"', "\' \'", s)
        s = re.sub('\(', ' -lrb- ', s)
        s = re.sub('\)', ' -rrb- ', s)
        s = re.sub('\[', ' -lsb- ', s)
        s = re.sub('\]', ' -rsb- ', s)
        s = re.sub('\{', ' -lcb- ', s)
        s = re.sub('\}', ' -rcb- ', s)
        s = re.sub('/', ' / ', s)
        s = s.lower()
        s = re.sub('\d+', 'NUM', s)
        s = re.sub('NUM.NUM', 'NUM . NUM', s)

        # Tokenize sen
        tokenized = word_tokenize(s)
        inp = [self.startc] + tokenized

        # Replace emojis/special characters with ELIP
        emojis = []
        for i, w in enumerate(inp):
            if w in UNICODE_EMOJI:
                emojis.append(w)
                inp[i] = 'ELIP'

        # Translate to appropriate index
        inp_inds = [self.word_to_index[w] if w in self.word_to_index else 0 for w in inp[:self.maxlen]]
        # TODO: check if OOV is working

        # Do padding/truncating
        # ?????

        # Do translation
        self.model.eval()
        inp_seq = np.zeros((len(inp_inds), 1), dtype=np.int)  # We only translate one sentence at a time
        inp_seq[:len(inp_inds), 0] = inp_inds
        forward = self.model.forward_gen(torch.from_numpy(inp_seq),
                                         end_c=self.word_to_index[self.endc],
                                         n_max=self.maxlen,
                                         auths=torch.from_numpy(np.array([n_class])))

        # Format appropriately
        output_list = [self.index_to_word[c.item()] for c in forward if c.item() in self.index_to_word]
        if output_list[-1] == 'END':
            output_list = output_list[:-1]

        # Replace all 'NUM' tags with the numbers in the original sentence
        nums = re.findall('\d+', sen)
        output_list = [nums.pop(0) if w == 'NUM' and nums else w for w in output_list]

        # Replace all 'URLS' with the original URL
        urls = re.findall('(https:.*|http:.*)', sen)
        output_list = [urls.pop(0) if w in ['URL', 'url'] and urls else w for w in output_list]

        # Replace all 'TWIT_PICS' with original link
        pics = re.findall('pic\.twitter.*', sen)
        output_list = [pics.pop(0) if w in ['TWIT_PIC', 'twit_pic'] and pics else w for w in output_list]

        # Replace all # with original hashtag
        tags = re.findall('#[A-z0-9]+', sen)
        output_list = [tags.pop(0) if w == '#' and tags else w for w in output_list]

        # Replace all @ with original link
        at = re.findall('@[A-z0-9]+', sen)
        output_list = [at.pop(0) if w == '@' and at else w for w in output_list]

        # Replace all 'ELIP' with original emojis
        output_list = [emojis.pop(0) if w in ['elip', 'ELIP'] and emojis else w for w in output_list]

        # If the first word is capitalized in the sentence, capitalize it here
        if sen[0].isupper() and output_list:
            output_list[0] = output_list[0].capitalize()

        output_string = self.jc.join(output_list)
        output_string = clean_text(output_string)

        translation = output_string

        # Print if verbose
        if verbose:
            print("Translating from %s to %s" % (class_name, n_class_name))
            print("Input sentence: %s" % sen)
            print("Translated Sentence: %s" % translation)

        # Return translated sentence
        return translation
