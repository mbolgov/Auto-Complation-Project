import pandas as pd
from joblib import Parallel, delayed

from .utils import clean_and_tokenize


def load_corpus(path="auto_completion_app/data/emails.csv"):
    """
    Загружает и очищает тексты, возвращает список токенизированных сообщений.
    """
    df = pd.read_csv(path)
    messages = df["message"]
    cleaned_messages = Parallel(n_jobs=-1)(
        delayed(clean_and_tokenize)(msg) for msg in messages
    )
    return cleaned_messages
