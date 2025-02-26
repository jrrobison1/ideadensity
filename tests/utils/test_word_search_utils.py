import pytest
from ideadensity.utils.word_search_utils import (
    beginning_of_sentence,
    is_repetition,
    search_backwards,
    MAX_LOOKBACK,
)
from ideadensity.word_item import WordListItem
from ideadensity.utils.constants import SENTENCE_END

NUMBER_OF_BLANK_WORD_ITEMS = 10
FIRST_WORD_INDEX = 10


@pytest.fixture
def create_word_list():
    def _create_word_list(tokens_and_tags):
        return [WordListItem() for _ in range(NUMBER_OF_BLANK_WORD_ITEMS)] + [
            WordListItem(token, tag) for token, tag in tokens_and_tags
        ]

    return _create_word_list


def test_beginning_of_sentence_middle(create_word_list):
    words = create_word_list(
        [
            ("This", "PLC_TAG"),
            ("is", "PLC_TAG"),
            ("a", "PLC_TAG"),
            ("sentence", "PLC_TAG"),
            (".", SENTENCE_END),
            ("Another", "PLC_TAG"),
            ("one", "PLC_TAG"),
            (".", SENTENCE_END),
        ]
    )

    assert beginning_of_sentence(words, FIRST_WORD_INDEX + 6) == FIRST_WORD_INDEX + 5


def test_beginning_of_sentence_start(create_word_list):
    words = create_word_list(
        [
            ("This", "PLC_TAG"),
            ("is", "PLC_TAG"),
            ("a", "PLC_TAG"),
            ("sentence", "PLC_TAG"),
            (".", SENTENCE_END),
        ]
    )

    assert beginning_of_sentence(words, FIRST_WORD_INDEX + 2) == FIRST_WORD_INDEX


def test_beginning_of_sentence_end(create_word_list):
    words = create_word_list(
        [
            ("This", "PLC_TAG"),
            ("is", "PLC_TAG"),
            ("a", "PLC_TAG"),
            ("sentence", "PLC_TAG"),
            (".", SENTENCE_END),
        ]
    )

    assert beginning_of_sentence(words, FIRST_WORD_INDEX + 4) == FIRST_WORD_INDEX


def test_beginning_of_sentence_single_word(create_word_list):
    words = create_word_list(
        [
            ("Word", "PLC_TAG"),
        ]
    )
    assert beginning_of_sentence(words, FIRST_WORD_INDEX) == FIRST_WORD_INDEX


def test_beginning_of_sentence_multiple_sentences(create_word_list):
    words = create_word_list(
        [
            ("First", "PLC_TAG"),
            (".", SENTENCE_END),
            ("Second", "PLC_TAG"),
            (".", SENTENCE_END),
            ("Third", "PLC_TAG"),
            ("sentence", "PLC_TAG"),
            (".", SENTENCE_END),
        ]
    )

    assert beginning_of_sentence(words, FIRST_WORD_INDEX + 5) == FIRST_WORD_INDEX + 4


def test_is_repetition():
    # Test exact match
    assert is_repetition("word", "word") == True

    # Test incomplete word with hyphen
    assert is_repetition("hesi-", "hesitation") == True

    # Test non-repetition
    assert is_repetition("cat", "dog") == False

    # Test empty strings
    assert is_repetition("", "") == False
    assert is_repetition("word", "") == False
    assert is_repetition("", "word") == False

    # Test short words (3 characters or less)
    assert is_repetition("a", "apple") == False
    assert is_repetition("an", "another") == False
    assert is_repetition("the", "theocracy") == False

    # Test words that start the same but aren't repetitions
    assert is_repetition("car", "carpet") == False


def test_search_backwards(create_word_list):
    assert (
        search_backwards(create_word_list([]), FIRST_WORD_INDEX, lambda x: True) is None
    )

    words = create_word_list([("First", "TAG1"), ("Second", "TAG2")])
    assert search_backwards(words, FIRST_WORD_INDEX, lambda x: True) is None

    words = create_word_list([("Word", "TAG") for _ in range(MAX_LOOKBACK + 1)])
    assert (
        search_backwards(words, FIRST_WORD_INDEX, lambda x: x.tag == "NONEXISTENT")
        is None
    )

    words = create_word_list(
        [("Target", "TARGET"), ("A", "TAG"), ("B", "TAG"), ("C", "TAG"), ("D", "TAG")]
    )
    assert (
        search_backwards(words, FIRST_WORD_INDEX + 4, lambda x: x.tag == "TARGET").token
        == "Target"
    )

    words = create_word_list(
        [("A", "TAG"), (".", SENTENCE_END), ("B", "TAG"), ("C", "TAG")]
    )
    assert (
        search_backwards(words, FIRST_WORD_INDEX + 3, lambda x: x.tag == "TAG").token
        == "B"
    )

    words = create_word_list([("A", "TAG"), ("B", "TAG"), ("Target", "TARGET")])
    assert (
        search_backwards(words, FIRST_WORD_INDEX + 2, lambda x: x.tag == "TAG").token
        == "B"
    )

    words = create_word_list(
        [("A", "TAG"), ("B", "TAG"), ("Target", "TAG"), ("C", "TAG"), ("D", "TAG")]
    )
    assert (
        search_backwards(
            words, FIRST_WORD_INDEX + 4, lambda x: x.token == "Target"
        ).token
        == "Target"
    )

    words = create_word_list([("A", "TAG"), ("B", "TAG"), ("C", "TAG")])
    with pytest.raises(IndexError):
        search_backwards(words, FIRST_WORD_INDEX + 10, lambda x: True)
