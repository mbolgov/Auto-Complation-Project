import numpy as np
from typing import List, Union
from collections import defaultdict, Counter

from .utils import punctuation, tokenize


class PrefixTreeNode:
    def __init__(self):
        self.children: dict[str, PrefixTreeNode] = {}
        self.count_prefix = 0
        self.count_word = 0
        self.top_words = Counter()


class PrefixTree:
    def __init__(self, corpus, k):
        """
        vocabulary: список всех уникальных токенов в корпусе
        """
        self.root = PrefixTreeNode()
        self.k = k

        # строим префиксное дерево
        for text in corpus:
            for word in text:
                node = self.root
                for ch in word:
                    node.count_prefix += 1
                    if ch not in node.children:
                        node.children[ch] = PrefixTreeNode()
                    node = node.children[ch]
                node.count_word += 1
                node.count_prefix += 1

        # запоминаем top-k слов для всех вершин, для этого используем dfs на стеке
        stack = [(self.root, '', 0)]
        while stack:
            node, word, tmp = stack[-1]
            if tmp == 0:
                stack[-1] = (node, word, 1)
                # считаем top_words у потомков
                for char, child in node.children.items():
                    stack.append((child, word + char, 0))
            else:
                # добавляем в словарь слово, кончающееся в текущей вершине и объединяем со словарями потомков
                if node.count_word > 0:
                    node.top_words[word] = node.count_word
                for child in node.children.values():
                    node.top_words.update(child.top_words)
                # оставляем k самых частых слов
                node.top_words = Counter(dict(node.top_words.most_common(self.k)))
                stack.pop()

    def get_words_and_probs(self, prefix: str) -> (List[str], List[float]):
        """
        Возвращает список слов, начинающихся на prefix,
        с их вероятностями (нормировать ничего не нужно)
        """
        node = self.root
        for char in prefix:
            if char not in node.children:
                return np.array([]), np.array([])
            node = node.children[char]

        words, probs = zip(*node.top_words.items())
        words, probs = np.array(words), np.array(probs) / node.count_prefix
        return words, probs


class NGramLanguageModel:
    def __init__(self, corpus, n_max=5, k=10):
        self.n_max = n_max
        self.k = k

        # считаем все возможные продолжения для каждой n-граммы для всех n до n_max
        ngram_continuations = [defaultdict(Counter) for _ in range(n_max)]
        for text in corpus:
            text = tuple(text)
            for i in range(len(text) - self.n_max):
                for n in range(1, n_max + 1):
                    if i + n >= len(text):
                        break
                    ngram = text[i:i + n]
                    next_word = text[i + n]
                    ngram_continuations[n - 1][ngram][next_word] += 1

        # заранее вычислим words_and_probs для top-k вариантов
        self.ngram_topk = [defaultdict(tuple) for _ in range(n_max)]
        for n in range(1, n_max + 1):
            for ngram, counter in ngram_continuations[n - 1].items():
                words, probs = zip(*counter.most_common(self.k))
                words, probs = np.array(words), np.array(probs) / sum(probs)
                self.ngram_topk[n - 1][ngram] = (np.array(words), probs)


    def get_next_words_and_probs(self, prefix: tuple, n: int = 0) -> (List[str], List[float]):
        """
        Возвращает список слов, которые могут идти после prefix,
        а так же список вероятностей этих слов
        """
        if n == 0:
            n = min(self.n_max, len(prefix))
        context = tuple(prefix[-n:])

        if context not in self.ngram_topk[n - 1]:
            return np.array([]), np.array([])
        return self.ngram_topk[n - 1][context]


class TextSuggestion:
    def __init__(self, corpus, n_max=5, k=10):
        self.prefix_tree = PrefixTree(corpus, k=k)
        self.n_gram_model = NGramLanguageModel(corpus, n_max=n_max)
        self.k = k

    def suggest_text(self, text: Union[str, list], n_gram=0, n_words=3, n_texts=1) -> list[list[str]]:
        """
        Возвращает возможные варианты продолжения текста (по умолчанию только один)

        text: строка или список слов – написанный пользователем текст
        n_words: число слов, которые дописывает n-граммная модель
        n_texts: число возвращаемых продолжений (пока что только одно)

        return: list[list[srt]] – список из n_texts списков слов, по 1 + n_words слов в каждом
        Первое слово – это то, которое WordCompletor дополнил до целого.
        """
        if type(text) == str:
            text = tokenize(text)
        text = tuple(text)

        # находим top-k продолжений первого слова, если последний токен не пуст
        # иначе считаем, что первое слово дополнять до целого не нужно
        if text[-1] != "":
            first_words, first_probs = self.prefix_tree.get_words_and_probs(text[-1])
        else:
            n_words -= 1
            # если содержательных токенов нет - генерируем из префиксного дерева, иначе генерируем с помощью n-грамм
            if len(text) == 1:
                first_words, first_probs = self.prefix_tree.get_words_and_probs(text[-1])
            else:
                first_words, first_probs = self.n_gram_model.get_next_words_and_probs(text[:-1], n=n_gram)

            # первый символ во всей фразе или символ после пробела - не пунктуация
            mask = ~np.isin(first_words, punctuation)
            first_words, first_probs = first_words[mask], first_probs[mask]

        topk_idx = np.argpartition(-first_probs, min(self.k, len(first_words) - 1))[:self.k]
        suggestions = [text[:-1] + (first_words[idx],) for idx in topk_idx]
        probs = first_probs[topk_idx]

        for tmp in range(n_words):
            new_suggestions, new_probs = [], []

            # перебираем k вариантов контекста, к каждому добавляем k наиболее вероятных продолжений
            for i in range(len(suggestions)):
                next_words, next_probs = self.n_gram_model.get_next_words_and_probs(suggestions[i], n=n_gram)
                topk_idx = np.argpartition(-next_probs, min(self.k, len(next_words) - 1))[:self.k]
                new_suggestions.extend([suggestions[i] + (next_words[idx],) for idx in topk_idx])
                new_probs.extend(next_probs[topk_idx] * probs[i])

            # из порядка (k)^2 вариантов предсказаний оставляем top-k
            new_suggestions, new_probs = new_suggestions, np.array(new_probs)
            topk_idx = np.argpartition(-new_probs, min(self.k, len(new_suggestions) - 1))[:self.k]
            suggestions = [new_suggestions[idx] for idx in topk_idx]
            probs = new_probs[topk_idx]

        # оставляем n_texts продолжений длины n_words + 1 и сортируем их по вероятности
        idx = np.argpartition(-probs, min(n_texts, len(probs) - 1))[:n_texts]
        idx = idx[np.argsort(-probs[idx])]
        suggestions = [list(suggestions[idx][-n_words - 1:]) for idx in idx]
        return suggestions

