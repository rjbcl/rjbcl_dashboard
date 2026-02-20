from django.db import connections
from rest_framework.views import APIView
from rest_framework.response import Response


class AgentSummaryAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        agent_code = request.session.get("agent_code")  # e.g. 30000808
        if not agent_code:
            return Response({"detail": "Agent not authenticated"}, status=401)


        # =====================================================
        # 1️⃣ DOWNLINE AGENT COUNT (LEVEL-1, ACTIVE)
        # =====================================================
        with connections["sqlserver"].cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(DISTINCT u.AgentCode)
                FROM tblAgentUnderSuperior u
                INNER JOIN tblAgentSuperior s
                        ON u.SuperiorCode = s.SuperiorCode
                INNER JOIN tblAgent a
                        ON a.AgentCode = u.AgentCode
                WHERE s.PersonalAgentCode = %s
                  AND a.IsActive = 1
                  AND a.LicenseExpiryDate > GETDATE()
            """, [agent_code])

            downline_count = cursor.fetchone()[0] or 0

        # =====================================================
        # 2️⃣ POLICY COUNTS
        # =====================================================
        with connections["sqlserver"].cursor() as cursor:

            # SELF
            cursor.execute("""
                SELECT COUNT(*)
                FROM tblPolicyDetail
                WHERE AgentCode = %s
            """, [agent_code])
            self_policy = cursor.fetchone()[0] or 0

            # DOWNLINE
            cursor.execute("""
                SELECT COUNT(*)
                FROM tblPolicyDetail
                WHERE AgentCode IN (
                    SELECT u.AgentCode
                    FROM tblAgentUnderSuperior u
                    INNER JOIN tblAgentSuperior s
                            ON u.SuperiorCode = s.SuperiorCode
                    WHERE s.PersonalAgentCode = %s
                )
            """, [agent_code])
            downline_policy = cursor.fetchone()[0] or 0

        total_policy = self_policy + downline_policy

        # =====================================================
        # 3️⃣ PREMIUM + COMMISSION
        # =====================================================
        with connections["sqlserver"].cursor() as cursor:

            # SELF
            cursor.execute("""
                SELECT
                    ISNULL(SUM(pd.Premium),0),
                    ISNULL(SUM(pp.CommAmount),0)
                FROM tblPolicyDetail pd
                INNER JOIN tblPremiumPaid pp
                        ON pd.PolicyNo = pp.PolicyNo
                WHERE pd.AgentCode = %s
            """, [agent_code])

            self_premium, self_commission = cursor.fetchone()

            # DOWNLINE
            cursor.execute("""
                SELECT
                    ISNULL(SUM(pd.Premium),0),
                    ISNULL(SUM(pp.CommAmount),0)
                FROM tblPolicyDetail pd
                INNER JOIN tblPremiumPaid pp
                        ON pd.PolicyNo = pp.PolicyNo
                WHERE pd.AgentCode IN (
                    SELECT u.AgentCode
                    FROM tblAgentUnderSuperior u
                    INNER JOIN tblAgentSuperior s
                            ON u.SuperiorCode = s.SuperiorCode
                    WHERE s.PersonalAgentCode = %s
                )
            """, [agent_code])

            downline_premium, downline_commission = cursor.fetchone()

        total_premium = self_premium + downline_premium
        total_commission = self_commission + downline_commission

        # =====================================================
        # 4️⃣ MONTHLY CHART (Premium + Commission)
        # =====================================================
        with connections["sqlserver"].cursor() as cursor:
            cursor.execute("""
                SELECT
                    DATENAME(MONTH, pp.PaidDate) AS MonthName,
                    MONTH(pp.PaidDate)           AS MonthNo,
                    SUM(pd.Premium)              AS Premium,
                    SUM(pp.CommAmount)           AS Commission
                FROM tblPolicyDetail pd
                INNER JOIN tblPremiumPaid pp
                        ON pd.PolicyNo = pp.PolicyNo
                WHERE pd.AgentCode = %s
                GROUP BY MONTH(pp.PaidDate), DATENAME(MONTH, pp.PaidDate)
                ORDER BY MonthNo
            """, [agent_code])

            chart_rows = cursor.fetchall()

        chart_labels = []
        chart_premium = []
        chart_commission = []

        for row in chart_rows:
            chart_labels.append(row[0])
            chart_premium.append(float(row[2] or 0))
            chart_commission.append(float(row[3] or 0))

        # =====================================================
        # ✅ FINAL RESPONSE (UI-COMPATIBLE)
        # =====================================================
        return Response({
            "kpi": {
                "policies": {
                    "total": total_policy,
                    "self": self_policy,
                    "downline": downline_policy
                },
                "premium": {
                    "total": round(total_premium, 2),
                    "self": round(self_premium, 2),
                    "downline": round(downline_premium, 2)
                },
                "downline": {
                    "count": downline_count
                },
            },
            "summary": {
                "policies": total_policy,
                "premium": round(total_premium, 2),
                "commission": round(total_commission, 2)
            },
            "chart": {
                "labels": chart_labels,
                "premium": chart_premium,
                "commission": chart_commission
            }
        })
