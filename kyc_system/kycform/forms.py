# kycform/forms.py

from django import forms
from django.utils import timezone
from .models import KycSubmission


class KycSubmissionAdminForm(forms.ModelForm):

    # virtual field shown in admin only
    kyc_status = forms.ChoiceField(
        choices=[
            ("NOT_INITIATED", "Not Initiated"),
            ("PENDING", "Pending"),
            ("INCOMPLETE", "Incomplete"),
            ("VERIFIED", "Verified"),
            ("REJECTED", "Rejected"),
        ],
        required=True,
        label="KYC Status",
    )

    class Meta:
        model = KycSubmission
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ---------------------------------------------------------
        # Pre-fill dropdown value from related user
        # ---------------------------------------------------------
        if self.instance and getattr(self.instance, "user", None):
            self.fields["kyc_status"].initial = self.instance.user.kyc_status

        # ---------------------------------------------------------
        # Enable/disable is_lock dynamically
        # ---------------------------------------------------------
        if "is_lock" in self.fields:

            # Determine effective status (POST overrides initial)
            status = self.data.get("kyc_status") or self.fields["kyc_status"].initial

            if status == "VERIFIED":
                self.fields["is_lock"].disabled = False
            else:
                self.fields["is_lock"].disabled = True
                self.fields["is_lock"].initial = False

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("kyc_status")

        # Enforce: cannot lock unless VERIFIED
        if status != "VERIFIED":
            cleaned["is_lock"] = False

        return cleaned

    def save(self, commit=True):
        submission = super().save(commit=False)

        new_status = self.cleaned_data.get("kyc_status")

        # Update related user's KYC status
        if new_status and submission.user:
            submission.user.kyc_status = new_status
            submission.user.save()

        # Handle locking timestamp (locked_by handled in admin.py)
        if submission.is_lock and not submission.locked_at:
            submission.locked_at = timezone.now()

        if commit:
            submission.save()

        return submission
