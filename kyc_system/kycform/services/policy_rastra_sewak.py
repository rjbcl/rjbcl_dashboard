from django.db import connections

from kycform.models import Group


class PolicyRastraSewakService:
    @staticmethod
    def get_details(policy_no, dob):
        if "sqlserver" not in connections.databases:
            return {
                "rows": [],
                "total": 0,
                "detail": "CORE_DB_UNAVAILABLE",
            }

        try:
            allowed_group_ids = list(
                Group.objects.values_list("group_id", flat=True)
            )
        except Exception:
            allowed_group_ids = []

        if not allowed_group_ids:
            return {
                "rows": [],
                "total": 0,
                "detail": "NO_ALLOWED_GROUP_CONFIGURED",
            }

        placeholders = ", ".join(["%s"] * len(allowed_group_ids))

        query = f"""
            SELECT
                ge.PolicyNo,
                ge.RegisterNO,
                ge.Name AS PolicyHolderName,
                CONVERT(VARCHAR(10), ge.DOB, 23) AS DOB,
                LTRIM(RTRIM(COALESCE(CAST(ged.GroupID AS VARCHAR(50)), CAST(ge.GroupID AS VARCHAR(50))))) AS GroupID,
                COALESCE(ged.Branch, ge.Branch) AS Branch,
                CONVERT(VARCHAR(10), ge.DOC, 23) AS PolicyDOC,
                ge.Term AS PolicyTerm,
                ge.SumAssured AS PolicySumAssured,
                ge.Premium AS PolicyPremium,
                CONVERT(VARCHAR(10), ge.FUP, 23) AS PolicyFUP,
                CONVERT(VARCHAR(10), ge.MaturityDate, 23) AS PolicyMaturityDate,
                ge.PolicyStatus AS PolicyCurrentStatus,
                ge.PolicyType,
                ge.Remarks AS PolicyRemarks,
                CONVERT(VARCHAR(10), ged.PaidDate, 23) AS PaidDate,
                CONVERT(VARCHAR(10), ged.DOC, 23) AS ReceiptDOC,
                ged.Term AS PaidTerm,
                ged.SumAssured AS PaidSumAssured,
                ged.Premium AS PaidPremium,
                CONVERT(VARCHAR(10), ged.FUP, 23) AS PaidFUP,
                ged.Instalment,
                ged.PaidAmount,
                CONVERT(VARCHAR(10), ged.MaturityDate, 23) AS PaidMaturityDate,
                ged.PolicyStatus AS PaidPolicyStatus,
                ged.ClaimStatus,
                ged.Remarks AS PaymentRemarks
            FROM tblGroupEndowment ge WITH (NOLOCK)
            INNER JOIN tblGroupEndowmentDetails ged WITH (NOLOCK)
                ON ge.RegisterNO = ged.RegisterNO
            WHERE ge.PolicyNo = %s
              AND CAST(ge.DOB AS DATE) = CAST(%s AS DATE)
              AND LTRIM(RTRIM(COALESCE(CAST(ged.GroupID AS VARCHAR(50)), CAST(ge.GroupID AS VARCHAR(50))))) IN ({placeholders})
            ORDER BY ged.PaidDate DESC, ged.DOC DESC, ge.RegisterNO DESC
        """

        cleaned_group_ids = [str(gid).strip() for gid in allowed_group_ids]
        params = [policy_no, dob, *cleaned_group_ids]

        with connections["sqlserver"].cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        data = [
            {
                "policy_no": row[0],
                "register_no": row[1],
                "policy_holder_name": row[2],
                "dob": row[3],
                "group_id": row[4],
                "branch": row[5],
                "policy_doc": row[6],
                "policy_term": row[7],
                "policy_sum_assured": float(row[8] or 0),
                "policy_premium": float(row[9] or 0),
                "policy_fup": row[10],
                "policy_maturity_date": row[11],
                "policy_current_status": row[12],
                "policy_type": row[13],
                "policy_remarks": row[14],
                "paid_date": row[15],
                "receipt_doc": row[16],
                "paid_term": row[17],
                "paid_sum_assured": float(row[18] or 0),
                "paid_premium": float(row[19] or 0),
                "paid_fup": row[20],
                "instalment": row[21],
                "paid_amount": float(row[22] or 0),
                "paid_maturity_date": row[23],
                "paid_policy_status": row[24],
                "claim_status": row[25],
                "payment_remarks": row[26],
            }
            for row in rows
        ]

        return {
            "rows": data,
            "total": len(data),
        }
