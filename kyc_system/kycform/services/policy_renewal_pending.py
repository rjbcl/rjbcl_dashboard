from django.db import connections


class PolicyRenewalPendingService:
    @staticmethod
    def get_renewal_pending(client_id, policy_no="", page=1, page_size=10, paginated=False):
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
            policy_filter_sql = "AND pd.PolicyNo LIKE %s"
            params.append(f"%{policy_no}%")

        with connections["sqlserver"].cursor() as cursor:
            if paginated:
                cursor.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM tblPolicyDetail pd WITH (NOLOCK)
                    INNER JOIN tblInsuredDetail i WITH (NOLOCK)
                            ON i.RegisterNo = pd.RegisterNo
                    WHERE i.ClientNo = %s
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
                    ISNULL(SUM(CAST(pd.Premium AS DECIMAL(38, 0))), 0) AS TotalPremiumAmount,
                    ISNULL(SUM(CAST(pd.LateFineAmount AS DECIMAL(38, 0))), 0) AS TotalLateFee,
                    ISNULL(SUM(
                        CASE
                            WHEN pd.PayMode = 'Y' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 365.25) * pd.Premium
                            WHEN pd.PayMode = 'H' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 180.0) * pd.Premium
                            WHEN pd.PayMode = 'Q' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 90.0) * pd.Premium
                            WHEN pd.PayMode = 'M' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 30.0) * pd.Premium
                            ELSE CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 365.25) * pd.Premium
                        END
                    ), 0) AS TotalLapsedPremium,
                    ISNULL(SUM(
                        CASE
                            WHEN pd.PayMode = 'Y' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 365.25) * pd.Premium + CAST(pd.LateFineAmount AS DECIMAL(38, 0))
                            WHEN pd.PayMode = 'H' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 180.0) * pd.Premium + CAST(pd.LateFineAmount AS DECIMAL(38, 0))
                            WHEN pd.PayMode = 'Q' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 90.0) * pd.Premium + CAST(pd.LateFineAmount AS DECIMAL(38, 0))
                            WHEN pd.PayMode = 'M' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 30.0) * pd.Premium + CAST(pd.LateFineAmount AS DECIMAL(38, 0))
                            ELSE CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 365.25) * pd.Premium + CAST(pd.LateFineAmount AS DECIMAL(38, 0))
                        END
                    ), 0) AS TotalAmount
                FROM tblPolicyDetail pd WITH (NOLOCK)
                INNER JOIN tblInsuredDetail i WITH (NOLOCK)
                        ON i.RegisterNo = pd.RegisterNo
                WHERE i.ClientNo = %s
                {policy_filter_sql}
                """,
                params,
            )
            totals_row = cursor.fetchone() or (0, 0, 0, 0)

            cursor.execute(
                f"""
                SELECT
                    pd.PolicyNo,
                    i.ClientNo,
                    pd.AgentCode,
                    CONVERT(VARCHAR(10), pd.FUP, 103) AS RenewalDeadlineDate,
                    p.PlanName AS ProductName,
                    CAST(pd.Premium AS DECIMAL(38, 0)) AS PremiumAmount,
                    p.PlanName AS PlanName,
                    p.PlanId,
                    CONVERT(VARCHAR(10), pd.DOC, 103) AS PolicyCreatedDate,
                    pd.Term,
                    pd.PayMode AS PolicyPremiumFrequency,
                    CAST(pd.LateFineAmount AS DECIMAL(38, 0)) AS LateFee,
                    i.Mobile,
                    i.FirstName
                        + ISNULL(' ' + i.MiddleName + ' ', ' ')
                        + i.LastName AS PolicyHolderName,
                    DATEDIFF(day, pd.FUP, GETDATE()) AS DaysElapsedSinceLastDueDate,
                    pd.CurrentStatus AS Status,
                    CASE
                        WHEN pd.PayMode = 'Y' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 365.25)
                        WHEN pd.PayMode = 'H' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 180.0)
                        WHEN pd.PayMode = 'Q' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 90.0)
                        WHEN pd.PayMode = 'M' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 30.0)
                        ELSE CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 365.25)
                    END AS LapsedInstallments,
                    CASE
                        WHEN pd.PayMode = 'Y' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 365.25) * pd.Premium
                        WHEN pd.PayMode = 'H' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 180.0) * pd.Premium
                        WHEN pd.PayMode = 'Q' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 90.0) * pd.Premium
                        WHEN pd.PayMode = 'M' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 30.0) * pd.Premium
                        ELSE CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 365.25) * pd.Premium
                    END AS LapsedPremium,
                    CASE
                        WHEN pd.PayMode = 'Y' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 365.25) * pd.Premium + CAST(pd.LateFineAmount AS DECIMAL(38, 0))
                        WHEN pd.PayMode = 'H' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 180.0) * pd.Premium + CAST(pd.LateFineAmount AS DECIMAL(38, 0))
                        WHEN pd.PayMode = 'Q' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 90.0) * pd.Premium + CAST(pd.LateFineAmount AS DECIMAL(38, 0))
                        WHEN pd.PayMode = 'M' THEN CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 30.0) * pd.Premium + CAST(pd.LateFineAmount AS DECIMAL(38, 0))
                        ELSE CEILING(DATEDIFF(day, pd.FUP, GETDATE()) / 365.25) * pd.Premium + CAST(pd.LateFineAmount AS DECIMAL(38, 0))
                    END AS TotalAmount
                FROM tblPolicyDetail pd WITH (NOLOCK)
                INNER JOIN tblPlan p
                        ON p.PlanID = pd.PlanID
                INNER JOIN tblInsuredDetail i
                        ON i.RegisterNo = pd.RegisterNo
                WHERE i.ClientNo = %s
                {policy_filter_sql}
                ORDER BY pd.FUP ASC
                {pagination_sql}
                """,
                query_params,
            )
            rows = cursor.fetchall()

        data = []

        for row in rows:
            premium_amount = float(row[5] or 0)
            late_fee = float(row[11] or 0)
            lapsed_premium = float(row[17] or 0)
            row_total_amount = float(row[18] or 0)

            data.append(
                {
                    "policy_no": row[0],
                    "client_id": row[1],
                    "agent_code": row[2],
                    "renewal_deadline_date": row[3],
                    "product_name": row[4],
                    "premium_amount": premium_amount,
                    "plan_name": row[6],
                    "plan_id": row[7],
                    "policy_created_date": row[8],
                    "term": row[9],
                    "policy_premium_frequency": row[10],
                    "late_fee": late_fee,
                    "mobile": row[12],
                    "policy_holder_name": row[13],
                    "days_elapsed_since_last_due_date": int(row[14] or 0),
                    "status": row[15],
                    "lapsed_installments": int(row[16] or 0),
                    "lapsed_premium": lapsed_premium,
                    "total_amount": row_total_amount,
                }
            )

        if not paginated:
            total_rows = len(data)
            total_pages = 1 if total_rows else 0

        return {
            "rows": data,
            "total": {
                "premium_amount": round(float(totals_row[0] or 0), 2),
                "late_fee": round(float(totals_row[1] or 0), 2),
                "lapsed_premium": round(float(totals_row[2] or 0), 2),
                "total_amount": round(float(totals_row[3] or 0), 2),
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
