# kycform/models.py
from django.db import models

class Customer(models.Model):
    full_name = models.CharField(max_length=150)
    citizenship_no = models.CharField(max_length=50, unique=True)
    nid_no = models.CharField(max_length=50, blank=True, null=True)
    dob = models.DateField()
    address = models.TextField(blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    kyc_updated = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name

class Agent(models.Model):
    agent_code = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=200)


class Policy(models.Model):
    policy_no = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='policies')
    sum_assured = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    term_years = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.policy_no


class PremiumPayment(models.Model):
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.policy.policy_no} - {self.payment_date}"
    
from django.db import models

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


    


class KycPolicy(models.Model):
    policy_number = models.CharField(primary_key=True, max_length=50, db_column='policy_number')
    user_id = models.CharField(max_length=50, db_column='user_id')
    created_at = models.DateField(db_column='created_at')

    class Meta:
        db_table = "kyc_policy"
        managed = False


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

class KycAdmin(models.Model):
    """
    Custom Admin login for KYC system (NOT Django superuser).
    Only used for verifying customer KYC submissions.
    """

    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)   # store plain or hashed later
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
