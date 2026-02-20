from django.db import connections
from datetime import date


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
    }

    with connections["sqlserver"].cursor() as cursor:
        # Total policies + base premium
        cursor.execute(
            f"""
            SELECT
                COUNT(DISTINCT pd.PolicyNo) AS total_policies,
                ISNULL(SUM(pd.Premium), 0) AS total_premium
            FROM tblPolicyDetail pd WITH (NOLOCK)
            WHERE pd.PolicyNo IN {in_clause}
            """,
            policies,
        )
        row = cursor.fetchone()
        if row:
            data["kpi"]["policies"]["total"] = int(row[0] or 0)
            data["kpi"]["premium"]["total"] = float(row[1] or 0)

        # Due status
        cursor.execute(
            f"""
            SELECT
                COUNT(*) AS due_count,
                ISNULL(SUM(pd.Premium), 0) AS due_premium
            FROM tblPolicyDetail pd WITH (NOLOCK)
            WHERE pd.PolicyNo IN {in_clause}
              AND pd.FUP < GETDATE()
            """,
            policies,
        )
        row = cursor.fetchone()
        if row:
            data["kpi"]["due"]["count"] = int(row[0] or 0)
            data["kpi"]["due"]["premium"] = float(row[1] or 0)

        # Paid installment count
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

        # Monthly chart (last 12 months, year-aware)
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
                ISNULL(SUM(pd.Premium), 0)   AS premium_amount
            FROM tblPremiumPaid pp WITH (NOLOCK)
            INNER JOIN tblPolicyDetail pd WITH (NOLOCK)
                    ON pd.PolicyNo = pp.PolicyNo
            WHERE pp.PolicyNo IN {in_clause}
              AND pp.PaidDate >= %s
            GROUP BY YEAR(pp.PaidDate), MONTH(pp.PaidDate)
            ORDER BY paid_year, paid_month
            """,
            policies + [chart_start],
        )
        month_value_map = {
            (int(row[0]), int(row[1])): float(row[2] or 0)
            for row in cursor.fetchall()
        }

        for dt in month_starts:
            data["chart"]["labels"].append(dt.strftime("%b %Y"))
            data["chart"]["premium"].append(month_value_map.get((dt.year, dt.month), 0.0))

        # Recent payment history
        cursor.execute(
            f"""
            SELECT TOP 10
                pp.PolicyNo,
                CONVERT(VARCHAR(10), pp.PaidDate, 120) AS paid_date,
                CAST(pd.Premium AS DECIMAL(18,2)) AS amount,
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

    return data
