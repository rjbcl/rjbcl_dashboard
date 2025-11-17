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
