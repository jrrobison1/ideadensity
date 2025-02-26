"""
Tests for the idea density rater.
Total Expected from CPIDR 3.2:
    847 words
    436 propositions
    0.515 idea density

Total Actual found in thiss python port:
    847 words
    434 propositions
    0.512 idea density
"""

from unittest.mock import patch

import pytest
import spacy

from ideadensity.idea_density_rater import count_words_and_propositions, rate_text
from ideadensity.tagger import tag_text
from ideadensity.word_item import WordListItem, WordList
from ideadensity.utils.word_search_utils import beginning_of_sentence
from ideadensity.utils.constants import SENTENCE_END

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise OSError(
        "The 'en_core_web_sm' model is not installed. Please install it using: `python -m spacy download en_core_web_sm`."
    )


def test_turner_greene_sentence_1():
    sentence = "Louise and Ann went to the movies last night."

    word_count, proposition_count, idea_density, word_list = rate_text(
        sentence, speech_mode=False
    )

    assert word_count == 9
    assert proposition_count == 4
    assert idea_density == pytest.approx(0.444, abs=1e-3)


def test_turner_greene_sentence_2():
    sentence = "They met Charlie there."

    word_count, proposition_count, idea_density, word_list = rate_text(
        sentence, speech_mode=False
    )

    assert word_count == 4
    assert proposition_count == 2
    assert idea_density == pytest.approx(0.5, abs=1e-3)


def test_turner_greene_sentence_3():
    sentence = "Afterwards they all went for a chocolate sundae, but the ice cream parlor was closed."

    word_count, proposition_count, idea_density, word_list = rate_text(
        sentence, speech_mode=False
    )

    assert word_count == 15
    assert proposition_count == 6
    assert idea_density == pytest.approx(0.4, abs=1e-3)


def test_turner_greene_sentence_4():
    sentence = "Three fourths of Australia's sheep are pure Merinos."

    word_count, proposition_count, idea_density, word_list = rate_text(
        sentence, speech_mode=False
    )

    assert word_count == 8
    assert proposition_count == 4
    assert idea_density == pytest.approx(0.5, abs=1e-3)


def test_turner_greene_sentence_5():
    sentence = "They are popular because of the large amount of semiarid land."

    word_count, proposition_count, idea_density, word_list = rate_text(
        sentence, speech_mode=False
    )

    assert word_count == 11
    assert proposition_count == 6
    assert idea_density == pytest.approx(0.545, abs=1e-3)


def test_turner_greene_sentence_6():
    sentence = "The Merino thrives on the grasses and low bushes which grow on semiarid plains."

    word_count, proposition_count, idea_density, word_list = rate_text(
        sentence, speech_mode=False
    )

    assert word_count == 14
    assert proposition_count == 8
    assert idea_density == pytest.approx(0.571, abs=1e-3)


def test_turner_greene_sentence_7():
    sentence = "They are known for their heavy fleeces of fine-quality wool which bring a high price from textile manufacturers."

    word_count, proposition_count, idea_density, word_list = rate_text(
        sentence, speech_mode=False
    )

    assert word_count == 19

    # Note: The original CPIDR 3.2 finds 8 propositions
    assert proposition_count == 10
    assert idea_density == pytest.approx(0.526, abs=1e-3)


def test_turner_greene_sentence_8():
    sentence = "...I unbolted the door and went out."

    word_count, proposition_count, idea_density, word_list = rate_text(
        sentence, speech_mode=False
    )

    assert word_count == 7

    # Note: The original CPIDR 3.2 finds 4 propositions
    assert proposition_count == 3

    assert idea_density == pytest.approx(0.429, abs=1e-3)


def test_turner_greene_sentence_9():
    sentence = "It was cool outside in the early morning, and the sun had not yet dried the dew that had come when the wind died down."

    word_count, proposition_count, idea_density, word_list = rate_text(
        sentence, speech_mode=False
    )

    assert word_count == 25
    assert proposition_count == 10
    assert idea_density == pytest.approx(0.4, abs=1e-3)


def test_turner_greene_sentence_10():
    sentence = "I hunted around in the shed behind the inn and found a sort of mattock, and went down toward the stream to try and dig some worms for bait."

    word_count, proposition_count, idea_density, word_list = rate_text(
        sentence, speech_mode=False
    )

    assert word_count == 29
    assert proposition_count == 16
    assert idea_density == pytest.approx(0.552, abs=1e-3)


def test_turner_greene_sentence_11():
    sentence = "The stream was clear and shallow but it did not look trouty."

    word_count, proposition_count, idea_density, word_list = rate_text(
        sentence, speech_mode=False
    )

    assert word_count == 12
    assert proposition_count == 6
    assert idea_density == pytest.approx(0.5, abs=1e-3)


def test_turner_greene_sentence_12():
    sentence = "On the grassy bank where it was damp, I drove the mattock into the earth and loosened a chunk of sod."

    word_count, proposition_count, idea_density, word_list = rate_text(
        sentence, speech_mode=False
    )

    assert word_count == 21

    # Note: The original CPIDR 3.2 finds 9 propositions
    assert proposition_count == 8
    assert idea_density == pytest.approx(0.381, abs=1e-3)


def test_turner_greene_sentence_13():
    sentence = "There were worms underneath."

    word_count, proposition_count, idea_density, word_list = rate_text(
        sentence, speech_mode=False
    )

    assert word_count == 4
    assert proposition_count == 2
    assert idea_density == pytest.approx(0.5, abs=1e-3)


def test_turner_greene_sentence_14():
    sentence = "They slid out of sight as I lifted the sod and I dug carefully and got a good many."

    word_count, proposition_count, idea_density, word_list = rate_text(
        sentence, speech_mode=False
    )

    assert word_count == 19
    assert proposition_count == 12
    assert idea_density == pytest.approx(0.632, abs=1e-3)


def test_turner_1987_passage_1():
    text = """
    In the request to canonize the "Frontier Priest," John Newmann, bishop of Philadelphia in the nineteenth century, 
    two miracles were attributed to him in this century. In 1923, Eva Benassi, dying from peritonitis, dramatically 
    recovered after her nurse prayed to the bishop. In 1949, Kent Lenahan, hospitalized with two skull fractures, 
    smashed bones, and a pierced lung after a traffic accident, rose from his deathbed and resumed a normal life 
    after his mother prayed ardently to John Newmann.
    """

    word_count, proposition_count, idea_density, word_list = rate_text(
        text, speech_mode=False
    )

    assert word_count == 78
    assert proposition_count == 40
    assert idea_density == pytest.approx(0.513, abs=1e-3)


def test_turner_1987_passage_2():
    text = """
    On a flat map of the earth (Mercator Projection) satellite ground traces appear to have different shapes 
    than on a sphere. The ground trace for an object in an inclined circular or elliptical orbit appears as a 
    sinusoidal trace with North - South limits equal to the inclination of the orbital plane.
    The fun starts when you start the earth rotating. When you do this, visualizing a satellite's ground trace 
    becomes more complex. As we said earlier, a point on the equator moves from west to east more rapidly than do 
    points north and south of the equator. Satellites in a circular orbit travel at a constant speed. But when 
    orbits are inclined to the equator, the component of satellite velocity which is effective in an easterly or 
    westerly direction varies continuously throughout the orbital trace.
    As the satellite crosses the equator, its easterly or westerly component of velocity is its instantaneous 
    total velocity times the cosine of its angle of inclination. When it is at the most northerly or southerly 
    portion of its orbit, its easterly or westerly component is equal to its total instantaneous velocity. To 
    put it in simpler terms, a satellite in a circular or nearly circular orbit is not moving as fast in an 
    easterly or westerly direction at the equator as it is at its most northerly or southerly point.
    In elliptical orbits only the horizontal (to the Earth's surface) velocity component contributes to the 
    ground trace. To further complicate things, the ground trace is changed because the inertial or absolute 
    speed of the satellite varies throughout the elliptical path.
    Fortunately, most of the orbits, with a few special exceptions, we deal with are nearly circular and have a 
    fairly low altitude (within 400 to 600 NM). This eases the problem considerably.
    Because the ground trace of a satellite is dependent upon the relative motion between the satellite and the 
    earth, the visualization of ground tracks becomes quite complicated. Earth rotation causes each successive track 
    of a satellite in a near earth orbit (400 NM or less) to cross the equator at a point which is west of the 
    preceding track. This phenomena is referred to as "regression of the nodes."
    """

    word_count, proposition_count, idea_density, word_list = rate_text(
        text, speech_mode=False
    )

    assert word_count == 366

    # Note: The original CPIDR 3.2 finds 191 propositions
    assert proposition_count == 190
    assert idea_density == pytest.approx(0.519, abs=1e-3)


def test_turner_1987_passage_3():
    text = """
    Wegener proposed a theory of continental drift when geologists were beginning to find conventional theories of 
    continental permanence inadequate. Previous continental drift theories held that some catastrophic event 
    initiated continental displacement. In contrast, Wegener proposed that the same forces that produce great 
    folded mountain ranges, displaced the continents. He presented evidence from such a range of sciences that 
    his theory could not easily be ignored.
    In the late Paleozoic era, according to Wegener's hypothesis, all the continents were part of one huge landmass, 
    Pangaea, occupying half the Earth's surface. The other half was covered by the primeval Pacific Ocean. Wegener 
    presented evidence that in the Jurassic period Pangaea began to break into fragments, and the weaker oceanic 
    rock yielded to allow the continents to drift apart like icebergs in water.
    The concept of continental drift first occurred to Wegener as he contemplated the apparent fit of the coastlines 
    of the Atlantic Ocean. He tested this fit using the edges of the continental shelf as the boundary between continents 
    and oceans. He postulated that the continental blocks retain the approximate outlines they acquired during the 
    breakup of Pangaea. If the younger, Tertiary folded mountains could be flattened, the pieces could be reassembled 
    into one large continent partially flooded by shallow seas. 
    """

    word_count, proposition_count, idea_density, word_list = rate_text(
        text, speech_mode=False
    )

    assert word_count == 210
    assert proposition_count == 106
    assert idea_density == pytest.approx(0.505, abs=1e-3)


def test_empty_text():
    text = ""

    word_count, proposition_count, idea_density, word_list = rate_text(
        text, speech_mode=False
    )

    assert word_count == 0
    assert proposition_count == 0
    assert idea_density == pytest.approx(0.0, abs=1e-3)


def test_none_text():
    text = None

    word_count, proposition_count, idea_density, word_list = rate_text(
        text, speech_mode=False
    )

    assert word_count == 0
    assert proposition_count == 0
    assert idea_density == pytest.approx(0.0, abs=1e-3)


def test_two_numbers():
    text = "This is 1 2 a sentence with numbers."

    word_count, proposition_count, idea_density, word_list = rate_text(
        text, speech_mode=False
    )

    assert word_count == 7
    assert proposition_count == 3
    assert idea_density == pytest.approx(0.429, abs=1e-3)


def test_one_word():
    text = "Are"

    word_count, proposition_count, idea_density, word_list = rate_text(
        text, speech_mode=False
    )

    assert word_count == 1
    assert proposition_count == 1
    assert idea_density == pytest.approx(1.0, abs=1e-3)


def test_fraction():
    text = "This is a sentence with 1 / 2 of a fraction."

    word_count, proposition_count, idea_density, word_list = rate_text(
        text, speech_mode=False
    )

    assert word_count == 9
    assert proposition_count == 4
    assert idea_density == pytest.approx(0.444, abs=1e-3)


def test_one_number():
    text = "4"

    word_count, proposition_count, idea_density, word_list = rate_text(
        text, speech_mode=False
    )

    assert word_count == 1
    assert proposition_count == 0
    assert idea_density == pytest.approx(0.0, abs=1e-3)


@pytest.fixture(scope="module")
def mock_apply_idea_counting_rules():
    with patch(
        "ideadensity.idea_density_rater.apply_idea_counting_rules"
    ) as mock_apply_rules:
        yield mock_apply_rules


def test_rate_text_with_exception(mock_apply_idea_counting_rules):
    text = "This is a test sentence."

    mock_apply_idea_counting_rules.side_effect = Exception("Mocked exception")

    result = rate_text(text)

    assert result == (0, 0, 0.0, None)


def test_count_words_and_propositions_empty_list():
    word_list = WordList([])
    word_count, proposition_count = count_words_and_propositions(word_list)
    assert word_count == 0
    assert proposition_count == 0


def test_count_words_and_propositions_only_non_words():
    word_list = WordList([("placeholder", "placeholder")])
    word_list.items.append(WordListItem("", "PUNCT", is_word=False))
    word_list.items.append(WordListItem("", "SPACE", is_word=False))
    word_list.items.append(WordListItem("", "SYM", is_word=False))

    word_count, proposition_count = count_words_and_propositions(word_list)

    assert word_count == 0
    assert proposition_count == 0


def test_count_words_and_propositions_only_propositions():
    word_list = WordList([("placeholder", "placeholder")])
    word_list.items.pop()
    word_list.items.append(
        WordListItem("run", "VERB", is_proposition=True, is_word=True)
    )
    word_list.items.append(
        WordListItem("fast", "ADV", is_proposition=True, is_word=True)
    )

    word_count, proposition_count = count_words_and_propositions(word_list)
    assert word_count == 2
    assert proposition_count == 2
