import re
import sys


korean_pattern_str = '가-힣'
number_pattern_str = '0-9'
alphabet_pattern_str = 'a-zA-Z'
puntuation_pattern_str = '.,?!'

doublespace_pattern = re.compile(r'\s+')
repeatchars_pattern = re.compile(r'(\w)\\1{3,}')

def normalize(doc, english=False, number=False, punctuation=False,
    remove_repeat=0, remains=None, pattern=None):
    """
    Arguments
    ---------
    doc : str
        Input string to be normalized
    english : Boolean
        If True, it remains alphabet
    number : Boolean
        If True, it remains number
    punctuation : Boolean
        If True, it remains symbols '.,?!'
    remove_repeat : int
        If it is positive integer, it shortens repeated characters.
    remains : None or str
        User specfied characters that user wants to remain
    pattern : None or re.Pattern
        User specified regular expression pattern to use for normalization.
        For example, to remain Korean and alphabets,

            >>> patterm = re.compile('[^가-힣a-zA-Z]')

    Returns
    -------
    doc : str
        Normalized string
    """

    if sys.version_info.major >= 3 and sys.version_info.minor <= 6:
        if not isinstance(pattern, re._pattern_type):
            pattern = initialize_pattern(english, number, punctuation, remains)
    elif sys.version_info.major >= 3 and sys.version_info.minor >= 7:
        if not isinstance(pattern, re.Pattern):
            pattern = initialize_pattern(english, number, punctuation, remains)
    else:
        if not isinstance(pattern, re.Pattern):
            pattern = initialize_pattern(english, number, punctuation, remains)

    if remove_repeat > 0:
        doc = repeatchars_pattern.sub('\\1' * remove_repeat, doc)

    doc = pattern.sub(' ', doc)
    return doublespace_pattern.sub(' ', doc).strip()

def initialize_pattern(english=False, number=False, punctuation=False, remains=None):
    """
    Arguments
    ---------
    english : Boolean
        If True, it remains alphabet
    number : Boolean
        If True, it remains number
    punctuation : Boolean
        If True, it remains symbols '.,?!'
    remains : None or str
        User specfied characters that user wants to remain

    Returns
    -------
    pattern : re.Pattern
        Regular expression pattern

    Usage
    -----
        >>> initialize_pattern(english=True)
        $ re.compile(r'[^가-힣a-zA-Z]', re.UNICODE)
    """

    pattern = korean_pattern_str
    if english:
        pattern += alphabet_pattern_str
    if number:
        pattern += number_pattern_str
    if punctuation:
        pattern += puntuation_pattern_str
    if isinstance(remains, str):
        pattern += remains
    return re.compile(r'[^%s]' % pattern)
