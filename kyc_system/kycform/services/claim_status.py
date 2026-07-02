from datetime import date, datetime
from decimal import Decimal

from django.core.cache import cache
from django.db import connections


CLAIM_STATUS_CACHE_TTL = 10 * 60


def _clean_key(value):
    return "".join(ch for ch in str(value or "").lower() if ch.isalnum())


def _json_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _get_first(row, keys, default=""):
    cleaned = {_clean_key(key): value for key, value in row.items()}
    for key in keys:
        value = cleaned.get(_clean_key(key))
        if value is not None:
            return value
    return default


def _format_date(value):
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        value = value.strip()
        if "T" in value:
            return value.split("T", 1)[0]
    return str(value or "")


def _parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return datetime.strptime(str(value).strip()[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _normalize_claim_status(status, claim_paid_date, voucher_no):
    raw_status = str(status or "").strip()
    if raw_status == "0":
        return "Unpaid"
    if raw_status == "1":
        return "Paid"

    has_voucher = bool(str(voucher_no or "").strip())
    if not raw_status and has_voucher:
        return "Paid"

    return raw_status or "-"


def _fetch_rows(cursor):
    columns = [col[0] for col in cursor.description] if cursor.description else []
    rows = []

    for db_row in cursor.fetchall():
        rows.append(
            {
                columns[index]: _json_value(value)
                for index, value in enumerate(db_row)
            }
        )

    return rows


def _sort_key(row):
    claim_paid_date = row.get("claim_paid_date") or ""
    approve_date = row.get("approve_date") or ""
    return (
        _parse_date(claim_paid_date) or date.min,
        _parse_date(approve_date) or date.min,
        str(row.get("claim_no") or ""),
        str(row.get("id") or ""),
    )


def fetch_claim_status(policy_no):
    policy_no = str(policy_no or "").strip()
    if not policy_no:
        return {"holder": {}, "claims": []}

    cache_key = f"claim_status:claims:{policy_no}"
    cached_value = cache.get(cache_key)
    if cached_value is not None:
        return cached_value

    if "sqlserver" not in connections.databases:
        return {"holder": {}, "claims": []}

    policy_filter_sql = ""
    params = []
    if policy_no:
        policy_filter_sql = " AND LTRIM(RTRIM(ISNULL(PolicyNo, ''))) = %s"
        params.append(policy_no)

    query = f"""
        SELECT * FROM (
            SELECT
                PolicyNo,
                ClaimNo = claimid,
                ClaimStatus = PaidStatus,
                Remarks,
                ClaimPaidDate = PaidDate,
                ClaimType = 'Death',
                VoucherNo,
                ApproveDate,
                PolicyType = 'GroupPolicy'
            FROM tblGroupDeathClaim
            UNION
            SELECT
                PolicyNo,
                ClaimNo = claimid,
                ClaimStatus = PaidStatus,
                Remarks = '',
                ClaimPaidDate = SurrenderPaidDate,
                ClaimType = 'Surrender',
                VoucherNo,
                ApproveDate,
                PolicyType = 'GroupPolicy'
            FROM tblGroupSurrender
            UNION
            SELECT
                PolicyNo,
                ClaimNo = claimid,
                ClaimStatus = PaidStatus,
                Remarks,
                ClaimPaidDate = PaidDate,
                ClaimType = 'Maturity',
                VoucherNo,
                ApproveDate,
                PolicyType = 'GroupPolicy'
            FROM tblGroupMaturity
            UNION
            SELECT
                PolicyNo,
                ClaimNo = claimid,
                ClaimStatus,
                Remarks,
                ClaimPaidDate = ClaimPaidDate,
                ClaimType = 'Death',
                VoucherNo,
                ApproveDate = ApprovalDate,
                PolicyType = 'IndividualPolicy'
            FROM tblclaim
            UNION
            SELECT
                PolicyNo,
                ClaimNo,
                ClaimStatus = Status,
                Remarks,
                ClaimPaidDate = SurrenderPaidDate,
                ClaimType = 'Surrender',
                VoucherNo,
                ApproveDate = ApprovedDate,
                PolicyType = 'IndividualPolicy'
            FROM tblSurrender
            UNION
            SELECT
                PolicyNo,
                ClaimNo,
                ClaimStatus = Status,
                Remarks,
                ClaimPaidDate = MaturityPaidDate,
                ClaimType = 'Maturity',
                VoucherNo,
                ApproveDate = ApprovedDate,
                PolicyType = 'IndividualPolicy'
            FROM tblmaturity
        ) X
        WHERE ISNULL(PolicyNo, '') <> ''
          {policy_filter_sql}
          AND (
                ClaimPaidDate IS NULL
                OR (
                    ClaimPaidDate >= DATEADD(MONTH, -3, CAST(GETDATE() AS DATE))
                    AND ClaimPaidDate <= CAST(GETDATE() AS DATE)
                )
              )
          AND (
                ApproveDate IS NULL
                OR (
                    ApproveDate >= DATEADD(MONTH, -3, CAST(GETDATE() AS DATE))
                    AND ApproveDate <= CAST(GETDATE() AS DATE)
                )
              )
    """

    with connections["sqlserver"].cursor() as cursor:
        cursor.execute(query, params)
        rows = _fetch_rows(cursor)

    claims = []
    for index, row in enumerate(rows, start=1):
        claim_no = str(_get_first(row, ["ClaimNo", "claimid"], "") or "").strip()
        policy_value = str(_get_first(row, ["PolicyNo", "Policy No"], policy_no) or policy_no).strip()
        claim_paid_date = _format_date(
            _get_first(row, ["ClaimPaidDate", "PaidDate", "SurrenderPaidDate", "MaturityPaidDate"], "")
        )
        claims.append(
            {
                "id": claim_no or f"{policy_value}-{index}",
                "policy_no": policy_value,
                "claim_no": claim_no,
                "claim_status": _normalize_claim_status(
                    _get_first(row, ["ClaimStatus", "PaidStatus", "Status"], ""),
                    claim_paid_date,
                    _get_first(row, ["VoucherNo", "Voucher No"], ""),
                ),
                "remarks": str(_get_first(row, ["Remarks"], "") or "").strip(),
                "claim_paid_date": claim_paid_date,
                "voucher_no": str(_get_first(row, ["VoucherNo", "Voucher No"], "") or "").strip(),
                "approve_date": _format_date(_get_first(row, ["ApproveDate", "ApprovedDate", "ApprovalDate"], "")),
                "policy_type": str(_get_first(row, ["PolicyType"], "") or "").strip(),
                "raw": row,
            }
        )

    claims.sort(key=_sort_key, reverse=True)

    result = {
        "holder": {"policy_no": policy_no},
        "claims": claims,
    }
    cache.set(cache_key, result, CLAIM_STATUS_CACHE_TTL)
    return result
