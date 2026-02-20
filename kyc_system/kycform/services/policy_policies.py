from django.db import connections


class PolicyPoliciesService:
    @staticmethod
    def get_policies(client_id):
        with connections["sqlserver"].cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    tpd.PolicyNo AS PolicyNumber,
                    tp.PlanName,
                    tpd.PlanID AS ProductCode,
                    tpd.Term,
                    CONVERT(NVARCHAR, tpd.DOC, 23) AS PolicyCreatedDate,
                    tid.ClientNo AS ClientId,
                    CONCAT(tid.FirstName, ' ', ISNULL(tid.MiddleName, ''), ' ', tid.LastName) AS ClientName,
                    tid.Mobile AS ClientMobile,
                    tid.Mobile AS ClientContactNumber,
                    tid.Email AS ClientEmail,
                    tid.TempAddress AS ClientAddress,
                    tid.FirstName AS ProposerFirstName,
                    tid.MiddleName AS ProposerMiddleName,
                    tid.LastName AS ProposerLastName,
                    tid.DOB AS ProposerDob,
                    tpd.SA AS PolicySumAssured,
                    tpd.Premium AS PolicyPremium,
                    tpd.PayMode AS PolicyPremiumFrequency,
                    tpd.MaturityDate AS PolicyMaturityDate,
                    tpd.FUP AS PolicyPremiumNextDueDate,
                    CONVERT(NVARCHAR, dbo.func_PreviousFUPDate(tpd.FUP, tpd.PayMode), 23) AS PolicyPremiumLastPaidDate,
                    tpd.CurrentStatus AS CurrentStatusCode,
                    ISNULL(NULLIF(LTRIM(RTRIM(tsdv.[Value])), ''), tpd.CurrentStatus) AS CurrentStatusText
                FROM dbo.tblPolicyDetail tpd WITH (NOLOCK)
                INNER JOIN dbo.tblInsuredDetail tid WITH (NOLOCK)
                        ON tid.RegisterNo = tpd.RegisterNo
                INNER JOIN dbo.tblPlan tp WITH (NOLOCK)
                        ON tp.PlanID = tpd.PlanID
                LEFT JOIN dbo.tblStaticDataValue tsdv WITH (NOLOCK)
                        ON LTRIM(RTRIM(tsdv.Code)) = LTRIM(RTRIM(tpd.CurrentStatus))
                       AND LTRIM(RTRIM(tsdv.StaticCode)) = 'CurrentStatus'
                WHERE tid.ClientNo = %s
                ORDER BY tpd.DOC DESC
                """,
                [client_id],
            )
            rows = cursor.fetchall()

        data = []
        for row in rows:
            data.append(
                {
                    "policy_number": row[0],
                    "plan_name": row[1],
                    "product_code": row[2],
                    "term": row[3],
                    "policy_created_date": row[4],
                    "client_id": row[5],
                    "client_name": " ".join((row[6] or "").split()),
                    "client_mobile": row[7],
                    "client_contact_number": row[8],
                    "client_email": row[9],
                    "client_address": row[10],
                    "proposer_first_name": row[11],
                    "proposer_middle_name": row[12],
                    "proposer_last_name": row[13],
                    "proposer_dob": row[14],
                    "policy_sum_assured": float(row[15] or 0),
                    "policy_premium": float(row[16] or 0),
                    "policy_premium_frequency": row[17],
                    "policy_maturity_date": row[18],
                    "policy_premium_next_due_date": row[19],
                    "policy_premium_last_paid_date": row[20],
                    "current_status_code": row[21],
                    "current_status": row[22],
                }
            )

        return {"rows": data}
