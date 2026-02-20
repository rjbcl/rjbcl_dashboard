from django.db import connections
from rest_framework.views import APIView
from rest_framework.response import Response


class AgentBusinessReportAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        agent_code = request.session.get("agent_code")
        if not agent_code:
            return Response({"detail": "Agent not authenticated"}, status=401)

        policy_no = request.GET.get("policy_no", "").strip()
        name = request.GET.get("name", "").strip()

        params = [agent_code]
        search_filter = ""

        if policy_no and name:
            search_filter = """
                AND (
                    p.PolicyNo LIKE %s
                    OR (
                        i.FirstName
                        + ISNULL(' ' + i.MiddleName, '')
                        + ISNULL(' ' + i.LastName, '')
                    ) LIKE %s
                )
            """
            params.extend([f"%{policy_no}%", f"%{name}%"])
        elif policy_no:
            search_filter = "AND p.PolicyNo LIKE %s"
            params.append(f"%{policy_no}%")
        elif name:
            search_filter = """
                AND (
                    i.FirstName
                    + ISNULL(' ' + i.MiddleName, '')
                    + ISNULL(' ' + i.LastName, '')
                ) LIKE %s
            """
            params.append(f"%{name}%")

        with connections["sqlserver"].cursor() as cursor:
            cursor.execute(f"""
                SELECT
                    ROW_NUMBER() OVER (ORDER BY p.DOC DESC) AS SN,
                    p.PolicyNo,
                    i.FirstName
                        + ISNULL(' ' + i.MiddleName, '')
                        + ISNULL(' ' + i.LastName, '') AS PolicyHolder,
                    pl.PlanName,
                    p.Term,
                    p.PayMode,
                    CONVERT(VARCHAR(10), p.DOC, 103) AS DOC,
                    CAST(p.SA AS MONEY) AS SA,
                    CAST(p.Premium AS MONEY) AS Premium,
                    CONVERT(VARCHAR(10), pp.PaidDate, 103) AS PaidDate,
                    CASE
                        WHEN pp.InstalmenType = 'F' THEN 'FIRST'
                        ELSE 'RENEWAL'
                    END AS PremiumType
                FROM tblPolicyDetail p WITH (NOLOCK)

                INNER JOIN tblInsuredDetail i WITH (NOLOCK)
                        ON p.Registerno = i.Registerno

                INNER JOIN tblPlan pl WITH (NOLOCK)
                        ON p.PlanID = pl.PlanID

                OUTER APPLY (
                    SELECT TOP 1 *
                    FROM tblPremiumPaid x WITH (NOLOCK)
                    WHERE x.PolicyNo = p.PolicyNo
                    ORDER BY x.PaidDate DESC
                ) pp

                WHERE p.AgentCode = %s
                {search_filter}

                ORDER BY p.DOC DESC
            """, params)

            rows = cursor.fetchall()

        data = []
        total_sa = 0
        total_premium = 0

        for r in rows:
            sa = float(r[7] or 0)
            premium = float(r[8] or 0)

            total_sa += sa
            total_premium += premium

            data.append({
                "sn": r[0],
                "policy_no": r[1],
                "policy_holder": r[2],
                "plan": r[3],
                "term": r[4],
                "paymode": r[5],
                "doc": r[6],
                "sa": sa,
                "premium": premium,
                "paid_date": r[9],
                "premium_type": r[10]
            })

        return Response({
            "rows": data,
            "total": {
                "sa": round(total_sa, 2),
                "premium": round(total_premium, 2)
            }
        })
