from app.categorization import (
    MIN_TRAINING_EXAMPLES,
    Categorizer,
    NaiveBayesClassifier,
    match_keyword,
    normalize,
    tokenize,
)


def test_normalize_and_tokenize():
    assert normalize("AMZN Mktp*US 1234") == "amzn mktp us 1234"
    assert tokenize("POS PURCHASE  Tesco Stores 3021") == ["tesco", "stores"]


def test_keyword_matching_uses_whole_words_and_prefers_the_longest():
    rules = {"uber": "Transport", "uber eats": "Dining", "bp": "Transport"}
    assert match_keyword("UBER *TRIP HELP.UBER.COM", rules) == "Transport"
    assert match_keyword("UBER EATS 8005928996", rules) == "Dining"
    assert match_keyword("BPAY BILLER 123", rules) is None


def _training(n_each=6):
    return [("Tesco Stores 1234", "Groceries")] * n_each + [("Shell Fuel Station", "Car")] * n_each


def test_classifier_needs_enough_examples():
    assert not NaiveBayesClassifier(_training(n_each=2)).ready
    assert NaiveBayesClassifier(_training()).ready
    assert sum(1 for _ in _training()) >= MIN_TRAINING_EXAMPLES


def test_classifier_predicts_from_learned_words():
    model = NaiveBayesClassifier(_training())
    category, confidence = model.predict("TESCO EXPRESS 99")
    assert category == "Groceries"
    assert confidence > 0.9
    assert model.predict("Completely unknown merchant") is None


def test_history_remembers_the_latest_choice_for_a_merchant():
    categorizer = Categorizer({}, [("ZEPHYR BOOKSHOP 001", "Gifts"), ("Zephyr Bookshop 002", "Books")])
    suggestion = categorizer.suggest("ZEPHYR BOOKSHOP 777")
    assert (suggestion.category, suggestion.source) == ("Books", "history")
    assert categorizer.suggest("ZEPHYR TOOLS").source == "none"


def test_pipeline_order_rule_then_model_then_default():
    training = [("Corner Books", "Hobbies")] * 6 + [("Amazon Marketplace books", "Hobbies")] * 6
    training += [("Tesco Stores", "Groceries")] * 6
    categorizer = Categorizer({"netflix": "Fun"}, training)

    # 1. The user's rule beats everything.
    assert (categorizer.suggest("NETFLIX.COM").category, categorizer.suggest("NETFLIX.COM").source) == (
        "Fun",
        "rule",
    )
    # 2. Learned from the user's own labels: they file Amazon under Hobbies, not the default Shopping.
    suggestion = categorizer.suggest("AMAZON MARKETPLACE")
    assert (suggestion.category, suggestion.source) == ("Hobbies", "model")
    # 3. Built-in keywords as a fallback.
    assert categorizer.suggest("STARBUCKS #123").category == "Dining"
    assert categorizer.suggest("STARBUCKS #123").source == "default"
    # 4. Nothing matched.
    assert categorizer.suggest("ZZZ UNKNOWN").source == "none"


def test_low_confidence_predictions_fall_through():
    # "shop" appears equally in both categories, so the model can't tell and shouldn't guess.
    training = [("Shop Alpha", "A")] * 6 + [("Shop Beta", "B")] * 6
    assert Categorizer({}, training).suggest("SHOP").source == "none"
