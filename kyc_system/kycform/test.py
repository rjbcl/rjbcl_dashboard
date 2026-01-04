from datetime import date, timedelta
import json

from django.test import TestCase
from django.utils import timezone
from django.db import connection

from kycform.models import (
    KycUserInfo,
    KycPolicy,
    KycSubmission,
    KycDocument,
    KYCTemporary,
    KycChangeLog,
    KycMobileOTP,
)

# ================================================================
# MIXIN FOR UNMANAGED kyc_policy TABLE
# ================================================================

class UnmanagedPolicyTableMixin:
    """
    Creates unmanaged kyc_policy table for test database only.
    Required because KycPolicy.managed = False
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS kyc_policy (
                    policy_number VARCHAR(50) PRIMARY KEY,
                    user_id VARCHAR(50),
                    created_at DATE
                )
                """
            )

    @classmethod
    def tearDownClass(cls):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS kyc_policy")
        super().tearDownClass()


# ================================================================
# KycUserInfo Tests
# ================================================================

class KycUserInfoTest(TestCase):

    def setUp(self):
        self.user = KycUserInfo.objects.create(
            user_id="CUS001",
            first_name="Anita",
            last_name="Shrestha",
            dob=date(1990, 5, 10),
            phone_number="9812345678",
        )

    def test_user_created(self):
        self.assertEqual(self.user.kyc_status, "NOT_INITIATED")
        self.assertFalse(self.user.mobile_verified)

    def test_user_str(self):
        self.assertEqual(str(self.user), "CUS001 - Anita Shrestha")

    def test_mobile_verified_flag(self):
        self.user.mobile_verified = True
        self.user.save()
        self.assertTrue(
            KycUserInfo.objects.get(user_id="CUS001").mobile_verified
        )


# ================================================================
# KycSubmission Tests
# ================================================================

class KycSubmissionTest(TestCase):

    def setUp(self):
        self.user = KycUserInfo.objects.create(
            user_id="CUS002",
            first_name="Ramesh",
            last_name="Karki",
            dob=date(1988, 1, 1),
        )

        self.submission = KycSubmission.objects.create(
            user=self.user,
            mobile="9800000000",
            is_pep=False,
            is_aml=False,
        )

    def test_submission_created(self):
        self.assertEqual(self.submission.user, self.user)
        self.assertEqual(self.submission.version, 1)

    def test_one_submission_per_user(self):
        with self.assertRaises(Exception):
            KycSubmission.objects.create(user=self.user)

    def test_lock_flag(self):
        self.submission.is_lock = True
        self.submission.save()
        self.assertTrue(
            KycSubmission.objects.get(user=self.user).is_lock
        )

    def test_data_json_storage(self):
        self.submission.data_json = {"mobile": "9800000000"}
        self.submission.save()
        self.assertEqual(self.submission.data_json["mobile"], "9800000000")


# ================================================================
# KYCTemporary Tests
# ================================================================

class KYCTemporaryTest(TestCase):

    def setUp(self):
        self.user = KycUserInfo.objects.create(
            user_id="CUS003",
            first_name="Bimal",
            last_name="Rana",
            dob=date(1992, 3, 3),
        )

        self.temp = KYCTemporary.objects.create(
            user=self.user,
            policy_no="POL123",
            data_json={"mobile": "9811111111"},
        )

    def test_temp_created(self):
        self.assertEqual(self.temp.policy_no, "POL123")

    def test_one_temp_per_user(self):
        with self.assertRaises(Exception):
            KYCTemporary.objects.create(
                user=self.user,
                policy_no="POL999",
            )

    def test_temp_json_persistence(self):
        self.assertEqual(self.temp.data_json["mobile"], "9811111111")


# ================================================================
# KycDocument Tests
# ================================================================

class KycDocumentTest(TestCase):

    def setUp(self):
        self.user = KycUserInfo.objects.create(
            user_id="CUS004",
            first_name="Sita",
            last_name="Thapa",
            dob=date(1995, 2, 2),
        )

        self.submission = KycSubmission.objects.create(user=self.user)

        self.doc = KycDocument.objects.create(
            user=self.user,
            submission=self.submission,
            doc_type="PHOTO",
            file_name="photo.jpg",
        )

    def test_document_created(self):
        self.assertEqual(self.doc.doc_type, "PHOTO")
        self.assertTrue(self.doc.is_current)

    def test_document_url_safe(self):
        self.assertIsNone(self.doc.url)


# ================================================================
# KycMobileOTP Tests
# ================================================================

class KycMobileOTPTest(TestCase):

    def setUp(self):
        self.user = KycUserInfo.objects.create(
            user_id="CUS005",
            first_name="Hari",
            last_name="Adhikari",
            dob=date(1980, 4, 4),
        )

        self.otp = KycMobileOTP.objects.create(
            kyc_user=self.user,
            mobile="9801234567",
            otp_hash="hashed",
            expires_at=timezone.now() + timedelta(minutes=2),
        )

    def test_otp_not_expired(self):
        self.assertFalse(self.otp.is_expired())

    def test_otp_expired(self):
        self.otp.expires_at = timezone.now() - timedelta(minutes=1)
        self.otp.save()
        self.assertTrue(self.otp.is_expired())

    def test_otp_verified_flag(self):
        self.otp.is_verified = True
        self.otp.save()
        self.assertTrue(
            KycMobileOTP.objects.get(id=self.otp.id).is_verified
        )


# ================================================================
# KycChangeLog Tests
# ================================================================

class KycChangeLogTest(TestCase):

    def setUp(self):
        self.user = KycUserInfo.objects.create(
            user_id="CUS006",
            first_name="Nabin",
            last_name="Shah",
            dob=date(1991, 6, 6),
        )

        self.submission = KycSubmission.objects.create(user=self.user)

        self.log = KycChangeLog.objects.create(
            submission=self.submission,
            action="UPDATE",
            actor_type="USER",
            field_name="mobile",
            old_value="9800000000",
            new_value="9811111111",
        )

    def test_changelog_created(self):
        self.assertEqual(self.log.action, "UPDATE")

    def test_changelog_str(self):
        self.assertIn(self.submission.user.user_id, str(self.log))


# ================================================================
# MOBILE OTP → SUBMISSION FLOW TEST
# ================================================================

class MobileOtpPersistenceTest(UnmanagedPolicyTableMixin, TestCase):

    def setUp(self):
        self.user = KycUserInfo.objects.create(
            user_id="U1001",
            first_name="Ram",
            last_name="Sharma",
            dob="1990-01-01",
            phone_number=None,
            mobile_verified=False,
        )

        self.policy = KycPolicy.objects.create(
            policy_number="POL123",
            user_id=self.user.user_id,
            created_at=timezone.now().date(),
        )

        session = self.client.session
        session["authenticated"] = True
        session["policy_no"] = self.policy.policy_number
        session.save()

    def test_mobile_otp_to_submission_flow(self):
        """
        OTP verify → save & continue → submit → mobile persists everywhere
        """

        otp = KycMobileOTP.objects.create(
            kyc_user=self.user,
            mobile="9812345678",
            otp_hash="dummy",
            expires_at=timezone.now() + timedelta(minutes=5),
        )

        self.user.mobile_verified = True
        self.user.phone_number = otp.mobile
        self.user.save()

        payload = {
            "mobile": "9812345678",
            "first_name": "Ram",
        }

        response = self.client.post(
            "/save-progress/",
            {
                "policy_no": self.policy.policy_number,
                "kyc_data": json.dumps(payload),
            },
        )
        self.assertEqual(response.status_code, 200)

        temp = KYCTemporary.objects.get(user=self.user)
        self.assertEqual(temp.data_json["mobile"], "9812345678")

        session = self.client.session
        session["mobile_otp_verified"] = True
        session.save()

        response = self.client.post(
            "/kyc-submit/",
            {
                "policy_no": self.policy.policy_number,
                "kyc_data": json.dumps(payload),
            },
        )
        self.assertEqual(response.status_code, 302)

        submission = KycSubmission.objects.get(user=self.user)
        self.assertEqual(submission.mobile, "9812345678")
        self.assertTrue(self.user.mobile_verified)


# ================================================================
# VERIFIED MOBILE OVERWRITE PROTECTION
# ================================================================

class VerifiedMobileOverwriteProtectionTest(UnmanagedPolicyTableMixin, TestCase):

    def setUp(self):
        self.user = KycUserInfo.objects.create(
            user_id="U2001",
            first_name="Secure",
            last_name="User",
            dob="1991-01-01",
            phone_number="9800000000",
            mobile_verified=True,
        )

        KycPolicy.objects.create(
            policy_number="POL2001",
            user_id=self.user.user_id,
            created_at=timezone.now().date(),
        )

    def test_temp_data_cannot_clear_verified_mobile(self):
        KYCTemporary.objects.update_or_create(
            user=self.user,
            defaults={
                "policy_no": "POL2001",
                "data_json": {"mobile": ""},
            },
        )

        user = KycUserInfo.objects.get(user_id=self.user.user_id)
        self.assertEqual(user.phone_number, "9800000000")

    def test_submission_cannot_override_verified_mobile(self):
        submission = KycSubmission.objects.create(
            user=self.user,
            mobile="9811111111",
        )

        submission.refresh_from_db()
        user = KycUserInfo.objects.get(user_id=self.user.user_id)

        self.assertEqual(user.phone_number, "9800000000")
        self.assertNotEqual(submission.mobile, "9811111111")
