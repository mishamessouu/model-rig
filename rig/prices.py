"""Turn token counts into cost with a price sheet from config/prices.toml."""
import tomllib

from . import ROOT

KINDS = ("input", "output", "cache_read", "cache_write")


def load(path=None):
    return tomllib.loads((path or ROOT / "config" / "prices.toml").read_text())["sheets"]


def cost(sheet, by_model):
    """Cost of `by_model` ({model: tokens}) in the sheet's unit.

    A model the sheet does not list makes the cost None and is named in the
    second value, so a partial sum never reads as the whole cost.
    """
    if not by_model:
        # A run with no usage record (a timeout, a crash) has an unknown
        # cost, not a cost of zero.
        return None, ["no usage recorded"]
    total, missing = 0.0, []
    for model, tokens in by_model.items():
        # The longest matching key wins, so "claude-sonnet-5" does not
        # price "claude-sonnet-5-5".
        keys = [key for key in sheet["models"] if model.startswith(key)]
        price = sheet["models"][max(keys, key=len)] if keys else None
        if price is None:
            missing.append(model)
            continue
        total += sum(tokens.get(kind, 0) * price[kind] for kind in KINDS) / 1e6
    return (None if missing else round(total, 4)), missing
