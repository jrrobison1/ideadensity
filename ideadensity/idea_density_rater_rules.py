import logging
from typing import Callable, List

from ideadensity.utils.constants import *
from ideadensity.utils.word_search_utils import (
    beginning_of_sentence,
    is_repetition,
    search_backwards,
)
from ideadensity.word_item import WordListItem

logger = logging.getLogger(__name__)

MAX_LOOKAHEAD = 5


def identify_words_and_adjust_tags(
    word_list: List[WordListItem], i: int, speech_mode: bool
) -> int:
    """
    Identify words and adjust tags based on specific rules.

    This function applies various rules to identify words, adjust tags, and handle
    special cases such as repetitions and contractions. It processes the current word
    and its context in the word list.

    Args:
        word_list (List[WordListItem]): The list of WordListItem objects to process.
        i (int): The current index in the word list.
        speech_mode (bool): Whether the text is in speech mode.

    Returns:
        int: The updated index after processing.

    Rules applied:
        001: Mark '^' as sentence end.
        002: Identify alphanumeric tokens as words.
        003: Combine consecutive cardinal numbers.
        004: Combine cardinal numbers separated by non-alphanumeric characters.
        020-023: Handle various forms of repetition in speech mode.
        050: Identify negations and contractions.
        054: Adjust 'that' and 'this' from determiners to pronouns when followed by verbs or adverbs.

    Note:
        This function may modify the word_list in-place, including deleting or combining items.
    """
    word = word_list[i]
    previous = word_list[i - 1]
    two_words_back = word_list[i - 2]

    # 001
    # The symbol  ^  used to mark broken-off spoken sentences
    # is an end-of-sentence marker.
    if word.token == "^":
        word.tag = SENTENCE_END
        word.rule_number = RuleNumber.SENTENCE_END_MARKER

    # 002
    # The item is a word if its token starts with a letter or digit
    # and its tag is not SYM (symbol).
    if word.token[0].isalnum() and word.tag != "SYM":
        word.is_word = True
        word.rule_number = RuleNumber.ALPHANUMERIC_WORD

    # 003
    # Two cardinal numbers in immediate succession are combined into one
    # (Uncommon situation; the next one is much more common)
    if word.tag == "CD" and previous.tag == "CD":
        previous.token = f"{previous.token} {word.token}"  # adjust token
        previous.rule_number = RuleNumber.COMBINE_CONSECUTIVE_CARDINALS
        i -= 1
        word = word_list[i]
        previous = word_list[i - 1]
        two_words_back = word_list[i - 2]
        del word_list[i + 1]

    # 004
    # Cardinal + nonalphanumeric + cardinal are combined into one token
    # (Common situation, for handling fractions, decimals, etc.)
    if (
        word.tag == "CD"  # current token is a number
        and len(previous.token) > 0  # preceding token contains some characters
        and not previous.token[0].isalnum()  # the first of which is nonalphanumeric
        and two_words_back.tag == "CD"  # pre-preceding token is also a number
    ):
        two_words_back.token = two_words_back.token + previous.token + word.token
        two_words_back.rule_number = RuleNumber.COMBINE_CARDINALS_WITH_SEPARATOR
        i -= 2
        word = word_list[i]
        previous = word_list[i - 1]
        two_words_back = word_list[i - 2]
        del word_list[i + 1 : i + 3]

    # 020
    # Repetition of the form "A A" is simplified to "A".
    # The first A can be an initial substring of the second one.
    # Both remain in the word count.
    if speech_mode:
        if is_repetition(previous.token, word.token):
            previous.is_proposition = False
            previous.is_word = False
            previous.tag = ""
            previous.rule_number = 20

    # 021, 022
    # Repetition of the form "A Punct A" is simplified to "A".
    # Repetition of the form "A B A" is simplified to "A B".
    # Both A's remain in the word count.
    # The first A can be an initial substring of the second one.
    # Punct is anything with tag "." or "," or ":".
    if speech_mode:
        if (
            is_repetition(two_words_back.token, word.token)
            and word.tag not in PUNCTUATION
        ):
            two_words_back.tag = ""
            two_words_back.is_word = False
            two_words_back.is_proposition = False
            two_words_back.rule_number = 22
            if previous.tag in PUNCTUATION:
                previous.tag = ""
                previous.is_word = False
                previous.is_proposition = False
                previous.rule_number = 21

    # 023
    # Repetition of the form "A B Punct A B" is simplified to "A B".
    # Both A's and B's remain in the word count.
    # The first A (or B) can be an initial substring of the second one.
    # Punct is anything with tag "." or "," or ":".
    if speech_mode:
        if (
            is_repetition(word_list[i - 3].token, word.token)
            and is_repetition(word_list[i - 4].token, previous.token)
            and word_list[i - 2].tag in PUNCTUATION
        ):
            word_list[i - 4].tag = word_list[i - 3].tag = word_list[i - 2].tag = ""
            word_list[i - 4].is_word = word_list[i - 3].is_word = word_list[
                i - 2
            ].is_word = False
            word_list[i - 4].is_proposition = word_list[i - 3].is_proposition = (
                word_list[i - 2].is_proposition
            ) = False
            word_list[i - 4].rule_number = word_list[i - 3].rule_number = word_list[
                i - 2
            ].rule_number = 23

    # 050
    # 'not' and any word ending in "n't" are assumed to be propositions and
    # their tag is changed to NOT.
    if (
        word.lowercase_token == "not"
        or word.lowercase_token.endswith("n't")
        or word.lowercase_token in NT
    ):
        word.is_proposition = True
        word.tag = "NOT"
        word.rule_number = 50

    # 054
    # 'that/DT' or 'this/DT' is a pronoun, not a determiner, if the word following it
    # is any kind of verb or adverb.
    if (previous.lowercase_token == "that" or previous.lowercase_token == "this") and (
        word.tag in VERBS or word.tag in ADVERBS
    ):
        previous.tag = "PRP"
        previous.rule_number = 54
        previous.is_proposition = False

    return i


def _should_move_auxiliary_verb(word_list: List[WordListItem], i: int) -> bool:
    if word_list[i].lowercase_token in AUXILIARY_VERBS:
        sentence_start = beginning_of_sentence(word_list, i)
        return sentence_start == i or word_list[sentence_start].tag in INTERROGATIVES


def adjust_word_order(word_list: List[WordListItem], i: int, speech_mode: bool) -> int:
    """
    Adjust word order for subject-auxiliary inversion in questions.

    This function implements rule 101, which handles subject-auxiliary inversion
    typically found in questions. It moves auxiliary verbs to the appropriate
    position before the main verb or end of the sentence in interrogative contexts.

    Args:
        word_list (List[WordListItem]): The list of words to process.
        i (int): The current index in the word list.
        speech_mode (bool): Whether the text is in speech mode (unused in this function).

    Returns:
        int: The current index, which remains unchanged in this function.

    Note:
        This function modifies the word_list in-place, potentially inserting new
        items and modifying existing ones.
    """
    word = word_list[i]

    # 101
    # Subject-Aux inversion
    # If the current word is an Aux, and:
    #   1. It's the first word of the sentence, or
    #   2. The sentence begins with an interrogative,
    # then move the current word rightward to put it:
    #   - In front of the first verb, or
    #   - At the end of the sentence.
    # Note: In some cases this may move a word too far right,
    # but the effect on proposition counting is benign.
    # 101
    # Subject-Aux inversion
    # If the current word is an Aux,
    # and the current word is the first word of the sentence
    # or the sentence begins with an interrogative,
    # move the current word rightward to put it in front
    # of the first verb, or the end of the sentence.
    # In some cases this will move a word too far to the right,
    # but the effect on proposition counting is benign.
    if _should_move_auxiliary_verb(word_list, i):
        # find out where to move to
        target_position = i + 1
        while target_position < len(word_list):
            if (
                word_list[target_position].tag == SENTENCE_END
                or word_list[target_position].tag in VERBS
            ):
                break
            target_position += 1

        if target_position > i + 1:
            word_list.insert(
                target_position, WordListItem(word.token, word.tag, True, True, 101)
            )
            # mark the old item as to be ignored
            word.tag = ""
            word.is_proposition = False
            word.is_word = False
            word.token += "/moved"

    return i


def identify_potential_propositions(
    word_list: List[WordListItem], i: int, speech_mode: bool
) -> int:
    """
    Identify potential propositions and apply specific rules to adjust their status.

    This function applies various rules to identify and adjust the proposition status
    of words based on their context, tags, and specific patterns in the text.

    Args:
        word_list (List[WordListItem]): The list of WordListItem objects to process.
        i (int): The current index in the word list.
        speech_mode (bool): Whether the text is in speech mode (unused in this function).

    Returns:
        int: The current index, which remains unchanged in this function.

    Rules applied:
        200: Mark words with tags in DEFAULT_PROPOSITIONS as propositions.
        201: Mark articles ("the", "an", "a") as non-propositions.
        203: Handle correlating conjunctions (e.g., "either...or").
        204: Treat "and then" and "or else" as single propositions.
        206: "To" is not a proposition when it's the last word in a sentence.
        207: Modal verbs are propositions when they're the last word in a sentence.
        210: Cardinal numbers are propositions only if followed by a noun within 5 words.
        211-212: Handle negative polarity items (e.g., "not...unless", "not...any").
        213: "Going to" is not a proposition when immediately preceding a verb.
        214: "If ... then" is treated as a single conjunction.
        225: "each other" is treated as a pronoun.
        230: "how come" and "how many" are treated as single propositions.

    Note:
        This function modifies the word_list in-place, updating the proposition status
        and rule numbers of individual WordListItem objects.
    """
    word = word_list[i]
    previous = word_list[i - 1]
    two_words_back = word_list[i - 2]

    # 200
    if word.tag in DEFAULT_PROPOSITIONS:
        word.is_proposition = True
        word.rule_number = 200

    # 201
    if word.lowercase_token in ["the", "an", "a"]:
        word.is_proposition = False
        word.rule_number = 201

    # We get better agreement with Turner & Greene without this rule.
    # 202
    # An attributive noun (such as 'lion' in 'lion tamer') is a proposition
    # (like an adjective).
    # if self.contains(Noun, b[i].tag) and b[i - 1].tag == "NN":
    #     b[i - 1].isprop = True
    #     b[i - 1].rulenumber = 202

    # 203
    # The first word in a correlating conjunction such as
    # "either...or", "neither...nor", "both...and"
    # is not a proposition. The second word is tagged CC;
    # the first word may have been tagged CC or DT.
    if word.tag == "CC" and not word.lowercase_token in CORRELATING_CONJUNCTIONS:
        target_item = search_backwards(
            word_list, i, lambda w: w.lowercase_token in CORRELATING_CONJUNCTIONS
        )
        if target_item is not None:
            target_item.is_proposition = False
            target_item.rule_number = 203

    # 204
    # "And then" and "or else" are each a single proposition
    if (previous.lowercase_token == "and" and word.lowercase_token == "then") or (
        previous.lowercase_token == "or" and word.lowercase_token == "else"
    ):
        word.is_proposition = False
        word.rule_number = 204

    # 206
    # "To" is not a proposition when it is last word in sentence.
    if word.tag == SENTENCE_END and previous.tag == "TO":
        previous.is_proposition = False
        previous.rule_number = 206

    # 207
    # Modal is a proposition when it is last word in sentence.
    if word.tag == SENTENCE_END and previous.tag == "MD":
        previous.is_proposition = True
        previous.rule_number = 207

    # 210
    # Cardinal number is a proposition only if there is a noun
    # within 5 words after it (not crossing a sentence boundary).
    # This is so "in 3 parts" is 2 props but "in 1941" is only one.
    if word.tag == "CD":
        word.is_proposition = False
        word.rule_number = 210
        # This rule looks forward up to 5 words, but not past
        # an end-of-sentence marker or the end of the WordList
        for j in range(i + 1, min(len(word_list), i + MAX_LOOKAHEAD + 1)):
            next_word = word_list[j]
            if next_word.tag == SENTENCE_END:
                break
            if next_word.tag in NOUNS:
                word.is_proposition = True
                break

    # 211
    # 'Not...unless' and similar pairs count as one proposition
    # (the second word is the one counted).
    if word.lowercase_token in NEGATIVE_POLARITY_2:
        target_item = search_backwards(word_list, i, lambda w: w.tag == "NOT")
        if target_item is not None:
            target_item.is_proposition = False
            target_item.rule_number = 211

    # 212
    # 'Not...any' and similar pairs count as one proposition
    # (the first word is the one counted).
    if word.lowercase_token in NEGATIVE_POLARITY_1:
        target_item = search_backwards(word_list, i, lambda w: w.tag == "NOT")
        if target_item is not None:
            word.is_proposition = False
            word.rule_number = 212

    # 213
    # "Going to" is not a proposition when immediately preceding a verb.
    if (
        word.tag in VERBS
        and previous.lowercase_token == "to"
        and two_words_back.lowercase_token == "going"
    ):
        previous.is_proposition = False
        previous.rule_number = 213
        two_words_back.is_proposition = False
        two_words_back.rule_number = 213

    # 214
    # "If ... then" is 1 conjunction, not two.
    # Actually checking for "if ... then (word)"
    # because "then" as last word of sentence is more likely to be adverb.
    if word.is_word and previous.lowercase_token == "then":
        target_item = search_backwards(
            word_list, i, lambda w: w.lowercase_token == "if"
        )
        if target_item is not None:
            previous.is_proposition = False
            previous.rule_number = 214

    # 225
    # "each other" is a pronoun (to be tagged as PRP PRP).
    if word.lowercase_token == "other" and previous.lowercase_token == "each":
        word.tag = previous.tag = "PRP"
        word.is_proposition = previous.is_proposition = False
        word.rule_number = previous.rule_number = 225

    # 230
    # "how come" and "how many" are each 1 proposition, not two.
    if (word.lowercase_token in ["come", "many"]) and (
        previous.lowercase_token == "how"
    ):
        word.is_proposition = False
        word.tag = previous.tag
        word.rule_number = 230

    return i


def handle_linking_verbs(
    word_list: List[WordListItem], i: int, speech_mode: bool
) -> int:
    """
    Handle rules related to linking verbs and their interactions with other parts of speech.

    This function applies several rules to determine whether linking verbs and related words
    should be counted as propositions based on their context.

    Args:
        word_list (List[WordListItem]): The list of words to process.
        i (int): The current index in the word list.
        speech_mode (bool): Whether the text is in speech mode (unused in this function).

    Returns:
        int: The current index, which remains unchanged in this function.

    Rules applied:
        301: Linking verb is not a proposition if followed by an adjective or adverb.
        302: "Be" is not a proposition when followed by a preposition.
        310: Linking verb + Adverb + {PDT, DT} is counted as 2 propositions.
        311: Adjectives following causative linking verbs are not counted as propositions.

    Note:
        This function modifies the word_list in-place, updating the proposition status
        and rule numbers of individual WordListItem objects.
    """
    # 301
    # Linking verb is not a proposition if followed by adj. or adv.
    # (Apparently, adverbs are frequent tagging mistakes for adjectives.)
    word = word_list[i]
    previous = word_list[i - 1]
    two_words_back = word_list[i - 2]

    if (
        word.tag in ADJECTIVES or word.tag in ADVERBS
    ) and previous.lowercase_token in LINKING_VERBS:
        previous.is_proposition = False
        previous.rule_number = 301

    # 302
    # "Be" is not a proposition when followed by a preposition.
    if word.tag == "IN" and previous.lowercase_token in BE:
        previous.is_proposition = False
        previous.rule_number = 302

    # 310
    # Linking verb + Adverb + { PDT, DT } is 2 propositions
    # (e.g., "he is now the president").
    # (Would otherwise be undercounted because of rule 201).
    if word.tag in ["DT", "PDT"]:
        if (
            previous.tag in ADVERBS
            and word_list[i - 2].lowercase_token in LINKING_VERBS
        ):
            previous.is_proposition = True
            previous.rule_number = 310
            two_words_back.is_proposition = True
            two_words_back.rule_number = 310

    # 311: Causative linking verbs
    # 'make it better' and similar phrases don't count the adjective as a new proposition
    if word.tag in ADJECTIVES:
        target_item = search_backwards(
            word_list, i, lambda w: w.lowercase_token in CAUSATIVE_LINKING_VERBS
        )
        if target_item is not None:
            word.is_proposition = False
            word.rule_number = 311

    return i


def handle_auxiliary_verbs(
    word_list: List[WordListItem], i: int, speech_mode: bool
) -> int:
    """
    Handle rules related to auxiliary verbs and their interactions with other parts of speech.

    This function applies several rules to determine whether auxiliary verbs and related words
    should be counted as propositions based on their context.

    Args:
        word_list (List[WordListItem]): The list of words to process.
        i (int): The current index in the word list.
        speech_mode (bool): Whether the text is in speech mode (unused in this function).

    Returns:
        int: The current index, which remains unchanged in this function.

    Rules applied:
        401: Auxiliary verb + "not" is counted as one proposition, not two.
        402: Auxiliary verb + Verb is counted as one proposition, not two.
        405: Auxiliary verb + NOT + Verb or Auxiliary verb + Adverb + Verb
             is counted as two propositions (NOT/Adverb and Verb).

    Note:
        This function modifies the word_list in-place, updating the proposition status
        and rule numbers of individual WordListItem objects.
    """
    word = word_list[i]
    previous = word_list[i - 1]
    two_words_back = word_list[i - 2]

    # Rule group 400 - Auxiliary verbs are not propositions
    # Note that Verb is a set of tags but Aux is a set of tokens.
    # Note also that Verb includes all Aux.

    # 401
    # Aux not is one proposition, not two
    if word.lowercase_token == "not" and previous.lowercase_token in AUXILIARY_VERBS:
        previous.is_proposition = False
        previous.rule_number = 401

    # 402
    # Aux Verb is one proposition, not two
    if word.tag in VERBS and previous.lowercase_token in AUXILIARY_VERBS:
        previous.is_proposition = False
        previous.rule_number = 402

    # 405
    # Aux NOT Verb          (NOT and the second Verb are propositions)
    # Also Aux Adverb Verb  (e.g., "had always sung", "would rather go")
    if (
        word.tag in VERBS
        and ((previous.tag == "NOT") or previous.tag in ADVERBS)
        and two_words_back.lowercase_token in AUXILIARY_VERBS
    ):
        two_words_back.is_proposition = False
        two_words_back.rule_number = 405

    return i


def handle_constructions_involving_to(
    word_list: List[WordListItem], i: int, speech_mode: bool
) -> int:
    """
    Handle rules related to constructions involving 'to' and adjust proposition counts accordingly.

    This function applies specific rules to handle constructions involving 'to' and related words,
    determining whether they should be counted as separate propositions based on their context.

    Args:
        word_list (List[WordListItem]): The list of words to process.
        i (int): The current index in the word list.
        speech_mode (bool): Whether the text is in speech mode (unused in this function).

    Returns:
        int: The current index, which remains unchanged in this function.

    Rules applied:
        510: 'TO VB' is counted as one proposition, not two.
        511: In 'for ... TO VB' constructions, 'for' is not counted as a proposition.

    Note:
        This function modifies the word_list in-place, updating the proposition status
        and rule numbers of individual WordListItem objects.
    """
    # Rule group 500 - Constructions involving 'to'
    word = word_list[i]
    previous = word_list[i - 1]

    # 510
    # TO VB is one proposition, not two
    if word.tag == "VB" and previous.tag == "TO":
        previous.is_proposition = False
        previous.rule_number = 510

    # 511
    # "for ... TO VB": "for" is not a proposition
    if word.tag == "VB" and previous.tag == "TO":
        # Search back up to 10 words, but not across a sentence end.
        target_item = search_backwards(
            word_list, i, lambda w: w.lowercase_token == "for"
        )
        if target_item is not None:
            target_item.is_proposition = False
            target_item.rule_number = 511

    # 512
    # "From" and "to" form a single proposition with
    # preceding "go", "come", or their synonyms.
    # (We get better agreement with Turner & Greene without this rule.)
    # if (
    #       ( (b[i].token == "to") or (b[i].token == "from") )
    #     and
    #       (Contains(ComeGo, b[i - 1].token) or Contains(ComeGo, b[i - 2].token))
    #    ):
    #   b[i].isprop = False
    #   b[i].rulenumber = 512

    return i


def handle_fillers(word_list: List[WordListItem], i: int, speech_mode: bool) -> int:
    """
    Handle filler words and phrases in speech mode.

    This function applies rules to identify and process filler words and phrases
    that are common in spoken language. It adjusts the proposition status and
    word count for these fillers.

    Args:
        word_list (List[WordListItem]): The list of words to process.
        i (int): The current index in the word list.
        speech_mode (bool): Whether the text is in speech mode.

    Returns:
        int: The updated index after processing.

    Rules applied:
        610: Marks entire sentences consisting only of filler words as non-propositions.
        632: Identifies "like" as a filler when not preceded by a form of "be".
        634: Treats "you know" as a single filler word.

    Note:
        This function only applies rules when in speech mode. It modifies the
        word_list in-place, updating tags, proposition status, and word counts
        for identified fillers.
    """
    if not speech_mode:
        return i

    # Rule group 600 - Fillers
    word = word_list[i]
    previous = word_list[i - 1]

    # 610
    # A sentence consisting entirely of probable filler words is propositionless
    if word.tag == SENTENCE_END:
        bos = beginning_of_sentence(word_list, i)
        k = 0
        for j in range(bos, i):
            if word_list[j].tag != "UH" and word_list[j].lowercase_token not in FILLER:
                k += 1

        if k == 0:
            for j in range(bos, i):
                word_list[j].tag = ""
                word_list[j].is_proposition = False
                word_list[j].rule_number = 610

    # 632
    # In speech mode, "like" is a filler when not immediately preceded by a form of "be".
    if word.lowercase_token == "like" and previous.lowercase_token not in BE:
        word.tag = ""
        word.is_proposition = False
        word.rule_number = 632

    # 634
    # In speech mode, "you know" is a filler and counts as one word, not two.
    if i > 0 and previous.lowercase_token == "you" and word.lowercase_token == "know":
        i -= 1
        word = word_list[i]
        previous = word_list[i - 1]
        two_words_back = word_list[i - 2]
        del word_list[i + 1]
        # reset data for the current item
        word.token = "you_know"
        word.tag = ""
        word.is_proposition = False
        word.is_word = True
        word.rule_number = 634

    return i


def apply_idea_counting_rules(
    word_list: List[WordListItem], speech_mode: bool = False
) -> None:
    """
    This loop iterates through the WordList and may add and remove items.

    The rules look back toward the beginning from the current word; that is,
    the rule is triggered by the last word in the pattern that it is looking for.
    There are guaranteed to be 10 null items at the beginning of the WordList,
    so rules do not have to worry about going past the beginning of the list.

    Most rules look at the output of prior rules; rule 200 is a good example
    of this. The program could be speeded up by identifying rules that do *not*
    feed a subsequent rule, and putting a "continue" statement in them, as in
    rule 000.

    When an addition or deletion to the WordList is to be made, it must take
    place AFTER the current location (e.g., when looking at b[i] you can add
    or delete at i+1 but not at i-1), to prevent renumbering. Rules 003 and 004
    contain examples of stepping backward and deleting forward.

    A deletion removes the item from the word count as well as the idea count.
    Accordingly, items should only be deleted if they've been moved or should not be counted as words.
    """
    i = 0
    while i < len(word_list):
        word = word_list[i]

        if word.token == "":
            i += 1
            continue

        rule_functions: List[Callable[[List[WordListItem], int, bool], int]] = [
            identify_words_and_adjust_tags,
            adjust_word_order,
            identify_potential_propositions,
            handle_linking_verbs,
            handle_auxiliary_verbs,
            handle_constructions_involving_to,
            handle_fillers,
        ]

        for rule_function in rule_functions:
            i = rule_function(word_list, i, speech_mode)

        i += 1
