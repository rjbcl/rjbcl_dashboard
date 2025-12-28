# kycform/models.py

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import get_user_model


User = get_user_model()

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
        max_length=20, choices=KYC_STATUS_CHOICES, default="NOT_INITIATED"
    )
    mobile_verified = models.BooleanField(default=False)
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

    # -------------------------------------------
    # RELATION
    # -------------------------------------------
    user = models.OneToOneField(
        KycUserInfo,
        on_delete=models.CASCADE,
        related_name="submission"
    )

    # -------------------------------------------
    # BACKUP DATA
    # -------------------------------------------
    data_json = models.JSONField(default=dict, blank=True)

    # -----------------------------------------------------
    # SOFT LOCK (Prevent concurrent edits)
    # -----------------------------------------------------
    currently_reviewed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="kyc_currently_reviewing"
    )
    review_started_at = models.DateTimeField(null=True, blank=True)
    review_timeout_minutes = 10  # allow override if needed
    rejection_comment = models.TextField(null=True, blank=True)
    # -----------------------------------------------------
    # OPTIMISTIC LOCKING (Versioning)
    # -----------------------------------------------------
    version = models.PositiveIntegerField(default=1)

    # -----------------------------------------------------
    # FINAL LOCK (Permanent freeze)
    # -----------------------------------------------------
    is_lock = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.CharField(max_length=200, null=True, blank=True)

    # -----------------------------------------------------
    # PERSONAL INFO
    # -----------------------------------------------------
    salutation = models.CharField(max_length=20, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    middle_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    full_name_nep = models.CharField(max_length=200, null=True, blank=True)

    gender = models.CharField(max_length=20, null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    marital_status = models.CharField(max_length=20, null=True, blank=True)

    dob_ad = models.DateField(null=True, blank=True)
    dob_bs = models.CharField(max_length=20, null=True, blank=True)

    email = models.CharField(max_length=200, null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)

    # -----------------------------------------------------
    # FAMILY
    # -----------------------------------------------------
    spouse_name = models.CharField(max_length=100, null=True, blank=True)
    father_name = models.CharField(max_length=100, null=True, blank=True)
    mother_name = models.CharField(max_length=100, null=True, blank=True)
    grand_father_name = models.CharField(max_length=100, null=True, blank=True)
    father_in_law_name = models.CharField(max_length=100, null=True, blank=True)
    son_name = models.CharField(max_length=100, null=True, blank=True)
    daughter_name = models.CharField(max_length=100, null=True, blank=True)
    daughter_in_law_name = models.CharField(max_length=100, null=True, blank=True)

    # -----------------------------------------------------
    # DOCUMENT INFO
    # -----------------------------------------------------
    citizenship_no = models.CharField(max_length=100, null=True, blank=True)
    citizen_bs = models.CharField(max_length=20, null=True, blank=True)
    citizen_ad = models.DateField(null=True, blank=True)
    citizenship_place = models.CharField(max_length=100, null=True, blank=True)

    passport_no = models.CharField(max_length=50, null=True, blank=True)
    nid_no = models.CharField(max_length=50, null=True, blank=True)

    # -----------------------------------------------------
    # PERMANENT ADDRESS
    # -----------------------------------------------------
    perm_province = models.CharField(max_length=50, null=True, blank=True)
    perm_district = models.CharField(max_length=50, null=True, blank=True)
    perm_municipality = models.CharField(max_length=50, null=True, blank=True)
    perm_ward = models.CharField(max_length=10, null=True, blank=True)
    perm_address = models.CharField(max_length=100, null=True, blank=True)
    perm_house_number = models.CharField(max_length=50, null=True, blank=True)

    # -----------------------------------------------------
    # TEMPORARY ADDRESS
    # -----------------------------------------------------
    temp_province = models.CharField(max_length=50, null=True, blank=True)
    temp_district = models.CharField(max_length=50, null=True, blank=True)
    temp_municipality = models.CharField(max_length=50, null=True, blank=True)
    temp_ward = models.CharField(max_length=10, null=True, blank=True)
    temp_address = models.CharField(max_length=100, null=True, blank=True)
    temp_house_number = models.CharField(max_length=50, null=True, blank=True)

    # -----------------------------------------------------
    # BANK
    # -----------------------------------------------------
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    bank_branch = models.CharField(max_length=100, null=True, blank=True)
    account_number = models.CharField(max_length=50, null=True, blank=True)
    account_type = models.CharField(max_length=50, null=True, blank=True)

    # -----------------------------------------------------
    # OCCUPATION
    # -----------------------------------------------------
    occupation = models.CharField(max_length=100, null=True, blank=True)
    occupation_description = models.CharField(max_length=200, null=True, blank=True)
    income_mode = models.CharField(max_length=50, null=True, blank=True)
    annual_income = models.BigIntegerField(null=True, blank=True)
    income_source = models.CharField(max_length=100, null=True, blank=True)
    pan_number = models.CharField(max_length=50, null=True, blank=True)
    qualification = models.CharField(max_length=100, null=True, blank=True)
    employer_name = models.CharField(max_length=150, null=True, blank=True)
    office_address = models.CharField(max_length=150, null=True, blank=True)

    # -----------------------------------------------------
    # NOMINEE
    # -----------------------------------------------------
    nominee_name = models.CharField(max_length=100, null=True, blank=True)
    nominee_relation = models.CharField(max_length=50, null=True, blank=True)
    nominee_dob_ad = models.DateField(null=True, blank=True)
    nominee_dob_bs = models.CharField(max_length=20, null=True, blank=True)
    nominee_contact = models.CharField(max_length=20, null=True, blank=True)

    guardian_name = models.CharField(max_length=100, null=True, blank=True)
    guardian_relation = models.CharField(max_length=100, null=True, blank=True)

    # -----------------------------------------------------
    # AML / PEP
    # -----------------------------------------------------
    is_pep = models.BooleanField(default=False)
    is_aml = models.BooleanField(default=False)

    # -----------------------------------------------------
    # FILE UPLOADS
    # -----------------------------------------------------
    photo = models.FileField(upload_to="kyc/photos/", null=True, blank=True)
    citizenship_front = models.FileField(upload_to="kyc/citizenship/", null=True, blank=True)
    citizenship_back = models.FileField(upload_to="kyc/citizenship/", null=True, blank=True)
    signature = models.FileField(upload_to="kyc/signature/", null=True, blank=True)
    passport_doc = models.FileField(upload_to="kyc/passport/", null=True, blank=True)

    additional_docs = models.JSONField(default=list, blank=True)

    # ============================================================
    # DOCUMENT ACCESS HELPERS (READ FROM KycDocument TABLE)
    # ============================================================
    def _doc(self, doc_type):
        doc = self.user.documents.filter(doc_type=doc_type, is_current=True).order_by("-uploaded_at").first()
        return doc.url if doc else None

    @property
    def photo_url(self):
        return self._doc("PHOTO")

    @property
    def citizenship_front_url(self):
        return self._doc("CITIZENSHIP_FRONT")

    @property
    def citizenship_back_url(self):
        return self._doc("CITIZENSHIP_BACK")

    @property
    def signature_url(self):
        return self._doc("SIGNATURE")

    @property
    def passport_doc_url(self):
        return self._doc("PASSPORT")

    @property
    def nid_url(self):
        return self._doc("NID")

    @property
    def additional_docs_list(self):
        docs = self.user.documents.filter(doc_type="ADDITIONAL").order_by("-uploaded_at")
        return [
            {
                "id": d.id,
                "file_name": d.file_name or d.file.name,
                "url": d.url,
                "uploaded_at": d.uploaded_at.isoformat(),
            }
            for d in docs
        ]

    # -----------------------------------------------------
    # META
    # -----------------------------------------------------
    submitted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "kyc_submission"

    def __str__(self):
        return f"KYC Submission - {self.user.user_id}"




# ================================================================
# DOCUMENT TABLE (UNIFIED STORAGE FOR ALL UPLOADED KYC DOCUMENTS)
# ================================================================
class KycDocument(models.Model):

    DOC_TYPES = [
        ("PHOTO", "Photo"),
        ("CITIZENSHIP_FRONT", "Citizenship Front"),
        ("CITIZENSHIP_BACK", "Citizenship Back"),
        ("SIGNATURE", "Signature"),
        ("PASSPORT", "Passport Document"),
        ("NID", "National Identity Card"),
        ("ADDITIONAL", "Additional Document"),
    ]

    id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey(
        KycUserInfo,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    submission = models.ForeignKey(
        "KycSubmission",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="docs"
    )

    doc_type = models.CharField(max_length=50, choices=DOC_TYPES)

    file = models.FileField(upload_to="kyc_docs/%Y/%m/%d/", null=True, blank=True)
    file_name = models.CharField(max_length=200, null=True, blank=True)


    # helpful metadata field
    metadata = models.JSONField(default=dict, blank=True)

    uploaded_at = models.DateTimeField(default=timezone.now)

    # whether this is the newest version of this doc_type
    is_current = models.BooleanField(default=True)

    class Meta:
        db_table = "kyc_documents"
        indexes = [
            models.Index(fields=["user", "doc_type", "is_current"]),
        ]

    def __str__(self):
        return f"{self.user.user_id} - {self.doc_type} - {self.file_name or self.file.name}"

    @property
    def url(self):
        try:
            return self.file.url
        except:
            return None


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
    
# ================================================================
# KYC CHANGE LOG MODEL
# ================================================================

class KycChangeLog(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "Create"),
        ("UPDATE", "Update"),
        ("DELETE", "Delete"),
        ("STATUS", "Status Change"),
        ("DOCUMENT", "Document Change"),
    ]

    ACTOR_TYPE = [
        ("USER", "User"),
        ("ADMIN", "Admin"),
        ("AGENT", "Agent"),
        ("SYSTEM", "System"),
    ]

    id = models.BigAutoField(primary_key=True)

    submission = models.ForeignKey(
        "KycSubmission",
        on_delete=models.CASCADE,
        related_name="change_logs"
    )

    field_name = models.CharField(max_length=100, blank=True, null=True)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor_type = models.CharField(max_length=20, choices=ACTOR_TYPE)
    actor_identifier = models.CharField(max_length=100, blank=True, null=True)

    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "kyc_change_log"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.submission.user.user_id} | {self.action} | {self.field_name}"

# ================================================================
# KYC MOBILE OTP MODEL

class KycMobileOTP(models.Model):
    kyc_user = models.ForeignKey(
        "KycUserInfo",
        on_delete=models.CASCADE,
        related_name="mobile_otps",
        db_index=True
    )
    mobile = models.CharField(max_length=10)
    otp_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["kyc_user", "mobile"]),
        ]

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.kyc_user.user_id} ({self.mobile})"
