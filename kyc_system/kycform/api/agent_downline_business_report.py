from django.db import connections
from rest_framework.views import APIView
from rest_framework.response import Response


class AgentDownlineBusinessReportAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        agent_code = request.session.get("agent_code")
        if not agent_code:
            return Response({"rows": []}, status=401)

        filter_agent = request.GET.get("agent_code", "").strip()
        superior_code = f"AM{agent_code}"

        params = [superior_code]
        agent_filter_sql = ""

        if filter_agent:
            agent_filter_sql = "AND a.AgentCode LIKE %s"
            params.append(f"%{filter_agent}%")

        with connections["sqlserver"].cursor() as cursor:
            cursor.execute(f"""
                SELECT
                    ROW_NUMBER() OVER (ORDER BY a.AgentCode) AS SN,
                    a.AgentCode,
                    a.FirstName + ISNULL(' ' + a.LastName,'') AS AgentName,

                    COUNT(DISTINCT p.PolicyNo) AS PolicyCount,

                    -- Earned Premium (all policies)
                    ISNULL(SUM(p.Premium),0) AS EarnedPremium,

                    -- Credit Premium (only paid policies)
                    ISNULL(SUM(
                        CASE WHEN pp.PolicyNo IS NOT NULL
                             THEN p.Premium ELSE 0 END
                    ),0) AS CreditPremium

                FROM tblAgentUnderSuperior u
                INNER JOIN tblAgent a
                        ON a.AgentCode = u.AgentCode
                INNER JOIN tblPolicyDetail p
                        ON p.AgentCode = a.AgentCode
                LEFT JOIN tblPremiumPaid pp
                        ON pp.PolicyNo = p.PolicyNo

                WHERE u.SuperiorCode = %s
                {agent_filter_sql}

                GROUP BY a.AgentCode, a.FirstName, a.LastName
                ORDER BY a.AgentCode
            """, params)

            rows = cursor.fetchall()

        data = []
        totals = {
            "policy": 0,
            "earned": 0,
            "credit": 0,
            "not_included": 0
        }

        for r in rows:
            earned = float(r[4])
            credit = float(r[5])
            not_included = earned - credit

            totals["policy"] += r[3]
            totals["earned"] += earned
            totals["credit"] += credit
            totals["not_included"] += not_included

            data.append({
                "sn": r[0],
                "agent_name": f"{r[2]} ({r[1]})",
                "policy": r[3],
                "earned": earned,
                "credit": credit,
                "not_included": not_included,
                "business_type": "DOWNLINE"
            })

        return Response({
            "rows": data,
            "total": totals
        })
