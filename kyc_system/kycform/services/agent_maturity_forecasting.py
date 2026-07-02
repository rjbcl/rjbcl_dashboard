from django.db import connections


class AgentMaturityForecastingService:
    @staticmethod
    def get_maturity_forecasting(agent_code, policy_no=None, page=1, page_size=10):
        page = int(page or 1)
        page_size = int(page_size or 10)
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 100:
            page_size = 100

        params = [agent_code]
        policy_filter = ""
        offset = (page - 1) * page_size

        if policy_no:
            policy_filter = "AND p.PolicyNo LIKE %s"
            params.append(f"%{policy_no}%")

        with connections["sqlserver"].cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    COUNT(*),
                    ISNULL(SUM(CAST(p.SA AS FLOAT)), 0),
                    ISNULL(SUM(CAST(p.Premium AS FLOAT)), 0)
                FROM tblPolicyDetail p
                INNER JOIN tblInsuredDetail i
                        ON p.Registerno = i.Registerno
                WHERE p.AgentCode = %s
                  AND p.CurrentStatus IN ('I', 'L')
                  AND CAST(p.MaturityDate AS DATE) >= CAST(GETDATE() AS DATE)
                  AND CAST(p.MaturityDate AS DATE) <= DATEADD(MONTH, 3, CAST(GETDATE() AS DATE))
                  {policy_filter}
                """,
                params,
            )
            agg_row = cursor.fetchone() or (0, 0, 0)
            total_items = int(agg_row[0] or 0)
            total_sa = float(agg_row[1] or 0)
            total_premium = float(agg_row[2] or 0)

            cursor.execute(
                f"""
                SELECT
                    ROW_NUMBER() OVER (ORDER BY p.MaturityDate ASC, p.PolicyNo ASC) AS SN,
                    p.PolicyNo,
                    p.Registerno,
                    i.FirstName
                        + ISNULL(' ' + i.MiddleName,'')
                        + ISNULL(' ' + i.LastName,'') AS PolicyHolder,
                    i.Mobile,
                    pl.PlanName,
                    p.Term,
                    p.PayMode,
                    CONVERT(VARCHAR(10), p.MaturityDate, 103) AS MaturityDate,
                    CAST(p.SA AS FLOAT),
                    CAST(p.Premium AS FLOAT),
                    CASE
                        WHEN p.CurrentStatus = 'I' THEN 'INFORCE'
                        WHEN p.CurrentStatus = 'L' THEN 'LAPSED'
                        ELSE ISNULL(NULLIF(LTRIM(RTRIM(p.CurrentStatus)), ''), 'UNKNOWN')
                    END AS PolicyStatus
                FROM tblPolicyDetail p
                INNER JOIN tblInsuredDetail i
                        ON p.Registerno = i.Registerno
                INNER JOIN tblPlan pl
                        ON p.PlanID = pl.PlanID
                WHERE p.AgentCode = %s
                  AND p.CurrentStatus IN ('I', 'L')
                  AND CAST(p.MaturityDate AS DATE) >= CAST(GETDATE() AS DATE)
                  AND CAST(p.MaturityDate AS DATE) <= DATEADD(MONTH, 3, CAST(GETDATE() AS DATE))
                  {policy_filter}
                ORDER BY p.MaturityDate ASC, p.PolicyNo ASC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
                """,
                params + [offset, page_size],
            )

            rows = cursor.fetchall()

        data = []
        for r in rows:
            data.append(
                {
                    "sn": r[0],
                    "policy_no": r[1],
                    "register_no": r[2],
                    "policy_holder": r[3],
                    "mobile": r[4],
                    "plan": r[5],
                    "term": r[6],
                    "paymode": r[7],
                    "maturity_date": r[8],
                    "sa": float(r[9] or 0),
                    "premium": float(r[10] or 0),
                    "status": r[11],
                }
            )

        return {
            "rows": data,
            "total_items": total_items,
            "total": {
                "sa": round(total_sa, 2),
                "premium": round(total_premium, 2),
            },
            "summary": {
                "policies": total_items,
            },
        }
