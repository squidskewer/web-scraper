import re
from collections import Counter
from pathlib import Path

import pandas as pd

DEFAULT_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "can", "could",
    "did", "do", "does", "doing", "done", "for", "from", "had", "has", "have", "having",
    "he", "her", "hers", "him", "his", "how", "i", "if", "in", "into", "is", "it", "its",
    "just", "like", "may", "might", "more", "most", "much", "no", "not", "of", "on", "one",
    "or", "other", "our", "out", "over", "said", "says", "she", "should", "so", "some",
    "such", "than", "that", "the", "their", "them", "then", "there", "these", "they",
    "this", "those", "to", "too", "up", "us", "use", "used", "using", "very", "was",
    "were", "what", "when", "which", "who", "why", "will", "with", "would", "you", "your",
    "we", "via", "also", "about", "new", "news", "http", "https", "www", "com",
}


def clean_text(text):
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return text


def tokenize(text, stopwords, min_len):
    words = clean_text(text).split()
    tokens = []
    for word in words:
        if len(word) < min_len:
            continue
        if word in stopwords:
            continue
        if word.isdigit():
            continue
        tokens.append(word)
    return tokens


def keyword_frequency(
    file_path,
    column="content",
    top_n=20,
    min_len=3,
    stopwords=None,
    extra_stopwords=None,
):
    path = Path(file_path)
    if not path.exists():
        print(f"Warning: missing dataset file: {file_path}")
        return []
    df = pd.read_csv(file_path)
    if column not in df.columns:
        print(f"Warning: missing column '{column}' in {file_path}")
        return []

    active_stopwords = set(stopwords or DEFAULT_STOPWORDS)
    if extra_stopwords:
        active_stopwords.update({w.lower() for w in extra_stopwords})

    counter = Counter()
    for text in df[column].dropna():
        tokens = tokenize(str(text), active_stopwords, min_len)
        counter.update(tokens)
    return counter.most_common(top_n)
