import os
import csv
import pytest
from ideadensity.utils.word_search_utils import (
    beginning_of_sentence,
    is_repetition,
    search_backwards,
    MAX_LOOKBACK,
)
from ideadensity.utils.export_utils import (
    export_cpidr_to_csv,
    export_depid_to_csv,
    export_cpidr_to_txt,
)
from ideadensity.word_item import WordListItem, WordList
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


def test_export_cpidr_to_csv(tmp_path):
    # Create test data
    tagged_text = [
        ("This", "DT"),
        ("is", "VBZ"),
        ("a", "DT"),
        ("test", "NN"),
        (".", ".")
    ]
    word_list = WordList(tagged_text)
    word_list.items[NUMBER_OF_BLANK_WORD_ITEMS + 0].is_word = True
    word_list.items[NUMBER_OF_BLANK_WORD_ITEMS + 1].is_word = True
    word_list.items[NUMBER_OF_BLANK_WORD_ITEMS + 3].is_word = True
    word_list.items[NUMBER_OF_BLANK_WORD_ITEMS + 3].is_proposition = True
    word_list.items[NUMBER_OF_BLANK_WORD_ITEMS + 3].rule_number = 5
    
    # Export to CSV
    csv_path = tmp_path / "test_cpidr.csv"
    export_cpidr_to_csv(word_list, str(csv_path))
    
    # Verify file exists
    assert os.path.exists(csv_path)
    
    # Read and verify contents
    rows = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            rows.append(row)
    
    # Check header
    assert rows[0] == ['Token', 'Tag', 'Is Word', 'Is Proposition', 'Rule Number']
    
    # Find the "test" row and verify it has the correct values
    test_row = None
    for row in rows[1:]:  # Skip header
        if row[0] == 'test':
            test_row = row
            break
    
    assert test_row is not None
    assert test_row[0] == 'test'
    assert test_row[1] == 'NN'
    assert test_row[2] == 'True'
    assert test_row[3] == 'True'
    assert test_row[4] == '5'


def test_export_depid_to_csv(tmp_path):
    # Create test data
    dependencies = [
        ("This", "det", "test"),
        ("is", "aux", "test"),
        ("a", "det", "test"),
        ("test", "root", "ROOT")
    ]
    
    # Export to CSV
    csv_path = tmp_path / "test_depid.csv"
    export_depid_to_csv(dependencies, str(csv_path))
    
    # Verify file exists
    assert os.path.exists(csv_path)
    
    # Read and verify contents
    rows = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            rows.append(row)
    
    # Check header
    assert rows[0] == ['Token', 'Dependency', 'Head']
    
    # Verify all dependencies were written correctly
    assert len(rows) == 5  # header + 4 dependencies
    
    # Check specific row
    assert rows[4] == ['test', 'root', 'ROOT']


def test_export_cpidr_to_txt(tmp_path):
    # Create test data
    tagged_text = [
        ("This", "DT"),
        ("is", "VBZ"),
        ("a", "DT"),
        ("test", "NN"),
        (".", ".")
    ]
    word_list = WordList(tagged_text)
    word_list.items[NUMBER_OF_BLANK_WORD_ITEMS + 0].is_word = True
    word_list.items[NUMBER_OF_BLANK_WORD_ITEMS + 1].is_word = True
    word_list.items[NUMBER_OF_BLANK_WORD_ITEMS + 3].is_word = True
    word_list.items[NUMBER_OF_BLANK_WORD_ITEMS + 1].is_proposition = True
    word_list.items[NUMBER_OF_BLANK_WORD_ITEMS + 1].rule_number = 200
    
    # Test data for the export function
    text = "This is a test."
    word_count = 3
    proposition_count = 1
    density = 0.333
    
    # Export to TXT
    txt_path = tmp_path / "test_cpidr.txt"
    export_cpidr_to_txt(word_list, text, word_count, proposition_count, density, str(txt_path))
    
    # Verify file exists
    assert os.path.exists(txt_path)
    
    # Read and verify contents
    with open(txt_path, 'r', encoding='utf-8') as txtfile:
        content = txtfile.read()
    
    # Check that the file contains expected elements
    assert "ideadensity" in content  # Check for ideadensity in header
    assert f'"{text[:50]}' in content
    assert "This" in content
    assert "is" in content
    assert "VBZ" in content
    assert "W P" in content  # is is both a word and proposition
    assert "test" in content
    
    # Check summary section
    assert f"     {proposition_count} propositions" in content
    assert f"     {word_count} words" in content
    assert f" {density:.3f} density" in content
