from django.db import connections
from rest_framework.views import APIView
from rest_framework.response import Response


class AgentHierarchyAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        agent_code = request.session.get("agent_code")
        if not agent_code:
            return Response({"rows": []})

        superior_code = f"AM{agent_code}"

        with connections["sqlserver"].cursor() as cursor:
            cursor.execute("""
                SELECT
                    ROW_NUMBER() OVER (ORDER BY a.AgentCode) AS SN,
                    a.AgentCode,
                    a.FirstName + ISNULL(' ' + a.LastName,'') AS AgentName,
                    a.MobileNo2,
                    a.[Address],
                    CASE
                        WHEN a.IsActive = 1 AND a.LicenseExpiryDate > GETDATE()
                        THEN 'ACTIVE'
                        ELSE 'INACTIVE'
                    END AS LicenseStatus
                FROM tblAgentUnderSuperior u
                INNER JOIN tblAgent a
                        ON a.AgentCode = u.AgentCode
                WHERE u.SuperiorCode = %s
            """, [superior_code])

            rows = cursor.fetchall()

        data = []
        for r in rows:
            data.append({
                "sn": r[0],
                "agent_code": r[1],
                "agent_name": r[2],
                "mobile": r[3],
                "address": r[4],
                "license_status": r[5],
            })

        return Response({"rows": data})
