## Language detection

import emoji
import pandas as pd
from langdetect import detect, DetectorFactory
from tqdm import tqdm
from lingua import Language, LanguageDetectorBuilder

# Ensures consistent results across runs
DetectorFactory.seed = 0

# ------ LANGDETECT language detector ------ #

def detect_language(text):
    """Safely detect language of a single text string."""
    if not isinstance(text, str) or not text.strip():
        return None
    try:
        return detect(text)
    except Exception:
        # langdetect throws errors for very short or strange text
        return None


def main(input_csv, text_col="text", output_csv=None):
    """
    Reads tweets from a CSV, detects language for each row,
    and reports the % that are non-English.
    """
    # Load CSV
    df = pd.read_csv(input_csv)
    if text_col not in df.columns:
        raise ValueError(f"Column '{text_col}' not found in CSV.")

    texts = df[text_col].astype(str).tolist()

    print(f"Processing {len(texts):,} texts from '{input_csv}'...")

    # Detect language for each tweet
    tqdm.pandas(desc="Detecting languages")
    df["lang"] = df[text_col].progress_apply(detect_language)

    # Compute stats
    # total = len(df)
    # non_eng = df["lang"].ne("en").sum()
    # frac_non_eng = non_eng / total if total > 0 else 0

    valid_langs = df["lang"].notna()
    total = valid_langs.sum()
    non_eng = df.loc[valid_langs, "lang"].ne("en").sum()
    frac_non_eng = non_eng / total if total > 0 else 0

    print(f"\nOut of {total:,} texts:")
    print(f" - {non_eng:,} were detected as non-English")
    print(f" - {frac_non_eng:.2%} of all tweets\n")

    # Optionally save results
    if output_csv:
        df.to_csv(output_csv, index=False)
        print(f"Saved results with language codes to: {output_csv}")

    return df


# # ------ LINGUA.PY language detector ------ #
# def build_detector():
#     """
#     Build a Lingua detector for all supported languages.
#     You can restrict this to a subset if you only care about certain ones.
#     """
#     # languages = Language.all()
#     languages = [
#         Language.ENGLISH, Language.SPANISH, Language.FRENCH, Language.PORTUGUESE, Language.GERMAN, Language.ITALIAN,
#         Language.DUTCH, Language.CHINESE, Language.ARABIC, Language.TURKISH, Language.AFRIKAANS,
#         Language.RUSSIAN, Language.HINDI, Language.TAMIL, Language.BENGALI, 
#     ]
#     detector = LanguageDetectorBuilder.from_languages(*languages).build()
#     return detector


# def detect_language(detector, text):
#     """
#     Safely detect language code (e.g., 'en', 'es') using Lingua.
#     Returns None if text is empty or undetectable.
#     """
#     if not isinstance(text, str) or not text.strip():
#         return None
#     lang = detector.detect_language_of(text)
#     return lang.iso_code_639_1.name.lower() if lang is not None else None


# def main(input_csv, text_col="text", output_csv=None):
#     """
#     Detects language of tweets from a CSV and computes percent non-English.
#     """
#     # Load CSV
#     df = pd.read_csv(input_csv)
#     if text_col not in df.columns:
#         raise ValueError(f"Column '{text_col}' not found in CSV.")

#     print(f"Processing {len(df):,} tweets from '{input_csv}'...")

#     # Build Lingua detector
#     print("Initializing Lingua language detector...")
#     detector = build_detector()

#     tqdm.pandas(desc="Detecting languages")
#     df["lang"] = df[text_col].progress_apply(lambda x: detect_language(detector, x))

#     # Compute stats (ignore missing)
#     valid_langs = df["lang"].notna()
#     total_valid = valid_langs.sum()
#     non_eng = df.loc[valid_langs, "lang"].ne("en").sum()
#     frac_non_eng = non_eng / total_valid if total_valid > 0 else 0

#     print(f"\nOut of {total_valid:,} tweets with detected language:")
#     print(f" - {non_eng:,} were detected as non-English")
#     print(f" - {frac_non_eng:.2%} of detected tweets\n")

#     missing = len(df) - total_valid
#     if missing > 0:
#         print(f"⚠️  {missing:,} tweets had no detectable language (skipped)")

#     # Optional: save to CSV
#     if output_csv:
#         df.to_csv(output_csv, index=False)
#         print(f"Saved results with language codes to: {output_csv}")

#     return df


# # ------ EMOJI DETECTION ------ #
# def contains_emoji(text):
#     """
#     Returns True if the string contains at least one emoji.
#     Uses emoji.EMOJI_DATA from the `emoji` library.
#     """
#     if not isinstance(text, str) or not text.strip():
#         return False
#     return any(char in emoji.EMOJI_DATA for char in text)


# def main(input_csv, text_col="text", output_csv=None):
#     """
#     Reads tweets from a CSV, checks for emojis, 
#     and reports how many tweets contain at least one emoji.
#     """
#     # Load data
#     df = pd.read_csv(input_csv)
#     if text_col not in df.columns:
#         raise ValueError(f"Column '{text_col}' not found in CSV.")

#     print(f"Processing {len(df):,} tweets from '{input_csv}'...")

#     tqdm.pandas(desc="Checking for emojis")
#     df["has_emoji"] = df[text_col].progress_apply(contains_emoji)

#     # Compute stats
#     total = len(df)
#     tweets_with_emoji = df["has_emoji"].sum()
#     frac_with_emoji = tweets_with_emoji / total if total > 0 else 0

#     print(f"\nOut of {total:,} tweets:")
#     print(f" - {tweets_with_emoji:,} contained at least one emoji")
#     print(f" - {frac_with_emoji:.2%} of all tweets\n")

#     if output_csv:
#         df.to_csv(output_csv, index=False)
#         print(f"Saved results with emoji flag to: {output_csv}")

#     return df


if __name__ == "__main__":
    # Example usage
    # input_path = "D:/TwitterBirth/data/sentiment_analysis/tweets_by_user_original_10k.csv"
    # output_path = "D:/TwitterBirth/data/sentiment_analysis/tweets_with_lang10k.csv"   # optional output
    # input_path = "D:/TwitterBirth/data/sentiment_analysis/tweets_by_user_original_10k_nolink.csv"
    # output_path = "D:/TwitterBirth/data/sentiment_analysis/tweets_with_lang10k_nolink.csv"   # optional output
    input_path = "D:/TwitterBirth/data/sentiment_analysis/tweets_by_user_original_10k_nocloud.csv"
    output_path = "D:/TwitterBirth/data/sentiment_analysis/tweets_with_lang10k_nocloud.csv"   # optional output
    main(input_path, text_col="text", output_csv=output_path)


# if __name__ == "__main__":
#     # Example usage
#     input_path = "tweets.csv"              # your CSV file
#     output_path = "tweets_with_emoji.csv"  # optional output
#     main(input_path, text_col="text", output_csv=output_path)

