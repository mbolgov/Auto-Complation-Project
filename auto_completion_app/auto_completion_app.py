import reflex as rx

from .models import TextSuggestion
from .get_data import load_corpus
from .utils import tokenize, detokenize


corpus = load_corpus(path="auto_completion_app/data/emails.csv")
suggestor = TextSuggestion(corpus, n_max=5, k=10)


class State(rx.State):
    """The app state."""

    input_text = ""
    input_tokens = []
    suggestions = []

    n_gram = 1
    n_words = 1
    n_texts = 1

    def set_input_text(self, value):
        """
        при изменении текста сохраняет новый и изменяет токены
        """
        self.input_text = value
        self.input_tokens = tokenize(self.input_text)
        self.update_suggestions()

    def choose_suggestion(self, suggestion):
        """
        при выборе совета конкатенирует текст с выбранным вариантом
        """
        self.input_tokens = self.input_tokens[:-1] + tokenize(suggestion)
        self.input_text = detokenize(self.input_tokens)
        self.update_suggestions()

    def update_n_gram_value(self):
        """
        следит за тем, чтобы n-gram было не меньше числа токенов
        """
        self.n_gram = min(self.n_gram, len(self.input_tokens) - (len(self.input_tokens) > 1 and self.input_tokens[-1] == ''))

    def set_n_gram(self, value):
        """
        меняет значение n для n-граммы
        """
        self.n_gram = value[0]
        self.update_suggestions()

    def set_n_words(self, value):
        """
        меняет значение n_words для генерации
        """
        self.n_words = value[0]
        self.update_suggestions()

    def set_n_texts(self, value):
        """
        меняет значение n_texts для генерации
        """
        self.n_texts = value[0]
        self.update_suggestions()

    def track_last_token(self):
        """
        добавляет пустой токен в конец (максимум один), если пользователь ничего не ввёл или ввёл пробел
        """
        if (self.input_text == '' or self.input_text[-1] == ' ') and (len(self.input_tokens) == 0 or self.input_tokens[-1] != ''):
            self.input_tokens.append('')

    def update_suggestions(self):
        """
        обновляет предсказания после любого изменения
        """
        self.track_last_token()
        self.update_n_gram_value()
        self.suggestions = [
            detokenize(tokens) for tokens in suggestor.suggest_text(self.input_tokens, n_gram=self.n_gram, n_words=self.n_words, n_texts=self.n_texts)
        ]


def index():
    return rx.box(
        rx.card(
            rx.vstack(
                # заголовок
                rx.heading("Auto-completion app", font_size="2em"),
                rx.text("by @mbolgov", font_size="0.9em"),

                # ползунки
                rx.hstack(
                    rx.vstack(
                        rx.text(f"n_gram: {State.n_gram}", weight="bold"),
                        rx.slider(
                            min=1, max=5, step=1,
                            value=[State.n_gram],
                            on_change=State.set_n_gram,
                            width="14em"
                        ),
                    ),
                    rx.vstack(
                        rx.text(f"n_words: {State.n_words}", weight="bold"),
                        rx.slider(
                            min=1, max=10, step=1,
                            value=[State.n_words],
                            on_change=State.set_n_words,
                            width="14em"
                        ),
                    ),
                    rx.vstack(
                        rx.text(f"n_texts: {State.n_texts}", weight="bold"),
                        rx.slider(
                            min=1, max=10, step=1,
                            value=[State.n_texts],
                            on_change=State.set_n_texts,
                            width="14em"
                        ),
                    ),
                    justify="between",   # распределены равномерно между границами
                    width="100%",
                ),

                # поле ввода
                rx.input(
                    placeholder="Enter text...",
                    value=State.input_text,
                    on_change=State.set_input_text,
                    width="100%",
                    border_radius="md",
                ),

                # варианты автодополнения
                rx.cond(
                    State.suggestions,   # если пусто - ничего не показываем
                    rx.vstack(
                        rx.foreach(
                            State.suggestions,
                            # кнопки с автодополнением
                            lambda s: rx.button(
                                s,
                                width="100%",
                                justify="flex-start",
                                variant="outline",
                                border_radius="md",
                                on_click=lambda: State.choose_suggestion(s),
                            )
                        ),
                        width="100%",
                        spacing="1",
                    )
                )
            ),
            width="50em",   # создаём красивую рамку
            padding="2em",
            border_radius="xl",
            box_shadow="md",
            bg="white"
        ),
        position="fixed",   # фиксируем положение сверху, чтобы при изменении кол-ва вариантов наше приложение не двигалось оп экрану
        top="10em",
        left="50%",
        transform="translateX(-50%)",
    )


app = rx.App()
app.add_page(index)
