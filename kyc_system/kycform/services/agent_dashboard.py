from datetime import date, timedelta
from django.db import connections


def get_agent_dashboard_data(agent_code: str):
    """
    Reads KPI + chart data from CORE MSSQL
    NO writes, NO temp table dependence
    """

    today = date.today()
    from_date = today - timedelta(days=30)

    data = {
        "kpi": {
            "policies": {"total": 0, "new": 0, "renewal": 0},
            "premium": {"total": 0, "self": 0, "downline": 0},
            "downline": 0,
        },
        "summary": {"policies": 0, "premium": 0, "commission": 0},
        "chart": {"labels": [], "premium": [], "commission": []},
    }

    with connections["sqlserver"].cursor() as cursor:

        # --------------------------------------------------
        # 1️⃣ POLICY COUNTS (Self / Downline / Total)
        # --------------------------------------------------
        cursor.execute(
            """
            EXEC proc_MISAgentCountDetailReport
                @Flag = 'Agent',
                @user = %s
            """,
            [agent_code],
        )
        row = cursor.fetchone()
        if row:
            data["kpi"]["policies"]["new"] = int(row[0] or 0)
            data["kpi"]["policies"]["renewal"] = int(row[1] or 0)
            data["kpi"]["policies"]["total"] = (
                data["kpi"]["policies"]["new"]
                + data["kpi"]["policies"]["renewal"]
            )

        # --------------------------------------------------
        # 2️⃣ DOWNLINE COUNT
        # --------------------------------------------------
        cursor.execute(
            """
            EXEC proc_GetAgentUnderAgent
                @Flag = 'Count',
                @user = %s
            """,
            [agent_code],
        )
        row = cursor.fetchone()
        if row:
            data["kpi"]["downline"] = int(row[0] or 0)

        # --------------------------------------------------
        # 3️⃣ PREMIUM + COMMISSION SUMMARY (30 days)
        # --------------------------------------------------
        cursor.execute(
            """
            EXEC proc_CommissionPayableReportWithAgentLoan
                @Flag     = 'Summary',
                @Param    = %s,
                @fromDate = %s,
                @toDate   = %s
            """,
            [agent_code, from_date, today],
        )
        row = cursor.fetchone()
        if row:
            data["kpi"]["premium"]["self"] = float(row[0] or 0)
            data["kpi"]["premium"]["downline"] = float(row[1] or 0)
            data["kpi"]["premium"]["total"] = float(row[2] or 0)

            data["summary"]["premium"] = data["kpi"]["premium"]["total"]
            data["summary"]["commission"] = float(row[3] or 0)

        # --------------------------------------------------
        # 4️⃣ MONTHLY SALES CHART
        # --------------------------------------------------
        cursor.execute(
            """
            EXEC proc_MISAgentBusinessReport
                @Flag = 'Monthly',
                @user = %s
            """,
            [agent_code],
        )
        rows = cursor.fetchall()
        for r in rows:
            data["chart"]["labels"].append(str(r[0]))
            data["chart"]["premium"].append(float(r[1] or 0))
            data["chart"]["commission"].append(float(r[2] or 0))

    return data
