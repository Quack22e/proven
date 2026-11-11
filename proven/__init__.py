"""Proven — checks the reasons in a variance explanation against the ledger.

Built for one accounting workflow: the month-end variance commentary ("Legal
costs rose $90K because of our funding round") that finance teams — and
increasingly AI copilots — write during the close.

The architecture in one line:

    UNTRUSTED (may propose)              |   DETERMINISTIC (decides)
    explanation -> extractor -> proposal +-> admit -> bind -> check -> PASS/FAIL/REVIEW

An extractor — rule-based by default, optionally a language model — *proposes*
claims. Nothing it says is believed: `claims.admit()` re-reads every proposal
against the explanation's own text, and every verdict is computed by
re-executing arithmetic over the company's transactions. A model never produces
a verdict, and a PASS never rests on anything only a model asserted.

The package imports nothing outside the standard library and itself;
`proven/tests/test_isolation.py` asserts that by AST.
"""

__version__ = "0.1.0"
