# kycform/models.py

from django.db import models
from django.utils import timezone


# ================================================================
# MAIN USER MODEL (LOGIN + BASIC ACCOUNT DETAILS)
# ================================================================
class KycUserInfo(models.Model):

    KYC_STATUS_CHOICES = [
        ("NOT_INITIATED", "Not Initiated"),
        ("PENDING", "Pending"),
        ("INCOMPLETE", "Incomplete"),
        ("VERIFIED", "Verified"),
        ("REJECTED", "Rejected"),
    ]

    user_id = models.CharField(max_length=50, primary_key=True)
    
    # Login credentials
    password = models.CharField(max_length=100, null=True, blank=True)

    # Basic identity
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100)
    full_name_nep = models.CharField(max_length=200, null=True, blank=True)

    dob = models.DateField()
    email = models.CharField(max_length=200, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)

    # Status
    kyc_status = models.CharField(
        max_length=20, choices=KYC_STATUS_CHOICES, default="NOT_INITIATED"
    )

    class Meta:
        db_table = "kyc_user_info"

    def __str__(self):
        return f"{self.user_id} - {self.first_name} {self.last_name}"


# ================================================================
# POLICY TABLE (USER → MULTIPLE POLICIES)
# ================================================================
class KycPolicy(models.Model):
    policy_number = models.CharField(primary_key=True, max_length=50)
    user_id = models.CharField(max_length=50)
    created_at = models.DateField()

    class Meta:
        db_table = "kyc_policy"
        managed = False


# ================================================================
# FULL KYC FORM SUBMISSION
# ================================================================
class KycSubmission(models.Model):
    """
    Stores full KYC form data for each user.
    One user_id = one KYC submission (can overwrite on update).
    """

    user = models.OneToOneField(KycUserInfo, on_delete=models.CASCADE, related_name="submission")

    # -------------------------
    # Personal Details
    # -------------------------
    salutation = models.CharField(max_length=20, null=True, blank=True)
    gender = models.CharField(max_length=20)
    nationality = models.CharField(max_length=50)

    marital_status = models.CharField(max_length=20)
    spouse_name = models.CharField(max_length=100, null=True, blank=True)
    father_name = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100)
    grand_father_name = models.CharField(max_length=100)
    father_in_law_name = models.CharField(max_length=100, null=True, blank=True)

    son_name = models.CharField(max_length=100, null=True, blank=True)
    daughter_name = models.CharField(max_length=100, null=True, blank=True)
    daughter_in_law_name = models.CharField(max_length=100, null=True, blank=True)

    # -------------------------
    # Citizenship / Documents
    # -------------------------
    citizenship_no = models.CharField(max_length=100)
    citizen_bs = models.CharField(max_length=20)
    citizen_ad = models.DateField()
    citizenship_issued_place = models.CharField(max_length=100)

    passport_no = models.CharField(max_length=50, null=True, blank=True)
    nid_no = models.CharField(max_length=50, null=True, blank=True)

    # -------------------------
    # Address — Permanent
    # -------------------------
    perm_province = models.CharField(max_length=50)
    perm_district = models.CharField(max_length=50)
    perm_municipality = models.CharField(max_length=50)
    perm_ward = models.IntegerField()
    perm_address = models.CharField(max_length=100)
    perm_house_number = models.CharField(max_length=50, null=True, blank=True)

    # -------------------------
    # Address — Temporary
    # -------------------------
    temp_province = models.CharField(max_length=50)
    temp_district = models.CharField(max_length=50)
    temp_municipality = models.CharField(max_length=50)
    temp_ward = models.IntegerField()
    temp_address = models.CharField(max_length=100)
    temp_house_number = models.CharField(max_length=50, null=True, blank=True)

    # -------------------------
    # Financial Details
    # -------------------------
    bank_name = models.CharField(max_length=100)
    bank_branch = models.CharField(max_length=100)
    bank_account_number = models.CharField(max_length=50)
    bank_account_type = models.CharField(max_length=50)

    occupation = models.CharField(max_length=100)
    occupation_description = models.CharField(max_length=150, null=True, blank=True)
    income_mode = models.CharField(max_length=20)
    annual_income = models.BigIntegerField()
    income_source = models.CharField(max_length=100)

    pan_number = models.CharField(max_length=50)
    qualification = models.CharField(max_length=50)
    employer_name = models.CharField(max_length=100, null=True, blank=True)
    office_address = models.CharField(max_length=100, null=True, blank=True)

    # -------------------------
    # Nominee
    # -------------------------
    nominee_name = models.CharField(max_length=100)
    nominee_relation = models.CharField(max_length=50)
    nominee_dob_bs = models.CharField(max_length=20)
    nominee_dob_ad = models.DateField()
    nominee_contact = models.CharField(max_length=20)

    guardian_name = models.CharField(max_length=100, null=True, blank=True)
    guardian_relation = models.CharField(max_length=100, null=True, blank=True)

    # -------------------------
    # PEP / AML
    # -------------------------
    is_pep = models.BooleanField(default=False)
    is_aml = models.BooleanField(default=False)

    # -------------------------
    # Metadata
    # -------------------------
    submitted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "kyc_submission"


# ================================================================
# DOCUMENT TABLE (ALL FILE UPLOADS)
# ================================================================
class KycDocument(models.Model):

    DOC_TYPES = [
        ("PHOTO", "Photo"),
        ("CITIZENSHIP_FRONT", "Citizenship Front"),
        ("CITIZENSHIP_BACK", "Citizenship Back"),
        ("NID", "National Identity Card"),
        ("SIGNATURE", "Signature"),
        ("ADDITIONAL", "Additional Document"),
    ]

    user = models.ForeignKey(KycUserInfo, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=50, choices=DOC_TYPES)
    file_path = models.FileField(upload_to="kyc_docs/")
    file_name = models.CharField(max_length=150, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "kyc_documents"


# ================================================================
# AGENT MODEL
# ================================================================
class KycAgentInfo(models.Model):
    agent_code = models.CharField(primary_key=True, max_length=50)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    dob = models.DateField()
    phone_number = models.CharField(max_length=20)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=50)

    class Meta:
        db_table = "kyc_agent_info"
        managed = False


# ================================================================
# ADMIN MODEL
# ================================================================
class KycAdmin(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "kycform_kycadmin"
