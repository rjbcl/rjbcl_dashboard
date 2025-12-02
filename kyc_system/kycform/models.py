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

    password = models.CharField(max_length=100, null=True, blank=True)

    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100)
    full_name_nep = models.CharField(max_length=200, null=True, blank=True)

    dob = models.DateField()
    email = models.CharField(max_length=200, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)

    # Admin review status
    kyc_status = models.CharField(
        max_length=20,
        choices=KYC_STATUS_CHOICES,
        default="NOT_INITIATED"
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

    # One user = one submission
    user = models.OneToOneField(
        KycUserInfo,
        on_delete=models.CASCADE,
        related_name="submission"
    )
    # Backup full JSON of all fields
    data_json = models.JSONField(default=dict, blank=True)

    is_lock = models.BooleanField(default=False)   # NEW FIELD
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.CharField(max_length=200, null=True, blank=True)   # NEW
    # -------------------------
    # PERSONAL
    # -------------------------
    salutation = models.CharField(max_length=20, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    full_name_nep = models.CharField(max_length=200, null=True, blank=True)

    gender = models.CharField(max_length=20, null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)

    dob_ad = models.DateField(null=True, blank=True)
    dob_bs = models.CharField(max_length=20, null=True, blank=True)

    email = models.CharField(max_length=200, null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)

    # -------------------------
    # FAMILY
    # -------------------------
    spouse_name = models.CharField(max_length=100, null=True, blank=True)
    father_name = models.CharField(max_length=100, null=True, blank=True)
    mother_name = models.CharField(max_length=100, null=True, blank=True)
    grand_father_name = models.CharField(max_length=100, null=True, blank=True)
    father_in_law_name = models.CharField(max_length=100, null=True, blank=True)
    son_name = models.CharField(max_length=100, null=True, blank=True)
    daughter_name = models.CharField(max_length=100, null=True, blank=True)
    daughter_in_law_name = models.CharField(max_length=100, null=True, blank=True)

    # -------------------------
    # DOCUMENT INFO
    # -------------------------
    citizenship_no = models.CharField(max_length=100, null=True, blank=True)
    citizen_bs = models.CharField(max_length=20, null=True, blank=True)
    citizen_ad = models.DateField(null=True, blank=True)
    citizenship_place = models.CharField(max_length=100, null=True, blank=True)

    passport_no = models.CharField(max_length=50, null=True, blank=True)
    nid_no = models.CharField(max_length=50, null=True, blank=True)

    # -------------------------
    # ADDRESS — Permanent
    # -------------------------
    perm_province = models.CharField(max_length=50, null=True, blank=True)
    perm_district = models.CharField(max_length=50, null=True, blank=True)
    perm_municipality = models.CharField(max_length=50, null=True, blank=True)
    perm_ward = models.CharField(max_length=10, null=True, blank=True)
    perm_address = models.CharField(max_length=100, null=True, blank=True)
    perm_house_number = models.CharField(max_length=50, null=True, blank=True)

    # -------------------------
    # ADDRESS — Temporary
    # -------------------------
    temp_province = models.CharField(max_length=50, null=True, blank=True)
    temp_district = models.CharField(max_length=50, null=True, blank=True)
    temp_municipality = models.CharField(max_length=50, null=True, blank=True)
    temp_ward = models.CharField(max_length=10, null=True, blank=True)
    temp_address = models.CharField(max_length=100, null=True, blank=True)
    temp_house_number = models.CharField(max_length=50, null=True, blank=True)

    # -------------------------
    # BANK
    # -------------------------
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    bank_branch = models.CharField(max_length=100, null=True, blank=True)
    account_number = models.CharField(max_length=50, null=True, blank=True)
    account_type = models.CharField(max_length=50, null=True, blank=True)

    # -------------------------
    # OCCUPATION
    # -------------------------
    occupation = models.CharField(max_length=100, null=True, blank=True)
    occupation_description = models.CharField(max_length=200, null=True, blank=True)
    income_mode = models.CharField(max_length=50, null=True, blank=True)
    annual_income = models.BigIntegerField(null=True, blank=True)
    income_source = models.CharField(max_length=100, null=True, blank=True)
    pan_number = models.CharField(max_length=50, null=True, blank=True)
    qualification = models.CharField(max_length=100, null=True, blank=True)
    employer_name = models.CharField(max_length=150, null=True, blank=True)
    office_address = models.CharField(max_length=150, null=True, blank=True)

    # -------------------------
    # NOMINEE
    # -------------------------
    nominee_name = models.CharField(max_length=100, null=True, blank=True)
    nominee_relation = models.CharField(max_length=50, null=True, blank=True)
    nominee_dob_ad = models.DateField(null=True, blank=True)
    nominee_dob_bs = models.CharField(max_length=20, null=True, blank=True)
    nominee_contact = models.CharField(max_length=20, null=True, blank=True)

    guardian_name = models.CharField(max_length=100, null=True, blank=True)
    guardian_relation = models.CharField(max_length=100, null=True, blank=True)

    # -------------------------
    # AML / PEP
    # -------------------------
    is_pep = models.BooleanField(default=False)
    is_aml = models.BooleanField(default=False)

    # -------------------------
    # FILE UPLOADS
    # -------------------------
    photo = models.FileField(upload_to="kyc/photos/", null=True, blank=True)
    citizenship_front = models.FileField(upload_to="kyc/citizenship/", null=True, blank=True)
    citizenship_back = models.FileField(upload_to="kyc/citizenship/", null=True, blank=True)
    signature = models.FileField(upload_to="kyc/signature/", null=True, blank=True)
    passport_doc = models.FileField(upload_to="kyc/passport/", null=True, blank=True)

    # additional_docs = [{"index":1, "doc_name":"...", "file_url":"..."}]
    additional_docs = models.JSONField(default=list, blank=True)

    submitted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "kyc_submission"

    def __str__(self):
        return f"KYC Submission - {self.user.user_id}"




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


# ================================================================
# TEMPORARY KYC DRAFT MODEL
# ================================================================
class KYCTemporary(models.Model):
    policy_no = models.CharField(max_length=30, unique=True)
    data_json = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Draft KYC for {self.policy_no}"