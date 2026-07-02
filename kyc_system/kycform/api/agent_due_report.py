from django.db import connections
from rest_framework.views import APIView
from rest_framework.response import Response


class AgentDueReportAPIView(APIView):
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
                        i.FirstName + ISNULL(' ' + i.MiddleName,'') + ISNULL(' ' + i.LastName,'')
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
                    i.FirstName + ISNULL(' ' + i.MiddleName,'') + ISNULL(' ' + i.LastName,'')
                ) LIKE %s
            """
            params.append(f"%{name}%")

        count_sql = f"""
            SELECT COUNT(*)
            FROM tblPolicyDetail pd WITH (NOLOCK)
            INNER JOIN tblInsuredDetail i WITH (NOLOCK)
                    ON pd.RegisterNo = i.RegisterNo
            WHERE pd.AgentCode = %s
              AND pd.FUP < GETDATE()
              {search_filter}
        """

        with connections["sqlserver"].cursor() as cursor:
            cursor.execute(count_sql, params)
            total_rows = int((cursor.fetchone() or [0])[0] or 0)
            total_pages = (total_rows + page_size - 1) // page_size if total_rows else 0
            if total_pages and page > total_pages:
                page = total_pages
            offset = (page - 1) * page_size if total_rows else 0

            cursor.execute(
                f"""
                SELECT
                    ROW_NUMBER() OVER (ORDER BY pd.FUP ASC) AS SN,
                    pd.PolicyNo,
                    i.FirstName + ISNULL(' ' + i.MiddleName,'') + ISNULL(' ' + i.LastName,'') AS PolicyHolder,
                    pl.PlanName,
                    pd.Term,
                    pd.PayMode,
                    CONVERT(VARCHAR(10), pd.DOC, 103) AS DOC,
                    CAST(pd.Premium AS DECIMAL(16,0)) AS Premium,
                    0 AS LateFee,
                    CONVERT(VARCHAR(10), pd.FUP, 103) AS NextDueDate,
                    i.Mobile,
                    CASE
                        WHEN pd.CurrentStatus = 'L' THEN 'LAPSED'
                        ELSE 'DUE'
                    END AS PolicyStatus
                FROM tblPolicyDetail pd WITH (NOLOCK)
                INNER JOIN tblInsuredDetail i WITH (NOLOCK)
                        ON pd.RegisterNo = i.RegisterNo
                INNER JOIN tblPlan pl WITH (NOLOCK)
                        ON pd.PlanID = pl.PlanID
                WHERE pd.AgentCode = %s
                  AND pd.FUP < GETDATE()
                  {search_filter}
                ORDER BY pd.FUP ASC
                OFFSET %s ROWS
                FETCH NEXT %s ROWS ONLY
                """,
                [*params, offset, page_size],
            )

            rows = cursor.fetchall()

        data = []
        for r in rows:
            data.append(
                {
                    "sn": r[0],
                    "policy_no": r[1],
                    "policy_holder": r[2],
                    "plan": r[3],
                    "term": r[4],
                    "paymode": r[5],
                    "doc": r[6],
                    "premium": float(r[7]),
                    "late_fee": float(r[8]),
                    "next_due_date": r[9],
                    "mobile": r[10],
                    "status": r[11],
                }
            )

        return Response(
            {
                "rows": data,
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
