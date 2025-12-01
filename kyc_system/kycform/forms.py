from django import forms
from .models import KycSubmission

class KycSubmissionAdminForm(forms.ModelForm):

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
        if self.instance and self.instance.user:
            self.fields["kyc_status"].initial = self.instance.user.kyc_status

    def save(self, commit=True):
        submission = super().save(commit=False)
        # write status back to related KycUserInfo
        new_status = self.cleaned_data["kyc_status"]
        submission.user.kyc_status = new_status
        submission.user.save()
        if commit:
            submission.save()
        return submission
