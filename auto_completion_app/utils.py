import re


punctuation = [".", ",", "!", "?", ":", ";"]


def clean_and_tokenize(text):
    """
    Очищает текст от мусора и разбивает его на токены
    """

    # убираем метаданные в начале
    text = text.split("\n\n", 1)[1]

    # убираем заголовки и строки-перенаправления
    text = re.sub(r"(from|to|cc|bcc|subject|sent|when|time|location):.*\n", "", text, flags=re.IGNORECASE)
    text = re.sub(r"----.*?----", "", text)
    text = re.sub(r"forwarded by.*\n", "", text, flags=re.IGNORECASE)

    # убираем email адреса и ссылки
    text = re.sub(r"\S+@\S+", " ", text)
    text = re.sub(r"http\S+|www\.\S+", " ", text)

    # убираем или меняем последовательности символов
    text = re.sub(r"[-=*_$]{2,}", " ", text)

    # убираем пути и вложения
    text = re.sub(r'\b[a-zA-Z]:[\\/][\w\-/\\\s\.]+', ' ', text)
    text = re.sub(r"\b[\w-]+\.(doc|txt|pdf|xls|mpg|mpeg|jpg|png|gif)\b", " ", text)
    text = re.sub(r'<<[^<>]+>>', ' ', text)

    # убираем телефоны
    text = re.sub(r'\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4}', ' ', text)
    text = re.sub(r"\b\d{1,3}[\.\-]\d{3}[\.\-]\d{4}\b", " ", text)
    text = re.sub(r"\b\d{3}-\d{4}\b", "", text)

    # убираем ip адреса
    text = re.sub(r"\b\d{1,3}(\.\d{1,3}){3}\b", " ", text)

    # убираем кодировки вида =09, =20
    text = re.sub(r"=\d{2}", " ", text)

    # убираем CSS/HTML-блоки
    text = re.sub(r"\b\w+\s*\{[^}]*\}", "", text)
    text = re.sub(r"\b\w+:[^\s]+", "", text)

    # убираем ASCII-арт — строки с множеством спецсимволов
    text = re.sub(r"[\"':;`._\-\^\(\)\[\]\{\}+><~|@#*%]", "", text)

    # убираем повторяющиеся знаки и слова
    text = re.sub(r"[.]{2,}", ".", text)
    text = re.sub(r"[,]{2,}", ",", text)
    text = re.sub(r"[!]{2,}", "!", text)
    text = re.sub(r"[?!]{2,}", "?", text)
    text = re.sub(r"\b(\w+)( \1){2,}\b", r"\1", text)

    # убираем длинные последовательности цифр
    text = re.sub(r'\d{5,}', ' ', text)

    # оставляем пробелы и приводим к нижнему регистру
    text = re.sub(r"\s+", " ", text).strip().lower()

    # разбиваем на токены
    return tokenize(text)


def tokenize(text):
    tokens = re.findall(r"[a-zA-Z]+(?:'[a-zA-Z]+)?|[.,!?;]", text)
    return tokens

def detokenize(tokens):
    text = ""
    for i, tok in enumerate(tokens):
        # если знак препинания - то пробел не ставим
        if i > 0 and tok not in punctuation:
            text += " "
        text += tok
    return text