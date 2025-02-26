from unittest.mock import patch

import pytest

from ideadensity.tagger import tag_text
from ideadensity.utils.constants import SENTENCE_END


@pytest.mark.skip(reason="This test fails on github actions")
@patch("spacy.load")
def test_spacy_model_not_found(mock_spacy_load):
    mock_spacy_load.side_effect = OSError("Model 'en_core_web_sm' not found.")

    with pytest.raises(OSError) as excinfo:
        tag_text("This is a test sentence.")

    assert "The 'en_core_web_sm' model is not installed." in str(excinfo.value)
    assert "Please install it using: `python -m spacy download en_core_web_sm`" in str(
        excinfo.value
    )


@pytest.mark.parametrize(
    "invalid_input",
    [
        None,
        ["list", "is", "invalid"],
        {"dictionary": "invalid"},
    ],
)
def test_tag_text_invalid_input(invalid_input):
    with pytest.raises(TypeError):
        tag_text(invalid_input)
