from datetime import date

from django.db import connections
from kycform.services.policy_loan_details import PolicyLoanDetailsService


def _build_in_clause(values):
    placeholders = ",".join(["%s"] * len(values))
    return f"({placeholders})"


def get_policy_dashboard_data(policy_numbers):
    """
    Returns dashboard payload for policy-holder portal.
    Reads only from CORE SQLServer.
    """
    policies = [p for p in policy_numbers if p]
    if not policies:
        return {
            "kpi": {
                "policies": {"total": 0},
                "premium": {"total": 0},
                "due": {"count": 0, "premium": 0},
            },
            "summary": {"policies": 0, "premium": 0, "paid_installments": 0},
            "chart": {"labels": [], "premium": []},
            "history": [],
            "loan": {
                "count": 0,
                "loan_amount": 0.0,
                "balance_amount": 0.0,
                "rows": [],
            },
        }

    in_clause = _build_in_clause(policies)

    data = {
        "kpi": {
            "policies": {"total": 0},
            "premium": {"total": 0},
            "due": {"count": 0, "premium": 0},
        },
        "summary": {"policies": 0, "premium": 0, "paid_installments": 0},
        "chart": {"labels": [], "premium": []},
        "history": [],
        "loan": {
            "count": 0,
            "loan_amount": 0.0,
            "balance_amount": 0.0,
            "rows": [],
        },
    }

    with connections["sqlserver"].cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
                COUNT(DISTINCT pd.PolicyNo) AS total_policies,
                SUM(CASE WHEN pd.FUP < GETDATE() THEN 1 ELSE 0 END) AS due_count,
                ISNULL(SUM(CASE WHEN pd.FUP < GETDATE() THEN pd.Premium ELSE 0 END), 0) AS due_premium
            FROM tblPolicyDetail pd WITH (NOLOCK)
            WHERE pd.PolicyNo IN {in_clause}
            """,
            policies,
        )
        row = cursor.fetchone()
        if row:
            data["kpi"]["policies"]["total"] = int(row[0] or 0)
            data["kpi"]["due"]["count"] = int(row[1] or 0)
            data["kpi"]["due"]["premium"] = float(row[2] or 0)

        cursor.execute(
            f"""
            SELECT ISNULL(SUM(CAST(pp.Premium AS DECIMAL(18,2))), 0) AS total_paid_premium
            FROM tblPremiumPaid pp WITH (NOLOCK)
            WHERE pp.PolicyNo IN {in_clause}
            """,
            policies,
        )
        row = cursor.fetchone()
        if row:
            data["kpi"]["premium"]["total"] = float(row[0] or 0)

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM tblPremiumPaid pp WITH (NOLOCK)
            WHERE pp.PolicyNo IN {in_clause}
            """,
            policies,
        )
        row = cursor.fetchone()
        paid_installments = int((row[0] or 0) if row else 0)

        today = date.today()
        month_starts = []
        for i in range(11, -1, -1):
            y = today.year
            m = today.month - i
            while m <= 0:
                y -= 1
                m += 12
            while m > 12:
                y += 1
                m -= 12
            month_starts.append(date(y, m, 1))

        chart_start = month_starts[0]

        cursor.execute(
            f"""
            SELECT
                YEAR(pp.PaidDate)            AS paid_year,
                MONTH(pp.PaidDate)           AS paid_month,
                ISNULL(SUM(CAST(pp.Premium AS DECIMAL(18,2))), 0) AS premium_amount
            FROM tblPremiumPaid pp WITH (NOLOCK)
            WHERE pp.PolicyNo IN {in_clause}
              AND pp.PaidDate >= %s
            GROUP BY YEAR(pp.PaidDate), MONTH(pp.PaidDate)
            ORDER BY paid_year, paid_month
            """,
            policies + [chart_start],
        )
        month_value_map = {
            (int(r[0]), int(r[1])): float(r[2] or 0)
            for r in cursor.fetchall()
        }

        for dt in month_starts:
            data["chart"]["labels"].append(dt.strftime("%b %Y"))
            data["chart"]["premium"].append(month_value_map.get((dt.year, dt.month), 0.0))

        cursor.execute(
            f"""
            SELECT TOP 10
                pp.PolicyNo,
                CONVERT(VARCHAR(10), pp.PaidDate, 120) AS paid_date,
                CAST(pp.Premium AS DECIMAL(18,2)) AS amount,
                pd.PayMode
            FROM tblPremiumPaid pp WITH (NOLOCK)
            INNER JOIN tblPolicyDetail pd WITH (NOLOCK)
                    ON pd.PolicyNo = pp.PolicyNo
            WHERE pp.PolicyNo IN {in_clause}
            ORDER BY pp.PaidDate DESC
            """,
            policies,
        )
        rows = cursor.fetchall()
        for idx, row in enumerate(rows, start=1):
            data["history"].append(
                {
                    "sn": idx,
                    "policy_no": row[0],
                    "paid_date": row[1],
                    "amount": float(row[2] or 0),
                    "mode": row[3] or "-",
                }
            )

    data["summary"]["policies"] = data["kpi"]["policies"]["total"]
    data["summary"]["premium"] = round(data["kpi"]["premium"]["total"], 2)
    data["summary"]["paid_installments"] = paid_installments

    data["kpi"]["premium"]["total"] = round(data["kpi"]["premium"]["total"], 2)
    data["kpi"]["due"]["premium"] = round(data["kpi"]["due"]["premium"], 2)
    data["loan"] = PolicyLoanDetailsService.get_dashboard_loan_data(policies)

    return data
