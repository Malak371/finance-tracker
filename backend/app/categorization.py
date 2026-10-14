"""Automatic categorisation of imported transactions.

The pipeline for one description, first match wins:

1. The user's own keyword rules ("TESCO" -> Groceries). Explicit, so they always win.
2. History: the same merchant (same words, ignoring numbers) that the user categorised before.
3. A Naive Bayes classifier trained only on this user's expenses whose category *they* chose
   (typed by hand, corrected later, or taken from their bank's export). It only answers when it
   is confident, and it never learns from its own guesses, which would reinforce mistakes.
4. Built-in keywords for well-known merchants, as a generic fallback.
5. Otherwise "Uncategorized".
"""

import math
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

UNCATEGORIZED = "Uncategorized"

# Category sources that reflect a decision by the user, i.e. valid training labels.
USER_LABELLED_SOURCES = ("manual", "file")

MIN_TRAINING_EXAMPLES = 10
MIN_CONFIDENCE = 0.7

# Words that appear in many bank descriptions and say nothing about the merchant.
STOPWORDS = {
    "pos", "purchase", "card", "debit", "credit", "payment", "visa", "mastercard", "contactless",
    "online", "www", "com", "ltd", "inc", "llc", "the", "and", "ref", "transaction", "txn",
}  # fmt: skip

DEFAULT_RULES = {
    # Groceries
    "aldi": "Groceries", "lidl": "Groceries", "tesco": "Groceries", "sainsbury": "Groceries",
    "whole foods": "Groceries", "trader joe": "Groceries", "safeway": "Groceries", "kroger": "Groceries",
    "costco": "Groceries", "walmart": "Groceries", "carrefour": "Groceries", "grocery": "Groceries",
    "supermarket": "Groceries",
    # Dining
    "starbucks": "Dining", "mcdonald": "Dining", "burger king": "Dining", "subway": "Dining",
    "chipotle": "Dining", "pret": "Dining", "uber eats": "Dining", "doordash": "Dining",
    "deliveroo": "Dining", "grubhub": "Dining", "restaurant": "Dining", "cafe": "Dining", "coffee": "Dining",
    "pizza": "Dining",
    # Transport
    "uber": "Transport", "lyft": "Transport", "bolt": "Transport", "shell": "Transport",
    "chevron": "Transport", "exxon": "Transport", "bp": "Transport", "parking": "Transport",
    "metro": "Transport", "transit": "Transport", "tfl": "Transport", "railway": "Transport",
    # Shopping
    "amazon": "Shopping", "amzn": "Shopping", "ebay": "Shopping", "target": "Shopping",
    "ikea": "Shopping", "zara": "Shopping", "h&m": "Shopping", "best buy": "Shopping",
    # Subscriptions
    "netflix": "Subscriptions", "spotify": "Subscriptions", "disney plus": "Subscriptions",
    "hulu": "Subscriptions", "apple com bill": "Subscriptions", "youtube premium": "Subscriptions",
    "icloud": "Subscriptions", "github": "Subscriptions", "adobe": "Subscriptions",
    # Utilities
    "electric": "Utilities", "water": "Utilities", "gas bill": "Utilities", "verizon": "Utilities",
    "at&t": "Utilities", "comcast": "Utilities", "vodafone": "Utilities", "internet": "Utilities",
    # Health
    "pharmacy": "Health", "cvs": "Health", "walgreens": "Health", "boots": "Health", "gym": "Health",
    "dental": "Health", "clinic": "Health",
    # Entertainment
    "cinema": "Entertainment", "steam": "Entertainment", "playstation": "Entertainment",
    "ticketmaster": "Entertainment", "theatre": "Entertainment",
    # Travel
    "airbnb": "Travel", "booking com": "Travel", "hotel": "Travel", "airline": "Travel",
    "ryanair": "Travel", "easyjet": "Travel", "expedia": "Travel",
}  # fmt: skip


def normalize(text: str) -> str:
    """Lowercase and reduce to words separated by single spaces ("AMZN Mktp*US" -> "amzn mktp us")."""
    return " ".join(re.findall(r"[a-z0-9&]+", text.lower()))


def tokenize(text: str) -> list[str]:
    return [t for t in normalize(text).split() if len(t) > 1 and not t.isdigit() and t not in STOPWORDS]


def match_keyword(description: str, rules: dict[str, str]) -> str | None:
    """Category of the longest keyword found as whole words in the description."""
    padded = f" {normalize(description)} "
    matches = [keyword for keyword in rules if f" {keyword} " in padded]
    return rules[max(matches, key=len)] if matches else None


class NaiveBayesClassifier:
    """Multinomial Naive Bayes over description words, with Laplace smoothing."""

    def __init__(self, examples: Iterable[tuple[str, str]]):
        self.class_counts: Counter[str] = Counter()
        self.word_counts: dict[str, Counter[str]] = defaultdict(Counter)
        for description, category in examples:
            tokens = tokenize(description)
            if tokens:
                self.class_counts[category] += 1
                self.word_counts[category].update(tokens)
        self.vocabulary = {word for counts in self.word_counts.values() for word in counts}
        self.total_words = {c: sum(counts.values()) for c, counts in self.word_counts.items()}
        self.examples = sum(self.class_counts.values())

    @property
    def ready(self) -> bool:
        return self.examples >= MIN_TRAINING_EXAMPLES and len(self.class_counts) >= 2

    def predict(self, description: str) -> tuple[str, float] | None:
        """Most likely category and its probability, or None if there's nothing to go on."""
        tokens = [t for t in tokenize(description) if t in self.vocabulary]
        if not self.ready or not tokens:
            return None
        vocabulary_size = len(self.vocabulary)
        scores = {}
        for category, count in self.class_counts.items():
            score = math.log(count / self.examples)
            for token in tokens:
                score += math.log(
                    (self.word_counts[category][token] + 1) / (self.total_words[category] + vocabulary_size)
                )
            scores[category] = score
        best = max(scores, key=scores.get)
        # Softmax over log-scores, shifted by the max for numerical stability.
        total = sum(math.exp(s - scores[best]) for s in scores.values())
        return best, 1 / total


@dataclass
class Suggestion:
    category: str
    source: str  # "rule", "history", "model", "default" or "none"
    confidence: float | None = None


def merchant_key(description: str) -> str:
    return " ".join(tokenize(description))


class Categorizer:
    def __init__(self, user_rules: dict[str, str], training_examples: Iterable[tuple[str, str]]):
        """`training_examples` are (description, category) pairs labelled by the user, oldest first."""
        examples = list(training_examples)
        self.user_rules = user_rules
        # Later examples overwrite earlier ones, so the user's most recent choice wins.
        self.history = {merchant_key(d): c for d, c in examples if merchant_key(d)}
        self.model = NaiveBayesClassifier(examples)

    def suggest(self, description: str) -> Suggestion:
        if category := match_keyword(description, self.user_rules):
            return Suggestion(category, "rule")
        if category := self.history.get(merchant_key(description)):
            return Suggestion(category, "history")
        if prediction := self.model.predict(description):
            category, confidence = prediction
            if confidence >= MIN_CONFIDENCE:
                return Suggestion(category, "model", round(confidence, 2))
        if category := match_keyword(description, DEFAULT_RULES):
            return Suggestion(category, "default")
        return Suggestion(UNCATEGORIZED, "none")
