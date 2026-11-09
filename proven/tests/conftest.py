"""The product's own runtime guard, used on its own test suite.

Every Proven test runs with the network switched off by `proven.netguard` — the
same code the server installs at start-up — so a test that tried to reach a
provider would fail rather than spend money. The Claude extractor is tested
against a fake client; its network check is monkeypatched where a test needs it.
"""
from proven import netguard

netguard.install()
