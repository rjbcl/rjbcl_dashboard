STATUS_LABELS = {
    "I": "Inforce",
    "L": "Lapse",
    "P": "Paidup",
    "D": "Death",
    "S": "Surrender",
    "M": "Maturity",
    "F": "Forefeiture",
    "B": "Blocked",
}


def format_policy_status(value):
    code = (value or "").strip()
    if not code:
        return ""
    return STATUS_LABELS.get(code.upper(), code)
