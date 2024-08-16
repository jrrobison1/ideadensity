import pytest
from pycpidr.idea_density_rater_rules import (
    adjust_word_order,
    identify_words_and_adjust_tags,
    identify_potential_propositions,
)
from pycpidr.word_item import WordListItem
from pycpidr.utils.constants import (
    SENTENCE_END,
    RuleNumber,
    DEFAULT_PROPOSITIONS,
    VERBS,
    NOUNS,
)

NUMBER_OF_BLANK_WORD_ITEMS = 10
FIRST_WORD_INDEX = NUMBER_OF_BLANK_WORD_ITEMS


@pytest.fixture
def create_word_list():
    def _create_word_list(tokens_and_tags):
        return [WordListItem() for _ in range(NUMBER_OF_BLANK_WORD_ITEMS)] + [
            WordListItem(token, tag, is_word=token[0].isalnum() and tag != "SYM")
            for token, tag in tokens_and_tags
        ]

    return _create_word_list


def test_sentence_end_marker(create_word_list):
    word_list = create_word_list([("^", "")])
    identify_words_and_adjust_tags(word_list, FIRST_WORD_INDEX, False)
    assert word_list[FIRST_WORD_INDEX].tag == SENTENCE_END
    assert word_list[FIRST_WORD_INDEX].rule_number == RuleNumber.SENTENCE_END_MARKER


def test_alphanumeric_word(create_word_list):
    word_list = create_word_list([("hello", "NN")])
    identify_words_and_adjust_tags(word_list, FIRST_WORD_INDEX, False)
    assert word_list[FIRST_WORD_INDEX].is_word == True
    assert word_list[FIRST_WORD_INDEX].rule_number == RuleNumber.ALPHANUMERIC_WORD


def test_combine_consecutive_cardinals(create_word_list):
    word_list = create_word_list([("10", "CD"), ("20", "CD"), ("thirty", "CD")])
    identify_words_and_adjust_tags(word_list, FIRST_WORD_INDEX + 1, False)
    assert len(word_list) == NUMBER_OF_BLANK_WORD_ITEMS + 2
    assert word_list[FIRST_WORD_INDEX].token == "10 20"
    assert (
        word_list[FIRST_WORD_INDEX].rule_number
        == RuleNumber.COMBINE_CONSECUTIVE_CARDINALS
    )


def test_combine_cardinals_with_separator(create_word_list):
    word_list = create_word_list([("10", "CD"), (".", ""), ("5", "CD")])
    identify_words_and_adjust_tags(word_list, FIRST_WORD_INDEX + 2, False)
    assert len(word_list) == NUMBER_OF_BLANK_WORD_ITEMS + 1
    assert word_list[FIRST_WORD_INDEX].token == "10.5"
    assert (
        word_list[FIRST_WORD_INDEX].rule_number
        == RuleNumber.COMBINE_CARDINALS_WITH_SEPARATOR
    )


def test_repetition_in_speech_mode(create_word_list):
    word_list = create_word_list([("the", "DT"), ("the", "DT")])
    identify_words_and_adjust_tags(word_list, FIRST_WORD_INDEX + 1, True)
    assert word_list[FIRST_WORD_INDEX].is_proposition == False
    assert word_list[FIRST_WORD_INDEX].is_word == False
    assert word_list[FIRST_WORD_INDEX].tag == ""
    assert word_list[FIRST_WORD_INDEX].rule_number == 20


def test_negation_identification(create_word_list):
    word_list = create_word_list([("not", "")])
    identify_words_and_adjust_tags(word_list, FIRST_WORD_INDEX, False)
    assert word_list[FIRST_WORD_INDEX].is_proposition == True
    assert word_list[FIRST_WORD_INDEX].tag == "NOT"
    assert word_list[FIRST_WORD_INDEX].rule_number == 50


def test_determiner_to_pronoun_adjustment(create_word_list):
    word_list = create_word_list([("that", "DT"), ("runs", "VBZ")])

    identify_words_and_adjust_tags(word_list, FIRST_WORD_INDEX + 1, False)

    assert word_list[FIRST_WORD_INDEX].tag == "PRP"
    assert word_list[FIRST_WORD_INDEX].is_proposition == False
    assert word_list[FIRST_WORD_INDEX].rule_number == 54


def test_no_adjustment_needed(create_word_list):
    word_list = create_word_list(
        [("The", "DT"), ("cat", "NN"), ("is", "VBZ"), ("happy", "JJ")]
    )
    i = adjust_word_order(word_list, FIRST_WORD_INDEX + 2, False)
    assert i == FIRST_WORD_INDEX + 2
    assert [w.token for w in word_list[FIRST_WORD_INDEX:]] == [
        "The",
        "cat",
        "is",
        "happy",
    ]


def test_aux_at_sentence_start(create_word_list):
    word_list = create_word_list(
        [
            ("Is", "VBZ"),
            ("the", "DT"),
            ("cat", "NN"),
            ("happy", "JJ"),
            ("?", SENTENCE_END),
        ]
    )
    i = adjust_word_order(word_list, FIRST_WORD_INDEX, False)
    assert i == FIRST_WORD_INDEX
    assert [w.token for w in word_list[FIRST_WORD_INDEX:]] == [
        "Is/moved",
        "the",
        "cat",
        "happy",
        "Is",
        "?",
    ]


def test_aux_after_interrogative(create_word_list):
    word_list = create_word_list(
        [
            ("Why", "WRB"),
            ("is", "VBZ"),
            ("the", "DT"),
            ("cat", "NN"),
            ("happy", "JJ"),
            ("?", SENTENCE_END),
        ]
    )
    i = adjust_word_order(word_list, FIRST_WORD_INDEX + 1, False)
    assert i == FIRST_WORD_INDEX + 1
    assert [w.token for w in word_list[FIRST_WORD_INDEX:]] == [
        "Why",
        "is/moved",
        "the",
        "cat",
        "happy",
        "is",
        "?",
    ]


def test_aux_moved_to_end_of_sentence(create_word_list):
    word_list = create_word_list(
        [
            ("Where", "WRB"),
            ("could", "MD"),
            ("it", "PRP"),
            ("have", "VB"),
            ("been", "VBN"),
            ("?", SENTENCE_END),
        ]
    )
    i = adjust_word_order(word_list, FIRST_WORD_INDEX + 4, False)
    assert i == FIRST_WORD_INDEX + 4
    assert [w.token for w in word_list[FIRST_WORD_INDEX:]] == [
        "Where",
        "could",
        "it",
        "have",
        "been",
        "?",
    ]


def test_aux_not_moved_when_not_needed(create_word_list):
    word_list = create_word_list(
        [("The", "DT"), ("cat", "NN"), ("can", "MD"), ("sleep", "VB")]
    )
    i = adjust_word_order(word_list, FIRST_WORD_INDEX + 2, False)
    assert i == FIRST_WORD_INDEX + 2
    assert [w.token for w in word_list[FIRST_WORD_INDEX:]] == [
        "The",
        "cat",
        "can",
        "sleep",
    ]


def test_original_aux_marked_as_ignored(create_word_list):
    word_list = create_word_list(
        [
            ("Is", "VBZ"),
            ("the", "DT"),
            ("cat", "NN"),
            ("happy", "JJ"),
            ("?", SENTENCE_END),
        ]
    )
    i = adjust_word_order(word_list, FIRST_WORD_INDEX, False)
    assert word_list[FIRST_WORD_INDEX].tag == ""
    assert word_list[FIRST_WORD_INDEX].is_proposition == False
    assert word_list[FIRST_WORD_INDEX].is_word == False
    assert word_list[FIRST_WORD_INDEX].token == "Is/moved"


def test_new_aux_position_marked_correctly(create_word_list):
    word_list = create_word_list(
        [
            ("Is", "VBZ"),
            ("the", "DT"),
            ("cat", "NN"),
            ("happy", "JJ"),
            ("?", SENTENCE_END),
        ]
    )
    i = adjust_word_order(word_list, FIRST_WORD_INDEX, False)
    new_aux = next(w for w in word_list[FIRST_WORD_INDEX:] if w.token == "Is")
    assert new_aux.tag == "VBZ"
    assert new_aux.is_proposition == True
    assert new_aux.is_word == True
    assert new_aux.rule_number == 101


def test_default_propositions(create_word_list):
    word_list = create_word_list([("run", "VB")])
    identify_potential_propositions(word_list, FIRST_WORD_INDEX, False)
    assert word_list[FIRST_WORD_INDEX].is_proposition == True
    assert word_list[FIRST_WORD_INDEX].rule_number == 200


def test_articles_not_propositions(create_word_list):
    word_list = create_word_list([("the", "DT")])
    identify_potential_propositions(word_list, FIRST_WORD_INDEX, False)
    assert word_list[FIRST_WORD_INDEX].is_proposition == False
    assert word_list[FIRST_WORD_INDEX].rule_number == 201


def test_correlating_conjunctions(create_word_list):
    word_list = create_word_list([("either", "CC"), ("or", "CC")])
    identify_potential_propositions(word_list, FIRST_WORD_INDEX + 1, False)
    assert word_list[FIRST_WORD_INDEX].is_proposition == False
    assert word_list[FIRST_WORD_INDEX].rule_number == 203


def test_and_then_single_proposition(create_word_list):
    word_list = create_word_list([("and", "CC"), ("then", "RB")])
    identify_potential_propositions(word_list, FIRST_WORD_INDEX + 1, False)
    assert word_list[FIRST_WORD_INDEX + 1].is_proposition == False
    assert word_list[FIRST_WORD_INDEX + 1].rule_number == 204


def test_to_not_proposition_at_sentence_end(create_word_list):
    word_list = create_word_list([("to", "TO"), (".", SENTENCE_END)])
    identify_potential_propositions(word_list, FIRST_WORD_INDEX + 1, False)
    assert word_list[FIRST_WORD_INDEX].is_proposition == False
    assert word_list[FIRST_WORD_INDEX].rule_number == 206


def test_modal_proposition_at_sentence_end(create_word_list):
    word_list = create_word_list([("can", "MD"), (".", SENTENCE_END)])
    identify_potential_propositions(word_list, FIRST_WORD_INDEX + 1, False)
    assert word_list[FIRST_WORD_INDEX].is_proposition == True
    assert word_list[FIRST_WORD_INDEX].rule_number == 207


def test_cardinal_number_proposition(create_word_list):
    word_list = create_word_list([("3", "CD"), ("cats", "NNS")])
    identify_potential_propositions(word_list, FIRST_WORD_INDEX, False)
    assert word_list[FIRST_WORD_INDEX].is_proposition == True
    assert word_list[FIRST_WORD_INDEX].rule_number == 210


def test_cardinal_number_not_proposition(create_word_list):
    word_list = create_word_list([("1941", "CD"), ("was", "VBD")])
    identify_potential_propositions(word_list, FIRST_WORD_INDEX, False)
    assert word_list[FIRST_WORD_INDEX].is_proposition == False
    assert word_list[FIRST_WORD_INDEX].rule_number == 210


def test_negative_polarity_not_unless(create_word_list):
    word_list = create_word_list([("not", "NOT"), ("go", "VB"), ("unless", "IN")])
    identify_potential_propositions(word_list, FIRST_WORD_INDEX + 2, False)
    assert word_list[FIRST_WORD_INDEX].is_proposition == False
    assert word_list[FIRST_WORD_INDEX].rule_number == 211


def test_negative_polarity_not_any(create_word_list):
    word_list = create_word_list([("not", "NOT"), ("any", "DT")])
    identify_potential_propositions(word_list, FIRST_WORD_INDEX + 1, False)
    assert word_list[FIRST_WORD_INDEX + 1].is_proposition == False
    assert word_list[FIRST_WORD_INDEX + 1].rule_number == 212


def test_going_to_before_verb(create_word_list):
    word_list = create_word_list([("going", "VBG"), ("to", "TO"), ("run", "VB")])
    identify_potential_propositions(word_list, FIRST_WORD_INDEX + 2, False)
    assert word_list[FIRST_WORD_INDEX].is_proposition == False
    assert word_list[FIRST_WORD_INDEX + 1].is_proposition == False
    assert word_list[FIRST_WORD_INDEX].rule_number == 213
    assert word_list[FIRST_WORD_INDEX + 1].rule_number == 213


def test_if_then_single_conjunction(create_word_list):
    word_list = create_word_list(
        [("if", "IN"), ("it", "PRP"), ("rains", "VBZ"), ("then", "RB"), ("stay", "VB")]
    )
    identify_potential_propositions(word_list, FIRST_WORD_INDEX + 4, False)
    assert word_list[FIRST_WORD_INDEX + 3].is_proposition == False
    assert word_list[FIRST_WORD_INDEX + 3].rule_number == 214


def test_each_other_as_pronoun(create_word_list):
    word_list = create_word_list([("each", "DT"), ("other", "JJ")])
    identify_potential_propositions(word_list, FIRST_WORD_INDEX + 1, False)
    assert word_list[FIRST_WORD_INDEX].tag == "PRP"
    assert word_list[FIRST_WORD_INDEX + 1].tag == "PRP"
    assert word_list[FIRST_WORD_INDEX].is_proposition == False
    assert word_list[FIRST_WORD_INDEX + 1].is_proposition == False
    assert word_list[FIRST_WORD_INDEX].rule_number == 225
    assert word_list[FIRST_WORD_INDEX + 1].rule_number == 225


def test_how_come_single_proposition(create_word_list):
    word_list = create_word_list([("how", "WRB"), ("come", "VB")])
    identify_potential_propositions(word_list, FIRST_WORD_INDEX + 1, False)
    assert word_list[FIRST_WORD_INDEX + 1].is_proposition == False
    assert word_list[FIRST_WORD_INDEX + 1].tag == "WRB"
    assert word_list[FIRST_WORD_INDEX + 1].rule_number == 230
