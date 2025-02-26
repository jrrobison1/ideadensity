import argparse
from ideadensity.idea_density_rater import rate_text


def main(text, speech_mode):
    _, _, density, word_list = rate_text(text, speech_mode=speech_mode)

    print(f"Density: {density}")
    print("Word list:")
    for word in word_list.items:
        print(
            f"Token: [{word.token}], tag: [{word.tag}], is_word: [{word.is_word}], is_prop: [{word.is_proposition}], rule_number: [{word.rule_number}]"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calculate idea density of a given text."
    )
    parser.add_argument("text", nargs="+", help="The text to analyze")
    parser.add_argument("--speech-mode", action="store_true", help="Enable speech mode")
    args = parser.parse_args()

    text = " ".join(args.text)
    main(text, args.speech_mode)
