from django.db import connections
from rest_framework.response import Response
from rest_framework.views import APIView


class AgentBusinessReportAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        agent_code = request.session.get("agent_code")
        if not agent_code:
            return Response({"detail": "Agent not authenticated"}, status=401)

        policy_no = request.GET.get("policy_no", "").strip()
        name = request.GET.get("name", "").strip()

        try:
            page = int(request.GET.get("page", "1") or 1)
        except ValueError:
            page = 1
        try:
            page_size = int(request.GET.get("page_size", "10") or 10)
        except ValueError:
            page_size = 10
        try:
            limit = int(request.GET.get("limit", "0") or 0)
        except ValueError:
            limit = 0
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

        count_sql = f"""
            SELECT COUNT(*)
            FROM tblPolicyDetail p WITH (NOLOCK)
            INNER JOIN tblInsuredDetail i WITH (NOLOCK)
                    ON p.Registerno = i.Registerno
            WHERE p.AgentCode = %s
            {search_filter}
        """

        total_sql = f"""
            SELECT
                ISNULL(SUM(CAST(p.SA AS MONEY)), 0) AS TotalSA,
                ISNULL(SUM(CAST(p.Premium AS MONEY)), 0) AS TotalPremium
            FROM tblPolicyDetail p WITH (NOLOCK)
            INNER JOIN tblInsuredDetail i WITH (NOLOCK)
                    ON p.Registerno = i.Registerno
            WHERE p.AgentCode = %s
            {search_filter}
        """

        with connections["sqlserver"].cursor() as cursor:
            cursor.execute(count_sql, params)
            total_rows = int((cursor.fetchone() or [0])[0] or 0)
            total_pages = (total_rows + page_size - 1) // page_size if total_rows else 0
            if total_pages and page > total_pages:
                page = total_pages

            cursor.execute(total_sql, params)
            total_row = cursor.fetchone() or (0, 0)
            overall_sa = float(total_row[0] or 0)
            overall_premium = float(total_row[1] or 0)

            if limit > 0:
                cursor.execute(
                    f"""
                    SELECT
                        TOP {min(limit, 500)}
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
                    """,
                    params,
                )
            else:
                offset = (page - 1) * page_size if total_rows else 0
                cursor.execute(
                    f"""
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
                    OFFSET %s ROWS
                    FETCH NEXT %s ROWS ONLY
                    """,
                    [*params, offset, page_size],
                )

            rows = cursor.fetchall()

        data = []
        for r in rows:
            sa = float(r[7] or 0)
            premium = float(r[8] or 0)

            data.append(
                {
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
                    "premium_type": r[10],
                }
            )

        return Response(
            {
                "rows": data,
                "total": {
                    "sa": round(overall_sa, 2),
                    "premium": round(overall_premium, 2),
                },
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_rows": total_rows,
                    "total_pages": total_pages,
                    "has_next": bool(total_pages and page < total_pages),
                    "has_prev": bool(total_pages and page > 1),
                },
            }
        )
