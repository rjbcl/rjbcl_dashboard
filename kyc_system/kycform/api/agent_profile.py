from django.db import connections
from rest_framework.views import APIView
from rest_framework.response import Response


class AgentProfileAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        agent_code = request.session.get("agent_code")
        if not agent_code:
            return Response({"detail": "Agent not authenticated"}, status=401)

        with connections["sqlserver"].cursor() as cursor:
            cursor.execute("""
                SELECT
                    a.AgentCode,
                    a.FirstName,
                    a.MiddleName,
                    a.LastName,
                    CONVERT(VARCHAR(10), a.DOB, 103) AS DOB,
                    a.MobileNo1,
                    a.Address,
                    a.LicenseNo,
                    CONVERT(VARCHAR(10), a.LicenseIssueDate, 103) AS LicenseIssueDate,
                    CONVERT(VARCHAR(10), a.LicenseExpiryDate, 103) AS LicenseExpiryDate,
                    a.IsActive,
                    a.BankAcNo,
                    b.BankName
                FROM tblAgent a WITH (NOLOCK)
                LEFT JOIN tblInv_Company b WITH (NOLOCK)
                       ON a.BankCode = b.BankCode
                WHERE LTRIM(RTRIM(a.AgentCode)) = %s
            """, [agent_code])

            row = cursor.fetchone()

        if not row:
            return Response({"detail": "Agent not found"}, status=404)

        full_name = " ".join(
            part for part in [row[1], row[2], row[3]] if part
        )

        data = {
            "agent": {
                "code": row[0],
                "name": full_name,
                "dob": row[4],
                "mobile": row[5],
                "address": row[6],
                "license_no": row[7],
                "license_issue": row[8],
                "license_expiry": row[9],
                "is_active": bool(row[10]),
                "bank_name": row[12] or "—",
                "bank_account": row[11] or "—"
            }
        }

        return Response(data)
