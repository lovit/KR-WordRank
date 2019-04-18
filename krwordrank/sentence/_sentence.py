class Summarizer:
    def __init__(self):
        raise NotImplemented


def keysentence(keywords, texts, topk=10, diversity=0.3, penalty=None):
    raise NotImplemented


def highlight_keyword(sent, keywords):
    for keyword, score in keywords.items():
        if score > 0:
            sent = sent.replace(keyword, '[%s]' % keyword)
    return sent