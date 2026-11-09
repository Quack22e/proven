"""The generator's own consistency: if these fail, the benchmark measures nothing."""
import pytest

from proven.claims import anchored_terms, term_pattern
from proven.synth import FAMILIES, HELDOUT, WORLD, generate, seeds, split_of
from proven.showcase import ledger as showcase_ledger

LEDGER = showcase_ledger()   # any ledger carrying the chart will do for term derivation


def matches(phrase: str, account: str, text: str) -> bool:
    terms = anchored_terms(phrase, account, LEDGER)
    return any(term_pattern(t.text).search(text.lower()) for t in terms)


@pytest.mark.parametrize("spec", WORLD, ids=lambda s: s.name)
def test_every_phrase_binds_to_every_memo_of_its_own_event(spec):
    for event in spec.events:
        for phrase in event.phrases:
            for memo in event.memos:
                assert matches(phrase, spec.name, f"{event.vendor} {memo}"), (phrase, memo)
            assert matches(phrase, spec.name, event.cross_memo), (phrase, event.cross_memo)


@pytest.mark.parametrize("spec", WORLD, ids=lambda s: s.name)
def test_no_phrase_binds_to_the_other_event_or_to_recurring_spend(spec):
    a, b = spec.events
    for this, other in ((a, b), (b, a)):
        for phrase in this.phrases:
            for memo in other.memos:
                assert not matches(phrase, spec.name, f"{other.vendor} {memo}"), (phrase, memo)
            for item in spec.recurring:
                assert not matches(phrase, spec.name, f"{item.vendor} {item.memo}"), (phrase, item)


@pytest.mark.parametrize("spec", WORLD, ids=lambda s: s.name)
def test_heldout_phrases_share_no_word_with_their_own_event(spec):
    for event in spec.events:
        for phrase in HELDOUT[event.key]:
            for memo in event.memos:
                assert not matches(phrase, spec.name, f"{event.vendor} {memo}"), (phrase, memo)


def test_the_first_event_of_each_account_is_billed_by_a_recurring_vendor():
    for spec in WORLD:
        assert spec.events[0].vendor in {r.vendor for r in spec.recurring}, spec.name


def test_generation_is_deterministic():
    a, b = generate(123), generate(123)
    assert a.explanation == b.explanation and a.ledger.sha256() == b.ledger.sha256()
    assert generate(124).ledger.sha256() != a.ledger.sha256()


def test_splits_are_disjoint_and_balanced():
    test, train = seeds("test", 110), seeds("train", 110)
    assert not set(test) & set(train)
    assert all(split_of(s) == "test" for s in test)
    families = {generate(s).family for s in test[: len(FAMILIES)]}
    assert families == {f.name for f in FAMILIES}


@pytest.mark.parametrize("family", FAMILIES, ids=lambda f: f.name)
def test_labels_are_well_formed(family):
    scenario = generate(7, family)
    target = scenario.labels[0]
    assert target.family == family.name and target.quote in scenario.explanation
    if family.kind == "defect":
        assert target.culprits and all(scenario.ledger.txn(t) for t in target.culprits)
    else:
        assert target.culprits == []
