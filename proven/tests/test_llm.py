"""The Claude extractor, against a fake client: what it sends, and what it may not get away with."""
import json
from types import SimpleNamespace

import pytest

from proven import llm, netguard
from proven.llm import ClaudeExtractor, NetworkDisabled
from proven.report import run
from proven.showcase import EXPLANATION, ledger


class FakeClient:
    def __init__(self, claims, stop_reason="end_turn"):
        self.requests = []
        self._claims, self._stop = claims, stop_reason
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        text = json.dumps({"claims": self._claims})
        return SimpleNamespace(stop_reason=self._stop, content=[SimpleNamespace(type="text", text=text)])


def claim(quote, **fields):
    base = {"quote": quote, "account": "", "direction": "", "change_text": "", "percent_text": "",
            "prior_text": "", "current_text": "", "reason_text": "", "search_terms": []}
    return {**base, **fields}


LEGAL = "Legal costs rose $90K because of our Series B funding round."


@pytest.fixture
def network_on(monkeypatch):
    monkeypatch.setattr(netguard, "network_allowed", lambda: True)


def test_refuses_to_run_with_the_network_off():
    extractor = ClaudeExtractor(client=FakeClient([]))
    with pytest.raises(NetworkDisabled):
        extractor.propose(EXPLANATION, ledger())


def test_sends_only_the_narrative_and_the_chart(network_on):
    client = FakeClient([])
    extractor = ClaudeExtractor(client=client)
    extractor.propose(EXPLANATION, ledger())
    [request] = client.requests
    sent = json.dumps(request)
    for txn in ledger().transactions:
        assert txn.memo not in sent and txn.id not in sent
    assert "Harbor & Vale" not in sent
    assert request["model"] == "claude-opus-5-5" and request["fallbacks"] == "default"
    assert request["output_config"]["format"]["type"] == "json_schema"
    [record] = extractor.transmissions
    assert "transactions" in record["not_sent"] and record["bytes"] > 0


def test_the_output_schema_has_nowhere_to_put_a_verdict():
    fields = set(llm.SCHEMA["properties"]["claims"]["items"]["properties"])
    assert not fields & {"verdict", "status", "severity", "pass", "fail", "correct"}


def test_proposals_cross_the_same_boundary_as_the_rules(network_on):
    client = FakeClient([
        claim(LEGAL, account="Legal & Professional Fees", direction="up", change_text="$90K",
              reason_text="our Series B funding round", search_terms=["closing documents"]),
        claim("Legal costs rose $95K because of the lawsuit.", change_text="$95K"),   # invented
        claim("Contractor costs increased $22K due to the website redesign.",
              change_text="$99K"),                                                   # figure not stated
    ])
    report = run(EXPLANATION, ledger(), extractor=ClaudeExtractor(client=client), network_allowed=True)
    reasons = sorted(r["reason"] for r in report["rejected"])
    assert reasons == ["figure_not_in_quote", "quote_not_in_text"]
    [legal] = report["claims"]
    assert legal["verdict"] == "FAIL"           # decided by the ledger, not the model
    origins = {t["text"]: t["origin"] for t in legal["claim"]["terms"]}
    assert origins["closing documents"] == "model"
    assert report["run"]["network"]["transmissions"][0]["provider"] == "anthropic"


def test_a_refusal_produces_no_proposals(network_on):
    extractor = ClaudeExtractor(client=FakeClient([claim(LEGAL)], stop_reason="refusal"))
    assert extractor.propose(EXPLANATION, ledger()) == []
    assert extractor.transmissions[0]["stop_reason"] == "refusal"


class BrokenClient(FakeClient):
    def _create(self, **kwargs):
        self.requests.append(kwargs)
        return SimpleNamespace(stop_reason="end_turn",
                               content=[SimpleNamespace(type="text", text="not json")])


def test_a_malformed_response_produces_no_proposals(network_on):
    extractor = ClaudeExtractor(client=BrokenClient([]))
    assert extractor.propose(EXPLANATION, ledger()) == []
    assert extractor.transmissions[0]["error"] == "response was not valid JSON"
