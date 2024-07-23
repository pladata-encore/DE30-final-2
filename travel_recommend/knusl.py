import json
from konlpy.tag import Okt

class KnuSL():
    def __init__(self, path='SentiWord_info.json'):
        with open(path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.okt = Okt()

    def get_word_score(self, word):
        for item in self.data:
            if item['word'] == word:
                return int(item['polarity'])
        return 0

    def get_sentence_score(self, sentence):
        tokens = self.okt.morphs(sentence)
        score = 0
        for token in tokens:
            score += self.get_word_score(token)
        return score

    def analyze(self, text):
        tokens = self.okt.morphs(text)
        result = []
        for token in tokens:
            result.append((token, self.get_word_score(token)))
        return result
