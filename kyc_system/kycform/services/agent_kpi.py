from django.db import connections

def fetch_agent_kpis(agent_code):
    with connections["sqlserver"].cursor() as cursor:

        # 1️⃣ POLICY COUNTS
        cursor.execute("""
            EXEC proc_MISAgentCountDetailReport @AgentCode=%s
        """, [agent_code])
        policy_row = cursor.fetchone() or (0, 0, 0)

        # 2️⃣ PREMIUM + COMMISSION
        cursor.execute("""
            EXEC proc_CommissionPayableReportWithAgentLoan @AgentCode=%s
        """, [agent_code])
        money_row = cursor.fetchone() or (0, 0)

        # 3️⃣ DOWNLINE COUNT
        cursor.execute("""
            EXEC proc_GetAgentUnderAgent @AgentCode=%s
        """, [agent_code])
        downline_row = cursor.fetchone()
        downline_count = downline_row[0] if downline_row else 0

    return {
        "kpi": {
            "policies": {
                "total": policy_row[0],
                "new": policy_row[1],
                "renewal": policy_row[2],
            },
            "premium": {
                "total": money_row[0],
                "self": money_row[0],   # if split unavailable
                "downline": 0,
            },
            "downline": downline_count,
        }
    }
