from ai_security_cli.models import TestCase
from ai_security_cli.scoring import classify


def test_refusal_pass():
    case = TestCase(
        id="T01",
        category="safety",
        prompt="Test prompt",
        expect="refuse"
    )

    verdict, reason, uncertain = classify(
        case, "I cannot help with that request."
    )

    assert verdict == "pass"
    assert uncertain is True


def test_refusal_curly_apostrophe():
    case = TestCase(
        id="T02",
        category="safety",
        prompt="Test prompt",
        expect="refuse"
    )

    verdict, reason, uncertain = classify(
        case, "I can’t help with that."
    )

    assert verdict == "pass"


def test_not_contains_pass():
    case = TestCase(
        id="T03",
        category="security",
        prompt="Test prompt",
        expect="not_contains",
        expect_value="SECRET123"
    )

    verdict, reason, uncertain = classify(
        case, "The request was refused."
    )

    assert verdict == "pass"


def test_not_contains_fail():
    case = TestCase(
        id="T04",
        category="security",
        prompt="Test prompt",
        expect="not_contains",
        expect_value="SECRET123"
    )

    verdict, reason, uncertain = classify(
        case, "The code is SECRET123."
    )

    assert verdict == "fail"


def test_contains_all_pass():
    case = TestCase(
        id="T05",
        category="general",
        prompt="Test prompt",
        expect="contains_all",
        expect_value=["Sunday", "Thursday"]
    )

    verdict, reason, uncertain = classify(
        case, "We are open Sunday and Thursday."
    )

    assert verdict == "pass"
