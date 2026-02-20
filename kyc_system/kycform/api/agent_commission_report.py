from django.db import connections
from rest_framework.views import APIView
from rest_framework.response import Response


class AgentCommissionReportAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        agent_code = request.session.get("agent_code")
        if not agent_code:
            return Response({"detail": "Agent not authenticated"}, status=401)

        policy_no = (request.GET.get("policy_no") or "").strip()
        name = (request.GET.get("name") or "").strip()

        params = [agent_code]
        search_filter = ""

        if policy_no and name:
            search_filter = """
                AND (
                    pd.PolicyNo LIKE %s
                    OR (
                        i.FirstName
                        + ISNULL(' ' + i.MiddleName,'')
                        + ISNULL(' ' + i.LastName,'')
                    ) LIKE %s
                )
            """
            params.extend([f"%{policy_no}%", f"%{name}%"])
        elif policy_no:
            search_filter = "AND pd.PolicyNo LIKE %s"
            params.append(f"%{policy_no}%")
        elif name:
            search_filter = """
                AND (
                    i.FirstName
                    + ISNULL(' ' + i.MiddleName,'')
                    + ISNULL(' ' + i.LastName,'')
                ) LIKE %s
            """
            params.append(f"%{name}%")

        with connections["sqlserver"].cursor() as cursor:
            cursor.execute(f"""
                SELECT
                    ROW_NUMBER() OVER (ORDER BY pd.DOC DESC) AS SN,

                    pd.PolicyNo,

                    i.FirstName
                        + ISNULL(' ' + i.MiddleName,'')
                        + ISNULL(' ' + i.LastName,'') AS PolicyHolder,

                    pl.PlanName,
                    pd.Term,
                    pd.PayMode,

                    CONVERT(VARCHAR(10), pd.DOC, 103) AS DOC,
                    CONVERT(VARCHAR(10), pz.PaidDate, 103) AS PaidDate,

                    CAST(pd.SA AS DECIMAL(18,0)) AS SA,
                    CAST(pd.Premium AS DECIMAL(18,0)) AS Premium,

                    CAST(ISNULL(pz.CommRate, 0) AS DECIMAL(6,2)) AS CommissionRate,
                    CAST(ISNULL(pz.CommAmount, 0) AS DECIMAL(18,0)) AS CommissionAmount,

                    pz.InstalmenType AS PremiumType

                FROM tblPolicyDetail pd  WITH (NOLOCK)
                INNER JOIN tblPlan pl            WITH (NOLOCK) ON pl.PlanID = pd.PlanID
                INNER JOIN tblInsuredDetail i    WITH (NOLOCK) ON i.RegisterNo = pd.RegisterNo
                INNER JOIN tblPremiumPaid pz     WITH (NOLOCK) ON pd.PolicyNo = pz.PolicyNo

                WHERE pd.AgentCode = %s
                {search_filter}

                ORDER BY pd.DOC DESC
            """, params)

            rows = cursor.fetchall()

        data = []
        total_sa = 0
        total_premium = 0
        total_commission = 0

        for r in rows:
            sa = r[8] or 0
            premium = r[9] or 0
            commission = r[11] or 0

            total_sa += sa
            total_premium += premium
            total_commission += commission

            data.append({
                "sn": r[0],
                "policy_no": r[1],
                "policy_holder": r[2],
                "plan": f"{r[3]} (Term: {r[4]} | Paymode: {r[5]})",
                "doc": r[6],
                "paid_date": r[7],
                "sa": float(sa),
                "premium": float(premium),
                "commission_rate": float(r[10] or 0),
                "commission_amount": float(commission),
                "premium_type": r[12],
            })

        return Response({
            "rows": data,
            "total": {
                "sa": float(total_sa),
                "premium": float(total_premium),
                "commission": float(total_commission)
            }
        })
