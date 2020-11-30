import collections

from ._model import PredictionModel


class MostUsed(PredictionModel):  # is it the same as 1-gram?
    def __init__(self):
        self.command_to_frequency = collections.defaultdict(int)

    def update(self, current_command: str):
        self.command_to_frequency[current_command] += 1

    def predict(self, current_command: str, n: int):
        sorted_dict = {
            k: v for k, v in
            sorted(self.command_to_frequency.items(), key=lambda item: (item[1], item[0]), reverse=True)
        }
        return list(sorted_dict.keys())[:n]

    @property
    def name(self) -> str:
        return 'MostUsed'


class Bigram(PredictionModel):
    """N-gram with N=2"""

    def __init__(self):
        self.ngram = collections.defaultdict(int)
        self.related_keys = collections.defaultdict(set)
        self.last_command = None

    def update(self, current_command: str):
        gram_key = self.last_command or '', current_command
        self.ngram[gram_key] += 1
        self.related_keys[self.last_command].add(gram_key)
        self.last_command = current_command

    def predict(self, current_command: str, n: int):
        try:
            related_keys = self.related_keys[current_command]
        except IndexError:
            related_keys = set(key for key in self.ngram.keys() if current_command == key[0])
        related_items = {}
        unrelated_items = {}
        for k, v in self.ngram.items():
            if k in related_keys:
                related_items[k] = v
            else:
                unrelated_items[k] = v

        sorted_dict = {
            k: v for k, v in sorted(related_items.items(), key=lambda item: (item[1], item[0]), reverse=True)
        }
        if len(sorted_dict) < n:
            for k, v in sorted(unrelated_items.items(), key=lambda item: (item[1], item[0]), reverse=True):
                sorted_dict[k] = v
        return list(k[-1] for k in sorted_dict.keys())[:n]

    @property
    def name(self) -> str:
        return 'Bigram'


class Trigram(Bigram):
    """N-gram with N=3"""

    def __init__(self):
        super().__init__()
        self.second_to_last_command = None

    def update(self, current_command: str):
        gram_key = self.second_to_last_command or '', self.last_command or '', current_command or ''
        self.ngram[gram_key] += 1
        self.related_keys[self.last_command].add(gram_key)
        self.related_keys[(self.second_to_last_command, self.last_command)].add(gram_key)

        self.second_to_last_command = self.last_command
        self.last_command = current_command

    @property
    def name(self) -> str:
        return 'Trigram'
