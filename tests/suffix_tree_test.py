"""Unit tests for SuffixTree."""

import unittest
import random
import string
from src import suffix_tree

SuffixTree = suffix_tree.SuffixTree


class SuffixTreeTest(unittest.TestCase):
    longMessage = True

    def _setup_tree(self, word: str) -> SuffixTree:
        tree = SuffixTree(word)
        tree.build()
        return tree

    def _assert_all_suffixes_present(self, tree: SuffixTree, word: str):
        for i in range(len(word)):
            suffix = word[i:]
            self.assertTrue(
                tree.find(suffix), f"word: {word}, suffix: {suffix}"
            )

    def _random_word(self, length: int, alphabet: str = string.ascii_lowercase):
        return "".join(random.choice(alphabet) for _ in range(length))

    def test_uncompressable(self):
        word = "abcde"
        tree = self._setup_tree(word)

        self._assert_all_suffixes_present(tree, word)

        self.assertFalse(tree.find("bcdef"))
        self.assertFalse(tree.find("ce"))
        self.assertFalse(tree.find("ax"))

    def test_rule_3(self):
        # https://stackoverflow.com/a/9513423 has diagram for comparison
        word = "abcabxabcd"
        tree = self._setup_tree(word)

        self._assert_all_suffixes_present(tree, word)

        self.assertFalse(tree.find("k"))
        self.assertFalse(tree.find("yd"))
        self.assertFalse(tree.find("bcx"))
        self.assertFalse(tree.find("cabxabd"))

    def test_rule_3_harder(self):
        words = [
            "savannas",
            "ogopogo",
            "oniononiono",
            "aaaaaaaaaaaaa",
            "hahaaahaahaaaa",
            "abcdefabxybcdmnabcdex",
            "aaaabaaaabaac",
            "aabaaabb",
        ]
        for word in words:
            tree = self._setup_tree(word)
            self._assert_all_suffixes_present(tree, word)

    def test_dynamic_short(self):
        word_length = 8
        iterations = 500

        for _ in range(iterations):
            word = self._random_word(word_length)
            tree = self._setup_tree(word)
            self._assert_all_suffixes_present(tree, word)
            # TODO: test more queries that should return False

    def test_dynamic_long(self):
        word_length = 40
        iterations = 500
        alphabet = "abcdefghij"

        for _ in range(iterations):
            word = self._random_word(word_length, alphabet)
            tree = self._setup_tree(word)
            self._assert_all_suffixes_present(tree, word)


if __name__ == "__main__":
    unittest.main()
