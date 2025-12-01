# kycform/admin.py
from .forms import KycSubmissionAdminForm
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import KycSubmission, KycUserInfo


def file_thumbnail(filefield, width=120):
    """
    Return an <img> or PDF link HTML for admin display. Accepts a FileField or None.
    """
    if not filefield:
        return "No File"
    try:
        url = filefield.url
    except Exception:
        return "No File"
    low = url.lower()
    if low.endswith(".pdf"):
        return format_html('<a href="{}" target="_blank" style="font-weight:bold">Open PDF</a>', url)
    return format_html('<img src="{}" width="{}" style="object-fit:cover;"/>', url, width)


@admin.register(KycSubmission)
class KycSubmissionAdmin(admin.ModelAdmin):
    """
    Admin for KycSubmission.
    - Shows AML/PEP fields directly in admin.
    - Uses user.kyc_status for status display & filtering.
    - Admin actions update KycUserInfo.kyc_status and append review audit into submission.data_json.
    """
    form = KycSubmissionAdminForm

    list_display = (
        "user",
        "kyc_status",
        "is_pep",          # added
        "is_aml",          # added
        "submitted_at",
        "has_photo",
        "extra_doc_count",
    )

    list_filter = (
        "user__kyc_status",
        "is_pep",           # added
        "is_aml",           # added
        "submitted_at",
    )

    search_fields = (
        "user__user_id",
        "user__first_name",
        "user__last_name",
        "citizenship_no"
    )

    readonly_fields = (
        "submitted_at",
        "data_block",
        "photo_preview",
        "citizenship_front_preview",
        "citizenship_back_preview",
        "signature_preview",
        "passport_doc_preview",
        "extra_docs_preview",
    )

    fieldsets = (
        ("Submission Metadata", {
            "fields": ("user", "submitted_at"),
        }),
        ("Personal Information", {
            "fields": (
                ("salutation", "first_name", "middle_name", "last_name"),
                "full_name_nep",
                ("gender", "nationality"),
                ("dob_ad", "dob_bs"),
                ("email", "mobile"),
            )
        }),
        ("Citizenship / Document Info", {
            "fields": (
                ("citizenship_no", "citizenship_place"),
                ("citizen_ad", "citizen_bs"),
                ("passport_no", "nid_no")
            )
        }),
        ("Permanent Address", {
            "fields": (
                ("perm_province", "perm_district", "perm_municipality"),
                ("perm_ward", "perm_address")
            )
        }),
        ("Temporary Address", {
            "fields": (
                ("temp_province", "temp_district", "temp_municipality"),
                ("temp_ward", "temp_address")
            )
        }),
        ("Bank / Occupation", {
            "fields": (
                ("bank_name", "bank_branch", "account_number", "account_type"),
                ("occupation", "occupation_description", "income_mode", "annual_income")
            )
        }),
        ("Nominee", {
            "fields": (
                ("nominee_name", "nominee_relation"),
                ("nominee_dob_ad", "nominee_dob_bs"),
                "nominee_contact"
            )
        }),
        # UPDATED — AML / PEP SECTION
        ("AML / PEP", {
            "fields": ("is_pep", "is_aml"),
        }),
        ("KYC Review", {
            "fields": ("kyc_status",)
        }),

        ("Documents", {
            "fields": (
                ("photo", "photo_preview"),
                ("citizenship_front", "citizenship_front_preview"),
                ("citizenship_back", "citizenship_back_preview"),
                ("signature", "signature_preview"),
                ("passport_doc", "passport_doc_preview"),
                "extra_docs_preview",
            )
        }),
        ("Raw JSON (Read-only)", {
            "classes": ("collapse",),
            "fields": ("data_block",),
        }),
    )

    # ---------------------------------------------------------------
    # Helper displays
    # ---------------------------------------------------------------
    def kyc_status(self, obj):
        try:
            st = obj.user.kyc_status
        except Exception:
            st = "UNKNOWN"
        color = {
            "NOT_INITIATED": "gray",
            "PENDING": "orange",
            "INCOMPLETE": "blue",
            "VERIFIED": "green",
            "REJECTED": "red",
        }.get(st, "black")
        return format_html('<span style="color:{}; font-weight:bold">{}</span>', color, st)

    kyc_status.short_description = "KYC Status"
    kyc_status.admin_order_field = "user__kyc_status"

    def has_photo(self, obj):
        return bool(obj.photo)
    has_photo.boolean = True
    has_photo.short_description = "Photo?"

    def extra_doc_count(self, obj):
        try:
            return len(obj.additional_docs or [])
        except Exception:
            return 0
    extra_doc_count.short_description = "Extra docs"

    def photo_preview(self, obj):
        return file_thumbnail(obj.photo)

    def citizenship_front_preview(self, obj):
        return file_thumbnail(obj.citizenship_front)

    def citizenship_back_preview(self, obj):
        return file_thumbnail(obj.citizenship_back)

    def signature_preview(self, obj):
        return file_thumbnail(obj.signature)

    def passport_doc_preview(self, obj):
        return file_thumbnail(obj.passport_doc)

    def extra_docs_preview(self, obj):
        if not obj.additional_docs:
            return "No Additional Documents"
        html = "<ul>"
        for d in obj.additional_docs:
            label = d.get("doc_name") or d.get("file_url") or "Document"
            url = d.get("file_url")
            if url:
                html += f'<li><a href="{url}" target="_blank">{label}</a></li>'
            else:
                html += f'<li>{label}</li>'
        html += "</ul>"
        return format_html(html)

    def data_block(self, obj):
        import json
        try:
            formatted = json.dumps(obj.data_json or {}, indent=2, ensure_ascii=False)
            return format_html("<pre style='max-height:350px; overflow:auto'>{}</pre>", formatted)
        except Exception:
            return "No data"

    # ---------------------------------------------------------------
    # Review Actions
    # ---------------------------------------------------------------
    actions = ["mark_verified", "mark_rejected", "mark_incomplete"]

    def _apply_review(self, request, queryset, new_status, default_comment=None):
        now = timezone.now().isoformat()

        for sub in queryset:
            # update user status
            try:
                sub.user.kyc_status = new_status
                sub.user.save()
            except Exception as e:
                self.message_user(request, f"Could not update user status for {sub.user}: {e}")

            # write audit
            try:
                review_entry = {
                    "status": new_status,
                    "reviewed_by": str(request.user),
                    "reviewed_at": now,
                    "comment": default_comment or ""
                }
                dd = sub.data_json or {}
                dd.setdefault("review_history", []).append(review_entry)
                dd["last_review"] = review_entry
                sub.data_json = dd
                sub.save()
            except Exception as e:
                self.message_user(request, f"Audit write failure {sub.pk}: {e}")

    def mark_verified(self, request, queryset):
        self._apply_review(request, queryset, "VERIFIED", "Verified by admin")
        self.message_user(request, "Selected submissions marked VERIFIED.")

    def mark_rejected(self, request, queryset):
        self._apply_review(request, queryset, "REJECTED", "Rejected by admin")
        self.message_user(request, "Selected submissions marked REJECTED.")

    def mark_incomplete(self, request, queryset):
        self._apply_review(request, queryset, "INCOMPLETE", "Marked incomplete - needs correction")
        self.message_user(request, "Selected submissions marked INCOMPLETE.")

    