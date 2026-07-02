from django.core.cache import cache
from django.db import connections
from rest_framework.exceptions import AuthenticationFailed

from kycform.models import KycPolicy, KycUserInfo


class PolicyClientService:
    @staticmethod
    def user_policy_numbers(user_id):
        cache_key = f"policy:user_policies:{user_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        policies = list(
            KycPolicy.objects.filter(user_id=user_id).values_list("policy_number", flat=True)
        )
        cache.set(cache_key, policies, 300)
        return policies

    @staticmethod
    def get_client_no(user_id):
        cache_key = f"policy:client_no:{user_id}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        policy_numbers = PolicyClientService.user_policy_numbers(user_id)
        if not policy_numbers:
            raise AuthenticationFailed("NO_POLICY_LINKED")

        placeholders = ", ".join(["%s"] * len(policy_numbers))
        query = f"""
            SELECT TOP 1 tid.ClientNo
            FROM tblPolicyDetail tpd WITH (NOLOCK)
            INNER JOIN tblInsuredDetail tid WITH (NOLOCK)
                    ON tid.RegisterNo = tpd.RegisterNo
            WHERE tpd.PolicyNo IN ({placeholders})
              AND tid.ClientNo IS NOT NULL
        """

        with connections["sqlserver"].cursor() as cursor:
            cursor.execute(query, policy_numbers)
            row = cursor.fetchone()

        if not row:
            raise AuthenticationFailed("CLIENT_NOT_FOUND")

        client_no = row[0]
        cache.set(cache_key, client_no, 300)
        return client_no

    @staticmethod
    def get_kyc_status(user_id):
        cache_key = f"policy:kyc_status:{user_id}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        kyc_status = (
            KycUserInfo.objects.filter(user_id=user_id)
            .values_list("kyc_status", flat=True)
            .first()
        )
        if kyc_status is None:
            raise AuthenticationFailed("USER_NOT_FOUND")

        cache.set(cache_key, kyc_status, 300)
        return kyc_status
