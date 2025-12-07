# kycform/forms.py

from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import KycSubmission


class KycSubmissionAdminForm(forms.ModelForm):
    """
    Stable admin ModelForm for KycSubmission.

    - `kyc_status` is a virtual dropdown (mirrors user.kyc_status)
    - `rejection_comment_input` is a UI-only temporary field (not stored directly)
      — admin.py inserts this field into the fieldsets when needed and controls its widget.
    - This form does NOT try to hide/show widgets in __init__; admin.py handles that.
    """

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

    # UI-only temporary field for admin to collect rejection reason.
    rejection_comment_input = forms.CharField(
        required=False,
        label="Rejection Comment",
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    class Meta:
        model = KycSubmission
        fields = "__all__"

    # ----------
    # __init__
    # ----------
    def __init__(self, *args, **kwargs):
        """
        Minimal init:
        - populate kyc_status initial from linked user. Keep widgets untouched so admin.get_form()
          can switch widget to HiddenInput/Textarea as needed.
        """
        super().__init__(*args, **kwargs)

        if self.instance and getattr(self.instance, "user", None):
            # keep admin dropdown in-sync with the user record
            try:
                self.fields["kyc_status"].initial = self.instance.user.kyc_status
            except Exception:
                # defensive: don't fail admin load if user missing
                self.fields["kyc_status"].initial = None

        # Do NOT change widget.is_hidden or attempt to set .is_hidden attribute:
        # admin.get_form() will set the visible widget or HiddenInput() as required.

    # ----------
    # clean
    # ----------
    def clean(self):
        cleaned = super().clean()

        status = cleaned.get("kyc_status")
        is_lock = cleaned.get("is_lock")
        comment_input = cleaned.get("rejection_comment_input")

        # 1) VERIFIED requires is_lock True
        if status == "VERIFIED" and not is_lock:
            raise ValidationError("To verify the KYC, you must check 'Is Lock'.")

        # 2) is_lock not allowed for other statuses
        if is_lock and status != "VERIFIED":
            raise ValidationError("You can only lock the KYC when it is marked VERIFIED.")

        # 3) REJECTED requires a comment
        if status == "REJECTED":
            # comment_input may be in POST but empty string; require non-empty after strip
            if not comment_input or not str(comment_input).strip():
                raise ValidationError("Please provide a valid reason for rejection.")

        # 4) Auto-reset lock when status is not VERIFIED
        if status != "VERIFIED":
            cleaned["is_lock"] = False

        # 5) Optimistic locking: compare DB version vs current instance.version
        if self.instance and self.instance.pk:
            db_version = (
                KycSubmission.objects.filter(pk=self.instance.pk)
                .values_list("version", flat=True)
                .first()
            )
            form_version = getattr(self.instance, "version", None)

            # If db_version is None treat defensively
            if db_version is not None and form_version is not None and db_version != form_version:
                raise ValidationError(
                    "Another staff updated this KYC during your review. "
                    "Reload the page to continue safely."
                )

        return cleaned

    # ----------
    # save
    # ----------
    def save(self, commit=True):
        # We save into the submission model; the admin view controls whether the
        # temporary field was visible and provided.
        submission = super().save(commit=False)

        new_status = self.cleaned_data.get("kyc_status")

        # Sync status to user record (double-safety)
        if new_status and getattr(submission, "user", None):
            try:
                submission.user.kyc_status = new_status
                submission.user.save()
            except Exception:
                # avoid raising on user save failure during admin form save — still let the admin action proceed
                pass

        # Save rejection comment only when REJECTED (leave previous comment if moving away)
        if new_status == "REJECTED":
            comment = self.cleaned_data.get("rejection_comment_input")
            if comment and str(comment).strip():
                submission.rejection_comment = comment

        # Fill locked_at timestamp when locking
        if submission.is_lock and not submission.locked_at:
            submission.locked_at = timezone.now()

        # Version bump (defensive)
        try:
            submission.version = (submission.version or 0) + 1
        except Exception:
            submission.version = 1

        if commit:
            submission.save()

        return submission
