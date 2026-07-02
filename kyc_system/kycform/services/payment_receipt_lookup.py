from kycform.services.policy_client import PolicyClientService
from kycform.services.policy_payment_history import PolicyPaymentHistoryService


def get_payment_receipt_row(user_id, payment_filters):
    client_id = PolicyClientService.get_client_no(user_id)
    data = PolicyPaymentHistoryService.get_payment_history(
        client_id=client_id,
        policy_no=payment_filters.get("policy_no", ""),
        paginated=False,
    )

    rows = data.get("rows", [])
    if not rows:
        return None

    def _norm(value):
        return str(value or "").strip()

    target_policy_no = _norm(payment_filters.get("policy_no"))
    target_paid_date = _norm(payment_filters.get("paid_date"))
    target_paid_amount = _norm(payment_filters.get("paid_amount"))
    target_premium = _norm(payment_filters.get("premium"))
    target_installment_type = _norm(payment_filters.get("installment_type"))

    for row in rows:
        if target_policy_no and _norm(row.get("policy_no")) != target_policy_no:
            continue
        if target_paid_date and _norm(row.get("premium_paid_date")) != target_paid_date:
            continue
        if target_paid_amount and _norm(row.get("paid_amount")) != target_paid_amount:
            continue
        if target_premium and _norm(row.get("premium")) != target_premium:
            continue
        if target_installment_type and _norm(row.get("installment_type")) != target_installment_type:
            continue
        return row

    return rows[0]
