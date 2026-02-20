from django.db import connections


class PolicyPaymentHistoryService:
    @staticmethod
    def get_payment_history(client_id):
        with connections["sqlserver"].cursor() as cursor:
            cursor.execute(
                """
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
                ORDER BY tpp.PaidDate DESC
                """,
                [client_id],
            )
            rows = cursor.fetchall()

        data = []
        total_paid_amount = 0
        total_premium = 0

        for row in rows:
            paid_amount = float(row[2] or 0)
            premium = float(row[3] or 0)

            total_paid_amount += paid_amount
            total_premium += premium

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

        return {
            "rows": data,
            "total": {
                "paid_amount": round(total_paid_amount, 2),
                "premium": round(total_premium, 2),
            },
        }
