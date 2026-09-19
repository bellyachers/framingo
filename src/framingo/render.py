"""Two surface forms for one meaning: the variable of charter proposition 3.

F (Framingo): every argument carries its role tag; slot order is shuffled,
so position carries nothing.

W (word order): English-shaped. Core arguments are marked by position alone
(agent before the verb, target after it); peripheral ones by a preposition,
as English does (README, "The precise claim"). Viewpoint is varied with a
passive, which moves the target to the front and the agent behind ``by``.

Both forms share every content token (entities, modifiers, verbs) and the
connectors ``->`` / ``!>``. They differ only in how roles are marked, which
is the variable the proposition names.

Tokens: a dot chain is split into segments with ``.`` as its own token, so
``Red.Apple`` and ``Apple`` share the token ``Apple`` in both forms.
"""

from __future__ import annotations

import random
import re

from .syntax import Concept, Event, Pipeline

PREPOSITIONS = {"tool": "with", "src": "from", "dst": "onto", "loc": "in", "reason": "because"}
PREP_ORDER = ("tool", "src", "dst", "loc", "reason")


def _concept(c: Concept) -> str:
    return ".".join(c.segments)


def _slot(event: Event, key: str) -> Concept | None:
    values = event.get(key)
    return values[0] if values else None


# -- F -----------------------------------------------------------------------


def f_event(event: Event, rng: random.Random | None) -> str:
    slots = [f"{k}:{_concept(v)}" for k, v in sorted(event.slots, key=lambda kv: kv[0])]
    if rng is not None:
        rng.shuffle(slots)
    return " ".join([_concept(event.verb)] + slots)


def f_pipeline(p: Pipeline, rng: random.Random | None = None) -> str:
    out = [f_event(p.events[0], rng)]
    for c, e in zip(p.connectors, p.events[1:]):
        out += [c, f_event(e, rng)]
    return " ".join(out)


# -- W -----------------------------------------------------------------------


def w_event(event: Event, passive: bool = False) -> str:
    verb = _concept(event.verb)
    agt, tgt = _slot(event, "agt"), _slot(event, "tgt")
    if passive and agt is not None and tgt is not None:
        core = [_concept(tgt), "was", verb, "by", _concept(agt)]
    elif agt is not None:
        core = [_concept(agt), verb] + ([_concept(tgt)] if tgt is not None else [])
    else:
        # no agent: the target is the grammatical subject ("the vase fell")
        core = [_concept(tgt), verb] if tgt is not None else [verb]
    periphery = []
    for key in PREP_ORDER:
        value = _slot(event, key)
        if value is not None:
            periphery += [PREPOSITIONS[key], _concept(value)]
    return " ".join(core + periphery)


def w_pipeline(p: Pipeline, passive_first: bool = False) -> str:
    out = [w_event(p.events[0], passive_first)]
    for c, e in zip(p.connectors, p.events[1:]):
        out += [c, w_event(e)]
    return " ".join(out)


# -- tokens ------------------------------------------------------------------


def tokens(text: str) -> list[str]:
    """``agt:Red.Apple`` -> ``agt: Red . Apple``."""
    out = []
    for word in text.split():
        m = re.match(r"^([a-z]+:)(.*)$", word)
        if m:
            out.append(m.group(1))
            word = m.group(2)
        parts = word.split(".")
        for i, part in enumerate(parts):
            if i:
                out.append(".")
            out.append(part)
    return out
