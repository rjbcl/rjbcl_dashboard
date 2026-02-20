from django.db import connections


class PolicyRenewalPendingService:
    @staticmethod
    def get_renewal_pending(client_id):
        with connections["sqlserver"].cursor() as cursor:
            cursor.execute(
                """
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
                ORDER BY pd.FUP ASC
                """,
                [client_id],
            )
            rows = cursor.fetchall()

        data = []
        total_premium_amount = 0
        total_late_fee = 0
        total_lapsed_premium = 0
        total_amount = 0

        for row in rows:
            premium_amount = float(row[5] or 0)
            late_fee = float(row[11] or 0)
            lapsed_premium = float(row[17] or 0)
            row_total_amount = float(row[18] or 0)

            total_premium_amount += premium_amount
            total_late_fee += late_fee
            total_lapsed_premium += lapsed_premium
            total_amount += row_total_amount

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

        return {
            "rows": data,
            "total": {
                "premium_amount": round(total_premium_amount, 2),
                "late_fee": round(total_late_fee, 2),
                "lapsed_premium": round(total_lapsed_premium, 2),
                "total_amount": round(total_amount, 2),
            },
        }
