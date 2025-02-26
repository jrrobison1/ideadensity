from enum import Enum


PUNCTUATION = frozenset({":", ",", "."})
ADJECTIVES = frozenset({"JJ", "JJR", "JJS"})
ADVERBS = frozenset({"RB", "RBR", "RBS", "WRB"})
VERBS = frozenset({"VB", "VBD", "VBG", "VBN", "VBP", "VBZ"})
NOUNS = frozenset({"NN", "NNS", "NNP", "NNPS"})
INTERROGATIVES = frozenset({"WDT", "WP", "WPS", "WRB"})

# All the tags that, by default, are taken to be propositions
DEFAULT_PROPOSITIONS = frozenset(
    {
        "CC",  # coordinating conjunction
        "CD",  # cardinal numeral
        "DT",  # determiner
        "IN",  # preposition/subordinating conj.
        "JJ",
        "JJR",
        "JJS",  # adjective
        "PDT",  # predeterminer
        "POS",  # possessive "'s" (which is not counted as a word)
        "PRP$",  # possessive pronoun
        "PP$",  # possessive pronoun
        "RB",
        "RBR",
        "RBS",  # adverbs
        "TO",  # "to" whether prep. or infinitival
        "VB",
        "VBD",
        "VBG",
        "VBN",
        "VBP",
        "VBZ",  # verbs
        "WDT",
        "WP",
        "WPS",
        "WRB",  # interrogatives/relatives
    }
)

# Words that are often non-propositional fillers.
FILLER = frozenset({"and", "or", "but", "if", "that", "just", "you", "know"})

# All forms of 'be'
BE = frozenset({"am", "is", "are", "was", "were", "being", "been"})

# Common negative contractions that may slip through the tagger, especially
# if accidentally typed without the apostrophe
NT = frozenset(
    {
        "didn't",
        "didnt",
        "don't" "don't",
        "dont",
        "can't",
        "cant",
        "couldn't",
        "couldnt",
        "won't",
        "wont",
        "wouldn't",
        "wouldnt",
    }
)

# 'Come', 'go', and their synonyms form a single proposition with following 'to' or 'from'
COME_GO = frozenset(
    {
        "come",
        "comes",
        "came",
        "coming",
        "return",
        "returns",
        "returned",
        "returning",
        "arrive",
        "arrives",
        "arrived",
        "arriving",
        "go",
        "goes",
        "went",
        "gone",
        "going",
        "depart",
        "departs",
        "departed",
        "departing",
        "emanate",
        "emanates",
        "emanated",
        "emanating",
    }
)

AUXILIARY_VERBS = frozenset(
    {
        "be",
        "am",
        "is",
        "are",
        "was",
        "were",
        "being",
        "been",
        "have",
        "has",
        "had",
        "having",
        "do",
        "does",
        "did",  # "doing" and "done" are not aux forms
        "need",  # "needs" is not an aux
        "dare",  # "dares" is not an aux
        # and we need not include modals here
        # because the tagger does not tag them as verbs.
    }
)

# All forms of all verbs that take an adjective after them
LINKING_VERBS = frozenset(
    {
        # Being
        "be",
        "am",
        "is",
        "are",
        "was",
        "were",
        "been",
        "being",
        # Becoming
        "become",
        "becomes",
        "became",
        "becoming",
        "get",
        "gets",
        "got",
        "gotten",
        "getting",
        # Seeming visually
        "look",
        "looks",
        "looked",
        "looking",
        "seem",
        "seems",
        "seemed",
        "seeming",
        "appear",
        "appears",
        "appeared",
        "appearing",
        # Seeming through other senses
        "sound",
        "sounds",
        "sounded",
        "sounding",
        "feel",
        "feels",
        "felt",
        "feeling",
        "smell",
        "smells",
        "smelled",
        "smelling",
        "taste",
        "tastes",
        "tasted",
        "tasting",
    }
)

# All forms of all verbs that take noun phrase + adjective after them,
# such as "make it better" or "turn it green."
CAUSATIVE_LINKING_VERBS = frozenset(
    {
        "make",
        "makes",
        "made",
        "making",
        "turn",
        "turns",
        "turned",
        "turning",
        "paint",
        "paints",
        "painted",
        "painting",
    }
)

CORRELATING_CONJUNCTIONS = frozenset({"both", "either", "neither"})

# N.B. The following are not all the negative-polarity items of English,
# but only the ones that seem to form 2-word 1-concept idioms.

# Negative-polarity items where the negative, rather than this word,
# counts as the proposition; e.g., "not...yet" = "not".
NEGATIVE_POLARITY_1 = frozenset({"yet", "much", "many", "any", "anymore"})

# Negative-polarity items where this word, rather than the earlier
# negative, counts as the proposition; e.g., "not...unless" = "(n)unless".
NEGATIVE_POLARITY_2 = frozenset({"unless"})  # are there others?

SENTENCE_END = "."


class RuleNumber(Enum):
    SENTENCE_END_MARKER = 1
    ALPHANUMERIC_WORD = 2
    COMBINE_CONSECUTIVE_CARDINALS = 3
    COMBINE_CARDINALS_WITH_SEPARATOR = 4
    REPETITION_A_A = 20
    REPETITION_A_PUNCT_A = 21
    REPETITION_A_B_A = 22
    REPETITION_A_B_PUNCT_A_B = 23
    NEGATION_CONTRACTION = 50
    THAT_THIS_AS_PRONOUN = 54
    SUBJECT_AUX_INVERSION = 101
    DEFAULT_PROPOSITION = 200
    ARTICLE_NOT_PROPOSITION = 201
    CORRELATING_CONJUNCTION = 203
    SINGLE_PROPOSITION = 204
    TO_NOT_PROPOSITION = 206
    MODAL_PROPOSITION = 207
    CARDINAL_NUMBER = 210
    NEGATIVE_POLARITY_2 = 211
    NEGATIVE_POLARITY_1 = 212
    GOING_TO = 213
    IF_THEN = 214
    EACH_OTHER = 225
    HOW_COME_MANY = 230
    LINKING_VERB_NOT_PROPOSITION = 301
    BE_NOT_PROPOSITION = 302
    LINKING_VERB_ADVERB_DT = 310
    CAUSATIVE_LINKING_VERB = 311
    AUX_NOT = 401
    AUX_VERB = 402
    AUX_NOT_VERB_OR_AUX_ADV_VERB = 405
    TO_VB_ONE_PROPOSITION = 510
    FOR_TO_VB_FOR_NOT_PROPOSITION = 511
    SENTENCE_FILLER = 610
    LIKE_FILLER = 632
    YOU_KNOW_FILLER = 634
