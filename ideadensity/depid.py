from typing import Callable, List, Optional, Set, Tuple

import spacy

PROPOSITION_DEPENDENCIES = frozenset(
    [
        "advcl",
        "advmod",
        "amod",
        "appos",
        "cc",
        "csubj",
        "csubjpass",
        "det",
        "neg",
        "npadvmod",
        "nsubj",
        "nsubjpass",
        "nummod",
        "poss",
        "predet",
        "preconj",
        "prep",
        "quantmod",
        "tmod",
        "vmod",
    ]
)
EXCLUDED_DETERMINERS = frozenset(["a", "an", "the"])
EXCLUDED_NSUBJ = frozenset(["it", "this"])

_nlp = None


def get_nlp() -> spacy.language.Language:
    """
    Load and return the spaCy English language model.

    Returns:
        spacy.language.Language: The loaded spaCy English language model.
    """
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise OSError(
                "The 'en_core_web_sm' model is not installed. Please install it using: `python -m spacy download en_core_web_sm`."
            )
    return _nlp


def filter_i_you_subject(sent: spacy.tokens.Span) -> bool:
    """
    Check if the sentence contains 'I' or 'you' as the subject of the main verb.

    This function is a sentence filter used by (Sirts et al., 2017) in their DEPID algorithm.

    It was added by Sirts et al. to achieve better performance on DementiaBank interviews.

    It returns False if the sentence contains 'I' or 'you' as the subject of the root verb,
    and True otherwise.

    Args:
        sent (spacy.tokens.Span): A spaCy sentence span to analyze.

    Returns:
        bool: False if 'I' or 'you' is the subject of the main verb, True otherwise.
    """
    for token in sent:
        if (
            token.text.lower() in ["i", "you"]
            and token.dep_ == "nsubj"
            and token.head.dep_ == "ROOT"
        ):
            return False
    return True


def filter_excluded_determiners(token: spacy.tokens.Token) -> bool:
    """
    Check if a token is an excluded determiner.

    This function is a token filter used by (Sirts et al., 2017) in their DEPID algorithm.
    It returns False if the token is a determiner ('det') and is in the list of excluded determiners,
    and True otherwise.

    Args:
        token (spacy.tokens.Token): A spaCy token to analyze.

    Returns:
        bool: False if the token is an excluded determiner, True otherwise.
    """
    if token.dep_ == "det" and token.text.lower() in EXCLUDED_DETERMINERS:
        return False
    return True


def filter_cc(token: spacy.tokens.Token) -> bool:
    """
    Check if a token is an excluded coordinating conjunction.

    (Sirts et al., 2017) exclude cc dependencies from the proposition list in their DEPID algorithm.

    It was added by Sirts et al. to achieve better performance on DementiaBank interviews.

    It returns False if the token is a coordinating conjunction ('cc'),
    and True otherwise.

    Args:
        token (spacy.tokens.Token): A spaCy token to analyze.

    Returns:
        bool: False if the token is a coordinating conjunction, True otherwise.
    """
    if token.dep_ == "cc":
        return False
    return True


def filter_excluded_nsubjs(token: spacy.tokens.Token) -> bool:
    """
    Check if a token is an excluded nominal subject.

    This function is a token filter used by (Sirts et al., 2017 in their DEPID algorithm.
    It returns False if the token is a nominal subject ('nsubj') and is in the list of excluded subjects,
    and True otherwise.

    Args:
        token (spacy.tokens.Token): A spaCy token to analyze.

    Returns:
        bool: False if the token is an excluded nominal subject, True otherwise.
    """
    if token.dep_ == "nsubj" and token.text.lower() in EXCLUDED_NSUBJ:
        return False
    return True


SENTENCE_FILTERS = [filter_i_you_subject]
TOKEN_FILTERS = [filter_excluded_determiners, filter_excluded_nsubjs, filter_cc]


def _get_token_filters(
    use_excluded_determiner_filter: bool = True,
    use_excluded_nsubj_filter: bool = True,
    use_excluded_cc_filter: bool = False,
    custom_token_filters: Optional[List[Callable[[spacy.tokens.Token], bool]]] = None,
) -> List[Callable[[spacy.tokens.Token], bool]]:
    token_filters = []
    if use_excluded_determiner_filter:
        token_filters.append(filter_excluded_determiners)
    if use_excluded_nsubj_filter:
        token_filters.append(filter_excluded_nsubjs)
    if use_excluded_cc_filter:
        token_filters.append(filter_cc)
    if custom_token_filters:
        token_filters.extend(custom_token_filters)
    return token_filters


def _get_sentence_filters(
    use_i_you_subject_filter: bool = False,
    custom_sentence_filters: Optional[List[Callable[[spacy.tokens.Span], bool]]] = None,
) -> List[Callable[[spacy.tokens.Span], bool]]:
    sentence_filters = []
    if use_i_you_subject_filter:
        sentence_filters.append(filter_i_you_subject)
    if custom_sentence_filters:
        sentence_filters.extend(custom_sentence_filters)

    return sentence_filters


def _filter_sentences(
    doc: spacy.tokens.Doc,
    sentence_filters: List[Callable[[spacy.tokens.Span], bool]],
    nlp: spacy.language.Language,
) -> spacy.tokens.Doc:
    if sentence_filters:
        filtered_sents = [
            sent
            for sent in doc.sents
            if all(filter_func(sent) for filter_func in sentence_filters)
        ]
        doc = spacy.tokens.Doc(
            doc.vocab, words=[token.text for sent in filtered_sents for token in sent]
        )
        doc = nlp(doc)

    return doc


def depid(
    text: str,
    is_depid_r: bool = False,
    use_excluded_determiner_filter: bool = True,
    use_excluded_nsubj_filter: bool = True,
    use_excluded_cc_filter: bool = False,
    use_i_you_subject_filter: bool = False,
    custom_sentence_filters: Optional[List[Callable[[spacy.tokens.Span], bool]]] = None,
    custom_token_filters: Optional[List[Callable[[spacy.tokens.Token], bool]]] = None,
) -> (
    Tuple[float, int, List[Tuple[str, str, str]]]
    | Tuple[float, int, Set[Tuple[str, str, str]]]
):
    """
    Calculate the Dependency-based Idea Density (DEPID) for a given text.

    This function implements the DEPID (Dependency-based Propositional Idea Density) algorithm
    as described by (Sirts et al., 2017)

    It processes the input text, applies various filters, and calculates the
    proposition density based on dependency relations.

    Args:
        text (str): The input text to analyze.
        is_depid_r (bool): If True, returns unique dependencies as a set. Otherwise, returns all dependencies as a list.
            Default is False.
        use_excluded_determiner_filter (bool): If True, applies the excluded determiner filter.
            Default is True. Condition used by default by Sirts et al.
        use_excluded_nsubj_filter (bool): If True, applies the excluded nominal subject filter.
            Default is True. Condition used by default by Sirts et al.
        use_excluded_cc_filter (bool): If True, applies the excluded coordinating conjunction filter.
            Default is False. Sirts et al. added this condition to achieve better performance
            on DementiaBank interviews.
        use_i_you_subject_filter (bool): If True, applies the 'I' and 'you' subject filter.
            Default is False. Sirts et al. added this condition to achieve better performance
            on DementiaBank interviews.
        custom_sentence_filters (Optional[List[Callable[[spacy.tokens.Span], bool]]]): Custom sentence-level filters to apply.
            Default is None.
        custom_token_filters (Optional[List[Callable[[spacy.tokens.Token], bool]]]): Custom token-level filters to apply.
            Default is None.

    Returns:
        Tuple[float, int, List[Tuple[str, str, str]]] | Tuple[float, int, Set[Tuple[str, str, str]]]:
            A tuple containing:
            - The calculated DEPID (proposition density)
            - The total word count
            - A list or set of tuples, each representing a dependency (token, dependency type, head)

    Note:
        The function applies various filters to exclude certain types of words and
        sentences based on the DEPID algorithm specifications. It then calculates
        the density as the ratio of identified propositions to the total word count.
    """

    nlp = get_nlp()
    doc = nlp(text)

    word_count = len(
        [token for token in doc if not token.is_punct and not token.is_space]
    )

    sentence_filters = _get_sentence_filters(
        use_i_you_subject_filter=use_i_you_subject_filter,
        custom_sentence_filters=custom_sentence_filters,
    )
    token_filters = _get_token_filters(
        use_excluded_determiner_filter=use_excluded_determiner_filter,
        use_excluded_nsubj_filter=use_excluded_nsubj_filter,
        use_excluded_cc_filter=use_excluded_cc_filter,
        custom_token_filters=custom_token_filters,
    )

    doc = _filter_sentences(doc, sentence_filters, nlp)
    dependencies = _get_final_dependencies(is_depid_r, doc, token_filters)
    density = (len(dependencies) / word_count) if word_count > 0 else 0.0

    return density, word_count, dependencies


def _get_final_dependencies(is_depid_r, doc, token_filters):
    if is_depid_r:
        dependencies = set()
    else:
        dependencies = []

    for token in doc:
        if not token.dep_ in PROPOSITION_DEPENDENCIES:
            continue
        if token_filters and any(
            not filter_func(token) for filter_func in token_filters
        ):
            continue
        if is_depid_r:
            dependencies.add((token.text, token.dep_, token.head.text))
        else:
            dependencies.append((token.text, token.dep_, token.head.text))

    return dependencies
