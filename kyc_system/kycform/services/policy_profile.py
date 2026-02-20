from django.db import connections
from rest_framework.exceptions import AuthenticationFailed

from kycform.models import KycPolicy, KycUserInfo
from .policy_client import PolicyClientService


class PolicyProfileService:
    @staticmethod
    def get_profile(user_id):
        policies = list(
            KycPolicy.objects.filter(user_id=user_id).values_list("policy_number", flat=True)
        )

        user = (
            KycUserInfo.objects.filter(user_id=user_id)
            .values(
                "user_id",
                "first_name",
                "middle_name",
                "last_name",
                "dob",
                "phone_number",
                "email",
                "kyc_status",
            )
            .first()
        )
        if not user:
            return None

        client_id = None
        bank_account = "-"
        bank_name = "-"

        try:
            client_id = PolicyClientService.get_client_no(user_id)
        except AuthenticationFailed:
            client_id = None

        if client_id:
            with connections["sqlserver"].cursor() as cursor:
                cursor.execute(
                    """
                    SELECT TOP 1
                        k.BankAcNo,
                        k.BankName
                    FROM tblKYCDetails k WITH (NOLOCK)
                    WHERE LTRIM(RTRIM(k.ClientNo)) = %s
                    """,
                    [client_id],
                )
                bank_row = cursor.fetchone()

            if bank_row:
                bank_account = bank_row[0] or "-"
                bank_name = bank_row[1] or "-"

        full_name = " ".join(
            part
            for part in [user["first_name"], user["middle_name"], user["last_name"]]
            if part
        )

        return {
            "policy_holder": {
                "policies": policies,
                "client_id": client_id,
                "name": full_name,
                "dob": str(user["dob"]) if user["dob"] else None,
                "mobile": user["phone_number"],
                "email": user["email"],
                "kyc_status": user["kyc_status"],
                "bank_name": bank_name,
                "bank_account": bank_account,
            }
        }
