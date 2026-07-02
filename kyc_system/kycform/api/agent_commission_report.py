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
        try:
            page = int(request.GET.get("page", "1") or 1)
        except ValueError:
            page = 1
        try:
            page_size = int(request.GET.get("page_size", "10") or 10)
        except ValueError:
            page_size = 10
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 100:
            page_size = 100

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

        count_sql = f"""
            SELECT COUNT(*)
            FROM tblPolicyDetail pd WITH (NOLOCK)
            INNER JOIN tblInsuredDetail i WITH (NOLOCK)
                    ON i.RegisterNo = pd.RegisterNo
            INNER JOIN tblPremiumPaid pz WITH (NOLOCK)
                    ON pd.PolicyNo = pz.PolicyNo
            WHERE pd.AgentCode = %s
            {search_filter}
        """

        total_sql = f"""
            SELECT
                CAST(ISNULL(SUM(pd.SA), 0) AS DECIMAL(18,0)) AS TotalSA,
                CAST(ISNULL(SUM(pd.Premium), 0) AS DECIMAL(18,0)) AS TotalPremium,
                CAST(ISNULL(SUM(ISNULL(pz.CommAmount, 0)), 0) AS DECIMAL(18,0)) AS TotalCommission
            FROM tblPolicyDetail pd WITH (NOLOCK)
            INNER JOIN tblInsuredDetail i WITH (NOLOCK)
                    ON i.RegisterNo = pd.RegisterNo
            INNER JOIN tblPremiumPaid pz WITH (NOLOCK)
                    ON pd.PolicyNo = pz.PolicyNo
            WHERE pd.AgentCode = %s
            {search_filter}
        """

        with connections["sqlserver"].cursor() as cursor:
            cursor.execute(count_sql, params)
            total_rows = int((cursor.fetchone() or [0])[0] or 0)
            total_pages = (total_rows + page_size - 1) // page_size if total_rows else 0
            if total_pages and page > total_pages:
                page = total_pages
            offset = (page - 1) * page_size if total_rows else 0

            cursor.execute(total_sql, params)
            total_row = cursor.fetchone() or (0, 0, 0)

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
                OFFSET %s ROWS
                FETCH NEXT %s ROWS ONLY
            """, [*params, offset, page_size])

            rows = cursor.fetchall()

        data = []

        for r in rows:
            sa = r[8] or 0
            premium = r[9] or 0
            commission = r[11] or 0

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
                "sa": float(total_row[0] or 0),
                "premium": float(total_row[1] or 0),
                "commission": float(total_row[2] or 0)
            },
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_rows": total_rows,
                "total_pages": total_pages,
                "has_next": bool(total_pages and page < total_pages),
                "has_prev": bool(total_pages and page > 1),
            },
        })
