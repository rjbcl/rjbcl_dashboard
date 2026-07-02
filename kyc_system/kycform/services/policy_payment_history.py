from django.db import connections


class PolicyPaymentHistoryService:
    @staticmethod
    def get_payment_history(client_id, policy_no="", page=1, page_size=10, paginated=False):
        page = int(page or 1)
        page_size = int(page_size or 10)
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        if page_size > 100:
            page_size = 100

        policy_filter_sql = ""
        params = [client_id]
        if policy_no:
            policy_filter_sql = "AND tpp.PolicyNo LIKE %s"
            params.append(f"%{policy_no}%")

        with connections["sqlserver"].cursor() as cursor:
            if paginated:
                cursor.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM tblPremiumPaid tpp WITH (NOLOCK)
                    INNER JOIN tblPolicyDetail tpd WITH (NOLOCK)
                            ON tpd.PolicyNo = tpp.PolicyNo
                    INNER JOIN tblInsuredDetail tid WITH (NOLOCK)
                            ON tid.RegisterNo = tpd.RegisterNo
                    WHERE tid.ClientNo = %s
                    {policy_filter_sql}
                    """,
                    params,
                )
                total_rows = int((cursor.fetchone() or [0])[0] or 0)
                total_pages = (total_rows + page_size - 1) // page_size if total_rows else 0
                if total_pages and page > total_pages:
                    page = total_pages
                offset = (page - 1) * page_size if total_rows else 0
                pagination_sql = "OFFSET %s ROWS FETCH NEXT %s ROWS ONLY"
                query_params = [*params, offset, page_size]
            else:
                total_rows = 0
                total_pages = 0
                pagination_sql = ""
                query_params = params

            cursor.execute(
                f"""
                SELECT
                    ISNULL(SUM(tpp.PaidAmount), 0) AS TotalPaidAmount,
                    ISNULL(SUM(tpp.Premium), 0) AS TotalPremium
                FROM tblPremiumPaid tpp WITH (NOLOCK)
                INNER JOIN tblPolicyDetail tpd WITH (NOLOCK)
                        ON tpd.PolicyNo = tpp.PolicyNo
                INNER JOIN tblInsuredDetail tid WITH (NOLOCK)
                        ON tid.RegisterNo = tpd.RegisterNo
                WHERE tid.ClientNo = %s
                {policy_filter_sql}
                """,
                params,
            )
            total_row = cursor.fetchone() or (0, 0)

            cursor.execute(
                f"""
                SELECT
                    tpp.PolicyNo,
                    CONVERT(VARCHAR(10), tpp.PaidDate, 103) AS PremiumPaidDate,
                    tpp.PaidAmount,
                    tpp.Premium,
                    tpp.InstalmenType,
                    p.PlanName,
                    tpd.Term,
                    CONVERT(VARCHAR(10), tpd.FUP, 103) AS FUP,
                    tid.ClientNo,
                    tid.FirstName
                        + ISNULL(' ' + tid.MiddleName, '')
                        + ISNULL(' ' + tid.LastName, '') AS ClientName,
                    tpd.PayMode AS PolicyPremiumFrequency
                FROM tblPremiumPaid tpp WITH (NOLOCK)
                INNER JOIN tblPolicyDetail tpd WITH (NOLOCK)
                        ON tpd.PolicyNo = tpp.PolicyNo
                INNER JOIN tblInsuredDetail tid WITH (NOLOCK)
                        ON tid.RegisterNo = tpd.RegisterNo
                INNER JOIN tblPlan p WITH (NOLOCK)
                        ON p.PlanID = tpd.PlanID
                WHERE tid.ClientNo = %s
                {policy_filter_sql}
                ORDER BY tpp.PaidDate DESC
                {pagination_sql}
                """,
                query_params,
            )
            rows = cursor.fetchall()

        data = []

        for row in rows:
            paid_amount = float(row[2] or 0)
            premium = float(row[3] or 0)

            data.append(
                {
                    "policy_no": row[0],
                    "premium_paid_date": row[1],
                    "paid_amount": paid_amount,
                    "premium": premium,
                    "installment_type": row[4],
                    "plan_name": row[5],
                    "term": row[6],
                    "fup": row[7],
                    "client_id": row[8],
                    "client_name": row[9],
                    "policy_premium_frequency": row[10],
                }
            )

        if not paginated:
            total_rows = len(data)
            total_pages = 1 if total_rows else 0

        return {
            "rows": data,
            "total": {
                "paid_amount": round(float(total_row[0] or 0), 2),
                "premium": round(float(total_row[1] or 0), 2),
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
