from django.core.cache import cache
from django.db import connections
from rest_framework.response import Response
from rest_framework.views import APIView


class AgentSummaryAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        agent_code = request.session.get("agent_code")
        if not agent_code:
            return Response({"detail": "Agent not authenticated"}, status=401)

        cache_key = f"agent:summary:{agent_code}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        with connections["sqlserver"].cursor() as cursor:
            cursor.execute(
                """
                WITH downline AS (
                    SELECT u.AgentCode
                    FROM tblAgentUnderSuperior u WITH (NOLOCK)
                    INNER JOIN tblAgentSuperior s WITH (NOLOCK)
                            ON u.SuperiorCode = s.SuperiorCode
                    WHERE s.PersonalAgentCode = %s
                )
                SELECT
                    -- policy counts
                    SUM(CASE WHEN pd.AgentCode = %s THEN 1 ELSE 0 END) AS self_policy,
                    SUM(CASE WHEN pd.AgentCode IN (SELECT AgentCode FROM downline) THEN 1 ELSE 0 END) AS downline_policy,

                    -- premium
                    ISNULL(SUM(CASE WHEN pd.AgentCode = %s THEN pd.Premium ELSE 0 END), 0) AS self_premium,
                    ISNULL(SUM(CASE WHEN pd.AgentCode IN (SELECT AgentCode FROM downline) THEN pd.Premium ELSE 0 END), 0) AS downline_premium,

                    -- commission (from paid table)
                    ISNULL(SUM(CASE WHEN pd.AgentCode = %s THEN pp.CommAmount ELSE 0 END), 0) AS self_commission,
                    ISNULL(SUM(CASE WHEN pd.AgentCode IN (SELECT AgentCode FROM downline) THEN pp.CommAmount ELSE 0 END), 0) AS downline_commission
                FROM tblPolicyDetail pd WITH (NOLOCK)
                LEFT JOIN tblPremiumPaid pp WITH (NOLOCK)
                       ON pd.PolicyNo = pp.PolicyNo
                WHERE pd.AgentCode = %s
                   OR pd.AgentCode IN (SELECT AgentCode FROM downline)
                """,
                [agent_code, agent_code, agent_code, agent_code, agent_code],
            )
            totals_row = cursor.fetchone() or (0, 0, 0, 0, 0, 0)

            self_policy = int(totals_row[0] or 0)
            downline_policy = int(totals_row[1] or 0)
            self_premium = float(totals_row[2] or 0)
            downline_premium = float(totals_row[3] or 0)
            self_commission = float(totals_row[4] or 0)
            downline_commission = float(totals_row[5] or 0)

            cursor.execute(
                """
                SELECT COUNT(DISTINCT u.AgentCode)
                FROM tblAgentUnderSuperior u WITH (NOLOCK)
                INNER JOIN tblAgentSuperior s WITH (NOLOCK)
                        ON u.SuperiorCode = s.SuperiorCode
                INNER JOIN tblAgent a WITH (NOLOCK)
                        ON a.AgentCode = u.AgentCode
                WHERE s.PersonalAgentCode = %s
                  AND a.IsActive = 1
                  AND a.LicenseExpiryDate > GETDATE()
                """,
                [agent_code],
            )
            downline_count = int((cursor.fetchone() or [0])[0] or 0)

            cursor.execute(
                """
                SELECT
                    DATENAME(MONTH, pp.PaidDate) AS MonthName,
                    MONTH(pp.PaidDate)           AS MonthNo,
                    SUM(pd.Premium)              AS Premium,
                    SUM(pp.CommAmount)           AS Commission
                FROM tblPolicyDetail pd WITH (NOLOCK)
                INNER JOIN tblPremiumPaid pp WITH (NOLOCK)
                        ON pd.PolicyNo = pp.PolicyNo
                WHERE pd.AgentCode = %s
                GROUP BY MONTH(pp.PaidDate), DATENAME(MONTH, pp.PaidDate)
                ORDER BY MonthNo
                """,
                [agent_code],
            )
            chart_rows = cursor.fetchall()

        total_policy = self_policy + downline_policy
        total_premium = self_premium + downline_premium
        total_commission = self_commission + downline_commission

        response = {
            "kpi": {
                "policies": {
                    "total": total_policy,
                    "self": self_policy,
                    "downline": downline_policy,
                },
                "premium": {
                    "total": round(total_premium, 2),
                    "self": round(self_premium, 2),
                    "downline": round(downline_premium, 2),
                },
                "downline": {
                    "count": downline_count,
                },
            },
            "summary": {
                "policies": total_policy,
                "premium": round(total_premium, 2),
                "commission": round(total_commission, 2),
            },
            "chart": {
                "labels": [row[0] for row in chart_rows],
                "premium": [float(row[2] or 0) for row in chart_rows],
                "commission": [float(row[3] or 0) for row in chart_rows],
            },
        }

        cache.set(cache_key, response, 60)
        return Response(response)
