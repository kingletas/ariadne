from ..core.refusal import Refusal

# ---------------------------------------------------------------------------
# Quotation convention -- detected once, per book
# ---------------------------------------------------------------------------


def quote_convention(text):
    doubles = text.count('"') + text.count("“")
    singles = text.count("‘")
    if doubles >= 20 and doubles >= singles:
        return "double"
    if singles >= 20:
        return "single"
    raise Refusal(
        "no quotation convention found -- double quotes %d, single quotes %d. "
        "Dialogue cannot be told from narration, so nothing that depends on it "
        "is reported. A book set in em-dashes needs a different rule." % (doubles, singles)
    )
