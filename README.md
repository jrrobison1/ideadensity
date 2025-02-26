# ideadensity
[![PyPI - Version](https://img.shields.io/pypi/v/ideadensity?link=https%3A%2F%2Fpypi.org%2Fproject%2Fideadensity%2F)](https://pypi.org/project/ideadensity/) [![Unit Tests](https://github.com/jrrobison1/pycpidr/actions/workflows/unit_tests.yml/badge.svg)](https://github.com/jrrobison1/pycpidr/actions/workflows/unit_tests.yml) [![Downloads](https://static.pepy.tech/badge/pycpidr)](https://pepy.tech/project/pycpidr)

Python library for computing propositional idea density.

## Table of Contents
- [Introduction](#introduction)
- [What is Idea Density?](#what-is-idea-density)
- [Installation](#installation)
- [Usage](#usage)
  - [CPIDR](#cpidr)
  - [DEPID](#depid)
- [Requirements](#requirements)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [CPIDR Parity with CPIDR 3.2](#cpidr-parity-with-cpidr-32)
- [References](#references)
- [Citing](#citing)
- [Contributing](#contributing)
- [License](#license)

## Introduction

ideadensity is a Python library which determines the propositional idea density of an English text automatically. This project aims to make this functionality more accessible to Python developers and researchers. ideadensity provides two ways of computing idea density:
- CPIDR. The CPIDR implementation in ideadensity is a direct port of the Computerized Propositional Idea Density Rater (CPIDR) 3.2 (Brown et al., 2008) [1]
- DEPID. This library implements the DEPID algorithm described by Sirts et al (2017) [2]

Here's a quick example of how to use ideadensity:
```python
from ideadensity import cpidr, depid

text = "The quick brown fox jumps over the lazy dog."
cpidr_word_count, proposition_count, cpidr_density, word_list = cpidr(text)
depid_density, depid_word_count, dependencies = depid(text)

print(f"CPIDR density: {cpidr_density:.3f}")
print(f"DEPID density: {depid_density:.3f}")
```

## What is Idea Density?

Idea density, also known as propositional density, is a measure of the amount of information conveyed relative to the number of words used. It's calculated by dividing the number of expressed propositions by the number of words. This metric has applications in various fields, including linguistics, cognitive science, and healthcare research.

## Installation

### Using pip
1. Install the package
```bash
pip install ideadensity
```

2. Download the required spaCy model:
```bash
python -m spacy download en_core_web_sm
```

### Using poetry

```bash
poetry add ideadensity
python -m spacy download en_core_web_sm
```

**Note**: This package currently supports Python 3.10-3.12 due to dependency constraints with spaCy and its dependencies. If you're using Python 3.13, you'll need to create a virtual environment with a compatible Python version.


## Usage
### CPIDR
Here's a simple example of how to use CPIDR:

```python
from ideadensity import cpidr

text = "The quick brown fox jumps over the lazy dog."
word_count, proposition_count, density, word_list = cpidr(text)

print(f"Word count: {word_count}")
print(f"Proposition count: {proposition_count}")
print(f"Idea density: {density:.3f}")

# Analyzing speech
speech_text = "Um, you know, I think that, like, the weather is nice today."
word_count, proposition_count, density, word_list = cpidr(speech_text, speech_mode=True)

print(f"Speech mode - Idea density: {density:.3f}")

# Detailed word analysis
for word in word_list.items:
    if word.is_word:
        print(f"Token: {word.token}, Tag: {word.tag}, Is proposition: {word.is_proposition}")
```

#### Speech Mode

ideadensity CPIDR mode supports a speech mode that handles common speech patterns and fillers differently from written text. When analyzing transcripts or spoken language, use the `speech_mode=True` parameter for more accurate results.

### DEPID
Here's an example of how to use the DEPID functionality:
```python
from ideadensity import depid

text = "The quick brown fox jumps over the lazy dog."
density, word_count, dependencies = depid(text)
print(f"Word count: {word_count}")
print(f"Idea density: {density:.3f}")
print("Dependencies:")
for dep in dependencies:
    print(f"Token: {dep[0]}, Dependency: {dep[1]}, Head: {dep[2]}")
```

#### DEPID-R
DEPID-R counts _distinct_ dependencies.

```python
from ideadensity import depid

text = "This is a test of DEPID-R. This is a test of DEPID-R"
density, word_count, dependencies = depid(text, is_depid_r=True)

print(f"DEPID-R idea density: {density:.3f}")
```

#### Using custom filters
ideadensity DEPID mode supports custom filtering of sentences and tokens. By default, ideadensity uses filters described by (Sirts et al., 2017):
- Sentence filter. 
    - Filter out sentences with "I" or "You" as the subject of the sentence (i.e. if the "I" or "You" token dependency is "nsubj" and it's head dependency is the root). 
    - Note: Sirts et al (2017) also filters out vague sentences using SpeciTeller. That is a filter which ideadensity does not yet implement.
- Token filters:
    - Filter out "det" dependencies if the token is "a", "an" or "the".
    - Filter out "nsubj" dependencies if the token is "it" or "this".
    - Filter out all "cc" dependencies.

This example demonstrates how to apply your own custom filters to modify the analysis. The `sentence_filters` and `token_filters` parameters allow you to customize the DEPID algorithm to suit your specific needs.
```python
def custom_sentence_filter(sent):
    return len(sent) > 3
def custom_token_filter(token):
    return token.pos_ != "DET"
text_with_filters = "I run. The quick brown fox jumps over the lazy dog."
density, word_count, dependencies = depid(text_with_filters,
sentence_filters=[custom_sentence_filter],
token_filters=[custom_token_filter])
print(f"\nWith custom filters - Idea density: {density:.3f}")
```


## Requirements

- Python 3.10+
- spaCy 3.7.5+

## Development Setup

To set up the development environment:

1. Clone the repository
2. Install Poetry if you haven't already: `pip install poetry`
3. Install project dependencies: `poetry install`
4. Install the required spaCy model: `poetry run python -m spacy download en_core_web_sm`
5. Activate the virtual environment: `poetry shell`

## Running Tests

To run the tests, use pytest:

```bash
pytest tests/
```

## CPIDR Parity with CPIDR 3.2
Because this port uses spaCy as a part-of-speech tagger instead of the original program's MontyLingua, there is a very slight difference in the reported idea density. This port includes unit tests containing 847 words of text.
ideadensity: 434 propositions. 0.512 idea density
CPIDR 3.2: 436 propositions. 0.515 idea density

For more information about the original CPIDR 3.2, please visit [CASPR's official page](http://ai1.ai.uga.edu/caspr/).

## References
[1] Brown, C., Snodgrass, T., Kemper, S. J., Herman, R., & Covington, M. A. (2008). Automatic measurement of propositional idea density from part-of-speech tagging. Behavior research methods, 40(2), 540-545.

[2] Sirts, K., Piguet, O., & Johnson, M. (2017). Idea density for predicting Alzheimer's disease from transcribed speech. arXiv preprint arXiv:1706.04473.

## Citing
If you use this project in your research, you may cite it as: 

Jason Robison. (2024). *ideadensity* (0.2.0) [Source code]. GitHub. https://github.com/jrrobison1/pycpidr


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please ensure that your code passes all tests and follows the project's coding style.

## License
This project is licensed under the GNU General Public License v2.0. See the [LICENSE](LICENSE) file for details.

ideadensity's CPIDR implementation is a port of the original CPIDR 3.2, which was released under GPL v2. This project maintains the same license to comply with the terms of the original software.
