from unittest.mock import Mock, MagicMock

import pytest
import spacy

from ideadensity.depid import (
    EXCLUDED_DETERMINERS,
    EXCLUDED_NSUBJ,
    depid,
    filter_excluded_determiners,
    filter_excluded_nsubjs,
    filter_i_you_subject,
    filter_cc,
)


try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise OSError(
        "The 'en_core_web_sm' model is not installed. Please install it using: `python -m spacy download en_core_web_sm`."
    )


def test_depid_basic():
    text = "The cat sat on the mat."
    density, word_count, dependencies = depid(text)
    assert isinstance(density, float)
    assert word_count == 6
    assert len(dependencies) > 0


def test_depid_empty_text():
    text = ""
    density, word_count, dependencies = depid(text)
    assert density == 0.0
    assert word_count == 0
    assert len(dependencies) == 0


def test_depid_punctuation_and_spaces():
    text = "Hello,   world!   How are you?"
    density, word_count, dependencies = depid(text)
    assert word_count == 5


def test_depid_sentence_filter():
    text = "I am happy. The sun is shining."
    density, word_count, dependencies = depid(
        text, custom_sentence_filters=[filter_i_you_subject]
    )
    assert "I" not in [dep[0] for dep in dependencies]


def test_depid_token_filter():
    text = "The cat and the dog are playing."
    density, word_count, dependencies = depid(
        text, custom_token_filters=[filter_excluded_determiners]
    )
    assert "the" not in [dep[0] for dep in dependencies]


def test_depid_custom_filters():
    def custom_sentence_filter(sent):
        return len(sent) > 3

    def custom_token_filter(token):
        return token.pos_ != "VERB"

    text = "I run. The quick brown fox jumps over the lazy dog."
    density, word_count, dependencies = depid(
        text,
        custom_sentence_filters=[custom_sentence_filter],
        custom_token_filters=[custom_token_filter],
    )
    assert len(dependencies) > 0
    assert "run" not in [dep[0] for dep in dependencies]
    assert "jumps" not in [dep[0] for dep in dependencies]


def test_depid_dependency_types():
    text = "The big brown dog quickly chased the small cat."
    density, word_count, dependencies = depid(text)
    dep_types = set(dep[1] for dep in dependencies)
    assert dep_types.issubset(set(["amod", "nsubj", "advmod", "dobj"]))


def test_depid_density_calculation():
    text = "The cat sat. The dog ran."
    density, word_count, dependencies = depid(text)
    expected_density = len(dependencies) / word_count
    assert abs(density - expected_density) < 1e-6


def test_depid_word_count_accuracy():
    text = "This is a test sentence with ten words in it."
    density, word_count, dependencies = depid(text)
    assert word_count == 10


def test_depid_with_is_depid_r_true():
    text = "The cat sat on the mat."
    density, word_count, dependencies = depid(text, is_depid_r=True)
    assert isinstance(density, float)
    assert word_count == 6
    assert isinstance(dependencies, set)
    assert len(dependencies) > 0


def test_depid_is_depid_r_true_unique_dependencies():
    text = "The cat sat on the mat. The cat sat on the mat."
    density, word_count, dependencies = depid(text, is_depid_r=True)
    assert len(dependencies) < word_count
    assert isinstance(dependencies, set)

    # Check if all elements in the set are unique
    assert len(dependencies) == len(set(dependencies))


def test_depid_is_depid_r_comparison():
    text = "The quick brown fox jumps over the lazy dog."
    density_r, word_count_r, dependencies_r = depid(text, is_depid_r=True)
    density, word_count, dependencies = depid(text, is_depid_r=False)

    assert density_r == density
    assert word_count_r == word_count
    assert set(dependencies) == dependencies_r
    assert isinstance(dependencies_r, set)
    assert isinstance(dependencies, list)


def test_depid_is_depid_r_empty_text():
    text = ""
    density, word_count, dependencies = depid(text, is_depid_r=True)
    assert density == 0.0
    assert word_count == 0
    assert isinstance(dependencies, set)
    assert len(dependencies) == 0


def test_depid_is_depid_r_with_filters():
    text = "The cat and the dog are playing. I am watching them."
    density, word_count, dependencies = depid(
        text,
        is_depid_r=True,
        custom_sentence_filters=[filter_i_you_subject],
        custom_token_filters=[filter_excluded_determiners, filter_excluded_nsubjs],
    )
    assert isinstance(dependencies, set)
    assert "the" not in [dep[0] for dep in dependencies]
    assert "I" not in [dep[0] for dep in dependencies]
    assert len(dependencies) > 0


@pytest.fixture
def mock_span():
    mock_span = MagicMock(spec=spacy.tokens.Span)
    return mock_span


@pytest.fixture
def mock_token():
    mock_token = Mock()
    return mock_token


def test_is_i_you_subject_with_i_subject(mock_span, mock_token):
    mock_token.text = "I"
    mock_token.dep_ = "nsubj"
    mock_token.head.dep_ = "ROOT"

    mock_span.__iter__.return_value = [mock_token]

    result = filter_i_you_subject(mock_span)

    assert result == False


def test_is_i_you_subject_with_you_subject(mock_token, mock_span):
    mock_token.text = "You"
    mock_token.dep_ = "nsubj"
    mock_token.head.dep_ = "ROOT"

    mock_span.__iter__.return_value = [mock_token]

    result = filter_i_you_subject(mock_span)

    assert result == False


def test_is_i_you_subject_with_other_subject(mock_token, mock_span):
    mock_token.text = "He"
    mock_token.dep_ = "nsubj"
    mock_token.head.dep_ = "ROOT"
    mock_span.__iter__.return_value = [mock_token]

    result = filter_i_you_subject(mock_span)

    assert result == True


def test_is_i_you_subject_with_i_not_subject(mock_token, mock_span):
    mock_token.text = "I"
    mock_token.dep_ = "dobj"
    mock_token.head.dep_ = "ROOT"
    mock_span.__iter__.return_value = [mock_token]

    result = filter_i_you_subject(mock_span)

    assert result == True


def test_is_i_you_subject_with_i_not_root_verb(mock_token, mock_span):
    mock_token.text = "I"
    mock_token.dep_ = "nsubj"
    mock_token.head.dep_ = "conj"
    mock_span.__iter__.return_value = [mock_token]

    result = filter_i_you_subject(mock_span)

    assert result == True


def test_is_excluded_determiner_with_excluded_determiner(mock_token):
    mock_token.dep_ = "det"
    mock_token.text = "the"

    result = filter_excluded_determiners(mock_token)

    assert result == False


def test_is_excluded_determiner_with_non_excluded_determiner(mock_token):
    mock_token.dep_ = "det"
    mock_token.text = "this"

    result = filter_excluded_determiners(mock_token)

    assert result == True


def test_is_excluded_determiner_with_non_determiner(mock_token):
    mock_token.dep_ = "nsubj"
    mock_token.text = "the"

    result = filter_excluded_determiners(mock_token)

    assert result == True


def test_is_excluded_determiner_case_insensitive(mock_token):
    mock_token.dep_ = "det"
    mock_token.text = "The"

    result = filter_excluded_determiners(mock_token)

    assert result == False


def test_is_excluded_determiner_with_all_excluded_determiners(mock_token):
    mock_token.dep_ = "det"

    for determiner in EXCLUDED_DETERMINERS:
        mock_token.text = determiner
        result = filter_excluded_determiners(mock_token)
        assert result == False


def test_is_excluded_nsubj_with_excluded_subject(mock_token):
    mock_token.dep_ = "nsubj"
    mock_token.text = "it"

    result = filter_excluded_nsubjs(mock_token)

    assert result == False


def test_is_excluded_nsubj_with_non_excluded_subject(mock_token):
    mock_token.dep_ = "nsubj"
    mock_token.text = "he"

    result = filter_excluded_nsubjs(mock_token)

    assert result == True


def test_is_excluded_nsubj_with_non_nsubj(mock_token):
    mock_token.dep_ = "dobj"
    mock_token.text = "it"

    result = filter_excluded_nsubjs(mock_token)

    assert result == True


def test_is_excluded_nsubj_case_insensitive(mock_token):
    mock_token.dep_ = "nsubj"
    mock_token.text = "It"

    result = filter_excluded_nsubjs(mock_token)

    assert result == False


def test_is_excluded_nsubj_with_all_excluded_subjects(mock_token):
    mock_token.dep_ = "nsubj"

    for subject in EXCLUDED_NSUBJ:
        mock_token.text = subject
        result = filter_excluded_nsubjs(mock_token)
        assert result == False


def test_is_excluded_cc_with_cc(mock_token):
    mock_token.dep_ = "cc"

    result = filter_cc(mock_token)

    assert result == False


def test_is_excluded_cc_with_non_cc(mock_token):
    mock_token.dep_ = "conj"

    result = filter_cc(mock_token)

    assert result == True


def test_is_excluded_cc_case_sensitivity(mock_token):
    mock_token.dep_ = "CC"

    result = filter_cc(mock_token)

    assert result == True


def test_is_excluded_cc_with_various_dependencies(mock_token):
    non_cc_dependencies = ["nsubj", "dobj", "amod", "prep", "pobj"]

    for dep in non_cc_dependencies:
        mock_token.dep_ = dep
        result = filter_cc(mock_token)
        assert result == True, f"Expected True for dependency '{dep}'"


def test_depid_with_excluded_determiner_filter():
    text = "The cat sat on the mat."
    density1, _, deps1 = depid(text, use_excluded_determiner_filter=True)
    density2, _, deps2 = depid(text, use_excluded_determiner_filter=False)

    assert density1 < density2
    assert len(deps1) < len(deps2)
    assert "the" not in [dep[0].lower() for dep in deps1]
    assert "the" in [dep[0].lower() for dep in deps2]


def test_depid_with_excluded_nsubj_filter():
    text = "It is raining. This is a test."
    density1, _, deps1 = depid(text, use_excluded_nsubj_filter=True)
    density2, _, deps2 = depid(text, use_excluded_nsubj_filter=False)

    assert density1 < density2
    assert len(deps1) < len(deps2)
    assert "it" not in [dep[0].lower() for dep in deps1]
    assert "this" not in [dep[0].lower() for dep in deps1]
    assert "it" in [dep[0].lower() for dep in deps2]
    assert "this" in [dep[0].lower() for dep in deps2]


def test_depid_with_excluded_cc_filter():
    text = "The cat and the dog are playing."
    density1, _, deps1 = depid(text, use_excluded_cc_filter=True)
    density2, _, deps2 = depid(text, use_excluded_cc_filter=False)

    assert density1 < density2
    assert len(deps1) < len(deps2)
    assert "and" not in [dep[0].lower() for dep in deps1]
    assert "and" in [dep[0].lower() for dep in deps2]


def test_depid_with_i_you_subject_filter():
    text = "I am happy. You are smart. She is kind."
    density1, _, deps1 = depid(text, use_i_you_subject_filter=True)
    density2, _, deps2 = depid(text, use_i_you_subject_filter=False)

    assert density1 < density2
    assert len(deps1) < len(deps2)
    assert "i" not in [dep[0].lower() for dep in deps1]
    assert "you" not in [dep[0].lower() for dep in deps1]
    assert "i" in [dep[0].lower() for dep in deps2]
    assert "you" in [dep[0].lower() for dep in deps2]


def test_depid_with_all_filters():
    text = "The cat and the dog are playing. I am watching them. It is fun."
    density1, _, deps1 = depid(
        text,
        use_excluded_determiner_filter=True,
        use_excluded_nsubj_filter=True,
        use_excluded_cc_filter=True,
        use_i_you_subject_filter=True,
    )
    density2, _, deps2 = depid(
        text,
        use_excluded_determiner_filter=False,
        use_excluded_nsubj_filter=False,
        use_excluded_cc_filter=False,
        use_i_you_subject_filter=False,
    )

    assert density1 < density2
    assert len(deps1) < len(deps2)
    assert not any(
        word in [dep[0].lower() for dep in deps1] for word in ["the", "and", "i", "it"]
    )
    assert all(
        word in [dep[0].lower() for dep in deps2] for word in ["the", "and", "i", "it"]
    )
