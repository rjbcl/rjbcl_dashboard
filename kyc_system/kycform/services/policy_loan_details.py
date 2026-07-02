from datetime import date, datetime
from decimal import Decimal

from django.db import connections


def _build_in_clause(values):
    placeholders = ",".join(["%s"] * len(values))
    return f"({placeholders})"


def _resolve_column(column_names, candidates):
    lowered = {name.lower(): name for name in column_names}
    for candidate in candidates:
        actual = lowered.get(candidate.lower())
        if actual:
            return actual
    return None


def _build_optional_select(column_name, alias):
    if not column_name:
        return f"NULL AS {alias}"
    return f"[{column_name}] AS {alias}"


def _serialize_value(value):
    if isinstance(value, memoryview):
        value = value.tobytes()
    if isinstance(value, (bytes, bytearray)):
        # Keep binary columns JSON-safe and deterministic.
        return value.hex()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


class PolicyLoanDetailsService:
    @staticmethod
    def _empty_payload():
        return {
            "rows": [],
            "total_items": 0,
            "total": {
                "loan_amount": 0.0,
                "balance_amount": 0.0,
            },
        }

    @staticmethod
    def _resolve_table_columns(cursor):
        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'tblPolicyLoanDetail'
            ORDER BY ORDINAL_POSITION
            """
        )
        return [r[0] for r in cursor.fetchall()]

    @staticmethod
    def get_loan_details(policy_numbers, page=1, page_size=10):
        policies = [p for p in policy_numbers if p]
        if not policies:
            return PolicyLoanDetailsService._empty_payload()

        if "sqlserver" not in connections.databases:
            payload = PolicyLoanDetailsService._empty_payload()
            payload["detail"] = "CORE_DB_UNAVAILABLE"
            return payload

        page = int(page or 1)
        page_size = int(page_size or 10)
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 100:
            page_size = 100

        offset = (page - 1) * page_size
        in_clause = _build_in_clause(policies)

        with connections["sqlserver"].cursor() as cursor:
            columns = PolicyLoanDetailsService._resolve_table_columns(cursor)
            if not columns:
                payload = PolicyLoanDetailsService._empty_payload()
                payload["detail"] = "LOAN_TABLE_NOT_FOUND"
                return payload

            policy_col = _resolve_column(
                columns, ["PolicyNo", "PolicyNO", "PolicyNumber", "Policy_No"]
            )
            if not policy_col:
                payload = PolicyLoanDetailsService._empty_payload()
                payload["detail"] = "LOAN_POLICY_COLUMN_NOT_FOUND"
                return payload

            amount_col = _resolve_column(
                columns,
                ["LoanAmount", "LoanAmt", "Amount", "PrincipalAmount", "PrincipleAmount"],
            )
            balance_col = _resolve_column(
                columns,
                ["BalanceAmount", "OutstandingAmount", "Outstanding", "Balance", "DueAmount", "LoanBalance"],
            )
            order_col = _resolve_column(
                columns, ["LoanDate", "DOC", "CreatedDate", "EntryDate", "LoanID", "ID"]
            ) or policy_col
            loan_date_col = _resolve_column(
                columns, ["LoanDate", "DOC", "CreatedDate", "EntryDate"]
            )
            interest_col = _resolve_column(
                columns, ["InterestAmount", "InterestAmt", "IntAmount", "Interest"]
            )
            status_col = _resolve_column(
                columns, ["LoanStatus", "Status", "CurrentStatus", "ApprovalStatus"]
            )

            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM tblPolicyLoanDetail WITH (NOLOCK)
                WHERE [{policy_col}] IN {in_clause}
                """,
                policies,
            )
            total_items = int((cursor.fetchone() or [0])[0] or 0)
            total_pages = (total_items + page_size - 1) // page_size if total_items else 0
            if total_pages and page > total_pages:
                page = total_pages
                offset = (page - 1) * page_size

            total_loan_amount = 0.0
            if amount_col:
                cursor.execute(
                    f"""
                    SELECT ISNULL(SUM(CAST([{amount_col}] AS DECIMAL(38,2))), 0)
                    FROM tblPolicyLoanDetail WITH (NOLOCK)
                    WHERE [{policy_col}] IN {in_clause}
                    """,
                    policies,
                )
                total_loan_amount = float((cursor.fetchone() or [0])[0] or 0)

            total_balance_amount = 0.0
            if balance_col:
                cursor.execute(
                    f"""
                    SELECT ISNULL(SUM(CAST([{balance_col}] AS DECIMAL(38,2))), 0)
                    FROM tblPolicyLoanDetail WITH (NOLOCK)
                    WHERE [{policy_col}] IN {in_clause}
                    """,
                    policies,
                )
                total_balance_amount = float((cursor.fetchone() or [0])[0] or 0)

            cursor.execute(
                f"""
                SELECT
                    [{policy_col}] AS policy_no,
                    {_build_optional_select(loan_date_col, "loan_date")},
                    {_build_optional_select(amount_col, "loan_amount")},
                    {_build_optional_select(balance_col, "balance_amount")},
                    {_build_optional_select(interest_col, "interest_amount")},
                    {_build_optional_select(status_col, "status")}
                FROM tblPolicyLoanDetail WITH (NOLOCK)
                WHERE [{policy_col}] IN {in_clause}
                ORDER BY [{order_col}] DESC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
                """,
                policies + [offset, page_size],
            )
            rows = cursor.fetchall()
            row_columns = [col[0] for col in cursor.description]

        data_rows = []
        for row in rows:
            data_rows.append(
                {
                    key: _serialize_value(value)
                    for key, value in zip(row_columns, row)
                }
            )

        return {
            "rows": data_rows,
            "total_items": total_items,
            "total": {
                "loan_amount": round(total_loan_amount, 2),
                "balance_amount": round(total_balance_amount, 2),
            },
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_rows": total_items,
                "total_pages": total_pages,
                "has_next": bool(total_pages and page < total_pages),
                "has_prev": bool(total_pages and page > 1),
            },
        }

    @staticmethod
    def get_dashboard_loan_data(policy_numbers, preview_size=5):
        result = PolicyLoanDetailsService.get_loan_details(
            policy_numbers, page=1, page_size=preview_size
        )
        return {
            "count": int(result.get("total_items", 0) or 0),
            "loan_amount": float(result.get("total", {}).get("loan_amount", 0) or 0),
            "balance_amount": float(result.get("total", {}).get("balance_amount", 0) or 0),
            "rows": result.get("rows", []),
            "detail": result.get("detail"),
        }
