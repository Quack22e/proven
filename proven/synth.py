"""Synthetic month-end closes with known causes — and explanations with known defects.

WHY SYNTHETIC, AND WHAT IT CAN AND CANNOT SHOW

Real ledgers with labelled variance explanations do not exist in public, and a
real one is a company's most sensitive data. So the generator builds a company,
injects the events that move its accounts, and then writes the commentary —
correctly, or with exactly one defect of a declared family. Because the cause is
injected, the right answer is known by construction rather than by re-running
the checker, which is the method Aptio used for its mutation studies: the
expected outcome follows from the *shape of the edit*.

What it shows: whether the checks catch each defect family, cite the right
transactions, and leave correct explanations alone. What it cannot show: how
real commentary is phrased, or how real memos are worded. The generator, the
lexicon and the checker share an author, and that is the ceiling on every number
this module produces. See the README's limits section.

FAMILIES

    control_exact            correct, figure written precisely           must PASS
    control_rounded          correct, figure rounded ("~$90K")           must PASS
    control_hedged           "primarily due to X", X is ~60-70%          must PASS
    control_cross_account    the cause also legitimately touches another
                             account, booked by that account's vendor    must PASS
    control_distractor       a second, correct claim in the same memo    must PASS
    wrong_amount             stated change off by 35-80%                 must FAIL
    wrong_direction          "rose" for a fall, or the reverse           must FAIL
    wrong_cause              blames a cause whose spend did not move     must FAIL
    partial                  "because of X", X is only 35-60%            must FAIL
    unsupported_cause        blames a cause absent from the ledger       must not PASS
    misclassified_overlooked an expense of the cause is booked to the
                             wrong account; the memo explains the books  must not PASS
    misclassified_economic   the same, but the memo states the true
                             (economic) amount, so it disagrees          must not PASS

SPLITS

`seed % 5 == 0` is the test split; everything else is train. Family assignment
cycles with the seed, so both splits are balanced. A policy trained on `train`
never sees a `test` scenario.
"""
from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field

from proven.ledger import Account, Ledger, Transaction

PERIODS = ("2026-08", "2026-09", "2026-10")   # history, prior, current
HISTORY, PRIOR, CURRENT = PERIODS


@dataclass(frozen=True)
class Recurring:
    vendor: str
    base: float
    memo: str


@dataclass(frozen=True)
class Event:
    key: str
    vendor: str
    memos: tuple[str, ...]
    phrases: tuple[str, ...]
    low: int
    high: int
    cross_memo: str        # wording of a legitimate charge for the same cause, in another account


@dataclass(frozen=True)
class AccountSpec:
    name: str
    aliases: tuple[str, ...]
    narrative: tuple[str, ...]    # aliases a writer would open a sentence with
    recurring: tuple[Recurring, ...]
    events: tuple[Event, Event]   # events[0] is billed by a recurring vendor


WORLD: tuple[AccountSpec, ...] = (
    AccountSpec(
        "Legal & Professional Fees",
        ("legal", "legal costs", "legal fees", "legal spend", "legal expenses",
         "professional fees", "legal and professional fees"),
        ("Legal costs", "Legal fees", "Legal spend", "Professional fees"),
        (Recurring("Harbor & Vale LLP", 6000, "General corporate retainer"),
         Recurring("Ledgerline CPAs", 3500, "Monthly close support")),
        (Event("financing", "Harbor & Vale LLP",
               ("Series B financing — closing documents", "Series B — investor rights agreements"),
               ("our funding round", "the Series B financing", "the fundraise"),
               40000, 95000, "Series B financing — data room fees"),
         Event("litigation", "Meridian Legal Group",
               ("Patent dispute — settlement payment", "Patent dispute — deposition preparation"),
               ("the patent litigation", "the patent dispute settlement"),
               30000, 80000, "Patent dispute — expert witness travel")),
    ),
    AccountSpec(
        "Marketing & Advertising",
        ("marketing", "marketing spend", "marketing costs", "advertising", "ad spend"),
        ("Marketing spend", "Marketing", "Advertising", "Ad spend"),
        (Recurring("Google Ads", 9000, "Search ads — always on"),
         Recurring("Brightwave Agency", 5000, "Content retainer")),
        (Event("campaign", "Google Ads",
               ("Q4 launch campaign — paid search", "Launch campaign — display"),
               ("the product launch campaign", "the Q4 launch campaign"),
               20000, 55000, "Launch campaign — landing page hosting"),
         Event("conference", "Expo Collective",
               ("DevSummit 2026 — booth sponsorship", "DevSummit 2026 — booth build"),
               ("the DevSummit sponsorship", "our DevSummit booth"),
               20000, 50000, "DevSummit 2026 — team travel")),
    ),
    AccountSpec(
        "Cloud Hosting",
        ("cloud", "cloud hosting", "hosting", "cloud costs", "cloud spend", "infrastructure"),
        ("Cloud hosting", "Cloud costs", "Cloud spend", "Hosting"),
        (Recurring("Amazon Web Services", 22000, "Production hosting"),
         Recurring("Datadog", 3000, "Monitoring")),
        (Event("migration", "Amazon Web Services",
               ("EC2 — data migration load testing", "S3 — migration storage"),
               ("the data migration", "higher AWS usage during the migration"),
               12000, 40000, "Data migration — contract support"),
         Event("training", "Tensorgrid",
               ("GPU cluster — model training run", "GPU cluster — reserved capacity"),
               ("the model training run", "GPU capacity for model training"),
               15000, 45000, "Model training — dataset labeling")),
    ),
    AccountSpec(
        "Software & Subscriptions",
        ("software", "software spend", "software costs", "subscriptions",
         "software subscriptions", "software & subscriptions"),
        ("Software spend", "Software costs", "Subscriptions"),
        (Recurring("Slack", 2400, "Workspace — monthly"),
         Recurring("GitHub", 2100, "Team plan — monthly"),
         Recurring("Figma", 1500, "Design team — monthly"),
         Recurring("Salesforce", 3200, "CRM — monthly")),
        (Event("renewal", "Salesforce",
               ("Annual renewal — 2027 CRM licenses", "Annual renewal — service add-on"),
               ("annual license renewals", "this year's license renewals"),
               15000, 45000, "Renewal — implementation support"),
         Event("compliance", "Trustline",
               ("SOC 2 compliance platform — annual plan", "SOC 2 — auditor portal"),
               ("the SOC 2 compliance platform", "our new compliance tooling"),
               12000, 35000, "SOC 2 audit — fieldwork")),
    ),
    AccountSpec(
        "Travel & Entertainment",
        ("travel", "travel costs", "travel spend", "travel and entertainment", "t&e"),
        ("Travel", "Travel costs", "Travel spend"),
        (Recurring("Delta Air Lines", 4200, "Flights"),
         Recurring("Marriott", 3100, "Hotel stays"),
         Recurring("Uber", 900, "Ground transport")),
        (Event("roadshow", "Delta Air Lines",
               ("Customer roadshow — flights", "Customer roadshow — change fees"),
               ("the customer roadshow", "customer visits on the East Coast roadshow"),
               10000, 30000, "Customer roadshow — event tickets"),
         Event("offsite", "Lakeside Lodge",
               ("Company offsite — venue and lodging", "Company offsite — catering"),
               ("the company offsite", "our team offsite"),
               15000, 45000, "Company offsite — facilitator")),
    ),
    AccountSpec(
        "Rent & Facilities",
        ("rent", "facilities", "rent and facilities", "facilities costs", "occupancy"),
        ("Rent and facilities", "Facilities costs", "Occupancy"),
        (Recurring("Bayview Properties", 18000, "HQ rent"),
         Recurring("Brightline Janitorial", 1200, "Cleaning service")),
        (Event("lease", "Bayview Properties",
               ("Lease — Austin office, first month", "Lease — Austin office, security deposit"),
               ("the new Austin office lease", "our Austin office expansion"),
               15000, 40000, "Austin office — lease legal review"),
         Event("buildout", "Northfield Builders",
               ("Fourth-floor build-out — progress billing", "Build-out — electrical"),
               ("the fourth-floor build-out", "the build-out of the fourth floor"),
               15000, 40000, "Build-out — permit filing support")),
    ),
    AccountSpec(
        "Contractors",
        ("contractors", "contractor costs", "contractor spend", "contract labor"),
        ("Contractor costs", "Contractor spend", "Contract labor"),
        (Recurring("Deel", 12000, "Monthly payroll — international team"),
         Recurring("Upwork", 2000, "Freelance support")),
        (Event("mobile", "Deel",
               ("Contract engineers — mobile app build", "Contract engineers — mobile QA"),
               ("contract engineers for the mobile app", "the mobile app build"),
               15000, 40000, "Mobile app — device farm"),
         Event("redesign", "Kestrel Design Studio",
               ("Website redesign — phase 2", "Website redesign — illustrations"),
               ("the website redesign", "design work on the website"),
               15000, 40000, "Website redesign — hosting")),
    ),
    AccountSpec(
        "Recruiting",
        ("recruiting", "recruiting costs", "recruiting fees", "hiring costs"),
        ("Recruiting costs", "Recruiting fees", "Hiring costs"),
        (Recurring("Greenhouse", 1800, "ATS subscription"),
         Recurring("LinkedIn", 2500, "Talent platform — monthly"),
         Recurring("Talentbridge Partners", 3000, "Retainer — monthly")),
        (Event("search", "Talentbridge Partners",
               ("VP Engineering search — placement fee", "VP Engineering search — second installment"),
               ("the VP Engineering search", "the VP Engineering placement"),
               20000, 60000, "VP Engineering search — candidate travel"),
         Event("campus", "Campus Connect",
               ("University career fairs — booth fees", "University career fairs — swag"),
               ("university recruiting events", "the fall career fairs"),
               10000, 30000, "University career fairs — sponsorship ads")),
    ),
    AccountSpec(
        "Insurance",
        ("insurance", "insurance costs", "insurance premiums"),
        ("Insurance", "Insurance costs", "Insurance premiums"),
        (Recurring("Atlas Mutual", 2600, "General liability — monthly"),
         Recurring("Shieldpoint", 900, "Workers comp — monthly")),
        (Event("d_and_o", "Atlas Mutual",
               ("D&O policy — annual premium", "D&O policy — broker fee"),
               ("the D&O policy renewal", "renewing our D&O policy"),
               10000, 30000, "D&O policy — legal review"),
         Event("cyber", "Bastion Underwriters",
               ("Cyber coverage — first-year premium", "Cyber coverage — binder fee"),
               ("the new cyber coverage", "cyber insurance coverage"),
               8000, 25000, "Cyber coverage — security assessment")),
    ),
)

CHART = tuple(Account(spec.name, spec.aliases) for spec in WORLD)

#: Ways of describing each cause that share no searchable word with the
#: lexicon or with that cause's own memos. Written before they were measured,
#: and kept whatever they scored: they exist to show how the checker degrades
#: when a writer phrases a cause in words it has never seen. Overlap with a
#: *different* cause's memos is allowed — that is a real-world hazard, and
#: measuring it is the point.
HELDOUT: dict[str, tuple[str, ...]] = {
    "financing": ("the capital we closed in October", "bringing on new shareholders"),
    "litigation": ("the IP case with a competitor", "resolving the claim against us"),
    "campaign": ("the October go-to-market push", "our biggest promotion of the year"),
    "conference": ("our presence at the developer event", "the industry meetup we attended"),
    "migration": ("moving our databases to the new region", "the cutover to the new stack"),
    "training": ("the large experiment our ML team ran", "scaling up research workloads"),
    "renewal": ("the yearly vendor true-ups", "re-upping our sales tools"),
    "compliance": ("getting audit-ready for enterprise customers", "the security attestation"),
    "roadshow": ("meeting buyers in New York and Boston", "the sales team's trips to prospects"),
    "offsite": ("the all-hands trip to the lake", "the planning week away"),
    "lease": ("taking more space in Texas", "the second location"),
    "buildout": ("the construction work upstairs", "making the new space usable"),
    "mobile": ("the iOS project", "outsourced phone development"),
    "redesign": ("refreshing our marketing site", "the new brand look online"),
    "search": ("the senior leadership hire", "filling the senior technical leader role"),
    "campus": ("college hiring season", "student pipeline building"),
    "d_and_o": ("board coverage", "protecting our directors"),
    "cyber": ("the new breach policy", "protection against hacks"),
}
ENTITIES = ("Arcadia Labs", "Brightfield Health", "Cobalt Freight", "Driftwood Analytics",
            "Ember Payments", "Fathom Bio", "Granite Data", "Halcyon Energy", "Ironwood Systems",
            "Juniper Logistics")


@dataclass(frozen=True)
class Family:
    name: str
    kind: str                       # "control" | "defect"
    requirement: str                # "PASS" | "FAIL" | "NOT_PASS"
    expected_codes: tuple[str, ...]


FAMILIES: tuple[Family, ...] = (
    Family("control_exact", "control", "PASS", ()),
    Family("control_rounded", "control", "PASS", ()),
    Family("control_hedged", "control", "PASS", ()),
    Family("control_cross_account", "control", "PASS", ()),
    Family("wrong_amount", "defect", "FAIL", ("WRONG_AMOUNT",)),
    Family("wrong_direction", "defect", "FAIL", ("WRONG_DIRECTION",)),
    Family("wrong_cause", "defect", "FAIL", ("WRONG_CAUSE",)),
    Family("partial", "defect", "FAIL", ("PARTIAL_EXPLANATION",)),
    Family("unsupported_cause", "defect", "NOT_PASS", ("REASON_NOT_FOUND",)),
    Family("misclassified_overlooked", "defect", "NOT_PASS", ("POSSIBLE_MISCLASSIFICATION",)),
    Family("misclassified_economic", "defect", "NOT_PASS",
           ("WRONG_AMOUNT", "POSSIBLE_MISCLASSIFICATION")),
)
DISTRACTOR = Family("control_distractor", "control", "PASS", ())
FAMILY_BY_NAME = {f.name: f for f in FAMILIES + (DISTRACTOR,)}


@dataclass
class Label:
    quote: str
    family: str
    kind: str
    requirement: str
    expected_codes: list[str]
    culprits: list[str]
    account: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Scenario:
    scenario_id: str
    seed: int
    split: str
    family: str
    ledger: Ledger
    explanation: str
    labels: list[Label] = field(default_factory=list)

    def to_dict(self, include_labels: bool = True) -> dict:
        data = {"scenario_id": self.scenario_id, "seed": self.seed, "split": self.split,
                "family": self.family, "ledger": self.ledger.to_dict(),
                "explanation": self.explanation}
        if include_labels:
            data["labels"] = [label.to_dict() for label in self.labels]
        return data


def split_of(seed: int) -> str:
    return "test" if seed % 5 == 0 else "train"


def family_of(seed: int) -> Family:
    # Cycling on seed // 5 keeps both splits balanced across families.
    return FAMILIES[(seed // 5) % len(FAMILIES)]


def seeds(split: str, n: int, start: int = 0) -> list[int]:
    out, seed = [], start
    while len(out) < n:
        if split_of(seed) == split:
            out.append(seed)
        seed += 1
    return out


# ── construction helpers ─────────────────────────────────────────────────

class _Builder:
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.rows: list[tuple[str, str, str, str, float]] = []   # date, account, vendor, memo, amount

    def add(self, period: str, account: str, vendor: str, memo: str, amount: float) -> int:
        day = self.rng.randint(2, 27)
        self.rows.append((f"{period}-{day:02d}", account, vendor, memo, round(amount, 2)))
        return len(self.rows) - 1

    def build(self, entity: str) -> tuple[Ledger, list[str]]:
        order = sorted(range(len(self.rows)), key=lambda i: (self.rows[i][0], i))
        ids = [""] * len(self.rows)
        transactions = []
        for n, index in enumerate(order):
            ids[index] = f"TX-{1001 + n}"
            date, account, vendor, memo, amount = self.rows[index]
            transactions.append(Transaction(ids[index], date, account, vendor, memo, amount))
        return (Ledger(entity, PRIOR, CURRENT, CHART, tuple(transactions)), ids)


def _baseline(builder: _Builder) -> None:
    for spec in WORLD:
        for item in spec.recurring:
            for period in PERIODS:
                builder.add(period, spec.name, item.vendor, item.memo,
                            item.base * builder.rng.uniform(0.95, 1.05))


def _inject(builder: _Builder, account: str, event: Event, total: float, period: str,
            split_parts: int = 2) -> list[int]:
    parts = [total] if split_parts == 1 else [total * 0.55, total * 0.45]
    return [builder.add(period, account, event.vendor, event.memos[i % len(event.memos)], amount)
            for i, amount in enumerate(parts)]


def money_text(value: float, rng: random.Random, mode: str) -> str:
    """How a writer states an amount: precisely, or rounded the way commentary is."""
    value = abs(value)
    if mode == "exact":
        return f"${value / 1000:.1f}K" if value >= 10000 else f"${value:,.0f}"
    for step in (10000, 5000, 1000, 500):
        rounded = round(value / step) * step
        if rounded and abs(rounded - value) / value <= 0.04:
            text = f"${rounded / 1000:g}K"
            return ("approximately " if rng.random() < 0.3 else "") + text
    return f"${value / 1000:.1f}K"


_UP = ("rose", "increased", "grew", "climbed")
_DOWN = ("fell", "decreased", "declined", "dropped")
_FULL = ("due to", "driven by", "because of", "as a result of", "reflecting")
_MAJORITY = ("primarily due to", "mainly driven by", "largely because of")


def sentence(rng: random.Random, alias: str, direction: int, amount: str, phrase: str,
             strength: str = "full", percent: str | None = None, prior_period: bool = False) -> str:
    verb = rng.choice(_UP if direction > 0 else _DOWN)
    connector = rng.choice(_MAJORITY if strength == "majority" else _FULL)
    reason = f"{phrase} in September" if prior_period else phrase
    form = rng.randrange(3)
    if form == 0:
        return f"{alias} {verb} {amount} month over month, {connector} {reason}."
    if form == 1 and percent:
        return f"{alias} {verb} {amount} ({percent}) compared with September, {connector} {reason}."
    noun = "increase" if direction > 0 else "decrease"
    article = "An" if amount.startswith("approximately") else "The"
    return f"{article} {amount} {noun} in {alias.lower()} was {connector} {reason}."


# ── the generator ────────────────────────────────────────────────────────

def generate(seed: int, family: Family | None = None, phrasing: str = "seen") -> Scenario:
    rng = random.Random(seed)
    family = family or family_of(seed)
    builder = _Builder(rng)
    _baseline(builder)

    order = list(range(len(WORLD)))
    rng.shuffle(order)
    target = WORLD[order[0]]
    spare = [WORLD[i] for i in order[1:]]
    other = spare.pop()                     # receives a misbooking or a cross-account charge
    distractors = spare[:rng.choice((1, 2))]

    event, decoy = target.events
    if family.name not in ("misclassified_overlooked", "misclassified_economic") and rng.random() < 0.5:
        event, decoy = decoy, event
    decrease = family.name in ("control_exact", "control_rounded", "wrong_amount",
                               "wrong_direction", "wrong_cause", "unsupported_cause") \
        and rng.random() < 0.25
    period = PRIOR if decrease else CURRENT

    culprits: list[int] = []
    cited, strength = event, "full"
    total = rng.uniform(event.low, event.high)

    if family.name in ("control_hedged", "partial"):
        share = rng.uniform(0.6, 0.72) if family.name == "control_hedged" else rng.uniform(0.38, 0.58)
        combined = rng.uniform(max(event.low, decoy.low) * 1.4, max(event.high, decoy.high) * 1.2)
        _inject(builder, target.name, event, combined * share, CURRENT)
        other_ids = _inject(builder, target.name, decoy, combined * (1 - share), CURRENT)
        strength = "majority" if family.name == "control_hedged" else "full"
        culprits = other_ids if family.name == "partial" else []
    elif family.name in ("misclassified_overlooked", "misclassified_economic"):
        ids = _inject(builder, target.name, event, total, CURRENT)
        moved = ids[1]
        date, _account, vendor, memo, amount = builder.rows[moved]
        builder.rows[moved] = (date, other.name, vendor, memo, round(total * rng.uniform(0.38, 0.5), 2))
        builder.rows[ids[0]] = builder.rows[ids[0]][:4] + (round(total - builder.rows[moved][4], 2),)
        culprits = [moved]
    else:
        culprits = _inject(builder, target.name, event, total, period)
        if family.name == "wrong_cause":
            steady = rng.uniform(4000, 9000)
            builder.add(PRIOR, target.name, decoy.vendor, decoy.memos[0], steady)
            builder.add(CURRENT, target.name, decoy.vendor, decoy.memos[1],
                        steady * rng.uniform(0.98, 1.02))
            cited = decoy
        elif family.name == "unsupported_cause":
            cited = decoy
        elif family.name == "control_cross_account":
            vendor = rng.choice(other.recurring)
            builder.add(CURRENT, other.name, vendor.vendor, event.cross_memo, rng.uniform(1500, 4000))

    distractor_events = []
    for spec in distractors:
        chosen = rng.choice(spec.events)
        _inject(builder, spec.name, chosen, rng.uniform(chosen.low, chosen.high), CURRENT)
        distractor_events.append((spec, chosen))

    ledger, ids = builder.build(rng.choice(ENTITIES))
    culprit_ids = [ids[i] for i in culprits]

    # ── the commentary ──
    change = ledger.variance(target.name).change
    direction = 1 if change >= 0 else -1
    stated_change = change
    mode = "exact" if family.name in ("control_exact", "control_cross_account") else "rounded"
    if family.name == "wrong_amount":
        factor = rng.uniform(1.35, 1.8) if rng.random() < 0.5 else rng.uniform(0.45, 0.65)
        stated_change = change * factor
    elif family.name == "wrong_direction":
        direction = -direction
    elif family.name == "misclassified_economic":
        stated_change = change + ledger.txn(culprit_ids[0]).amount
    pct = ledger.variance(target.name).change_pct
    percent = f"{abs(pct):.0f}%" if pct is not None and family.name != "wrong_amount" else None
    phrase = rng.choice(HELDOUT[cited.key] if phrasing == "heldout" else cited.phrases)
    alias = rng.choice(target.narrative)
    main = sentence(rng, alias, direction, money_text(stated_change, rng, mode), phrase,
                    strength=strength, percent=percent, prior_period=(period == PRIOR))

    labels = [Label(main, family.name, family.kind, family.requirement,
                    list(family.expected_codes),
                    culprit_ids if family.kind == "defect" else [], target.name)]
    lines = [main]
    for spec, chosen in distractor_events:
        dchange = ledger.variance(spec.name).change
        text = sentence(rng, rng.choice(spec.narrative), 1 if dchange >= 0 else -1,
                        money_text(dchange, rng, rng.choice(("exact", "rounded"))),
                        rng.choice(HELDOUT[chosen.key] if phrasing == "heldout" else chosen.phrases))
        labels.append(Label(text, DISTRACTOR.name, DISTRACTOR.kind, DISTRACTOR.requirement,
                            [], [], spec.name))
        lines.append(text)
    rng.shuffle(lines)
    explanation = "\n".join(
        [f"October 2026 close — operating expense commentary for {ledger.entity}."]
        + lines + ["All other accounts were broadly in line with September."])

    return Scenario(f"syn-{seed:05d}", seed, split_of(seed), family.name, ledger,
                    explanation, labels)


def generate_split(split: str, n: int, phrasing: str = "seen") -> list[Scenario]:
    return [generate(seed, phrasing=phrasing) for seed in seeds(split, n)]
