# kycform/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone

from .models import KycSubmission
from .forms import KycSubmissionAdminForm


# -------------------------------------------------------
# Helper: Thumbnail (image / PDF)
# -------------------------------------------------------
def file_thumbnail(f, width=120):
    if not f:
        return "No File"
    try:
        url = f.url
    except:
        return "No File"

    if url.lower().endswith(".pdf"):
        return format_html('<a href="{}" target="_blank">Open PDF</a>', url)

    return format_html('<img src="{}" width="{}" style="object-fit:cover;"/>', url, width)


# -------------------------------------------------------
# ADMIN CLASS
# -------------------------------------------------------
@admin.register(KycSubmission)
class KycSubmissionAdmin(admin.ModelAdmin):

    form = KycSubmissionAdminForm

    list_display = (
        "user",
        "kyc_status_colored",
        "is_lock",
        "locked_by",
        "submitted_at",
        "has_photo",
        "extra_doc_count",
    )

    list_filter = (
        "is_lock",
        "submitted_at",
        "user__kyc_status",
    )

    search_fields = (
        "user__user_id",
        "user__first_name",
        "user__last_name",
        "citizenship_no",
    )

    readonly_fields = (
        "submitted_at",
        "locked_at",
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
            "fields": ("user", "submitted_at", "kyc_status", "is_lock", "locked_at", "locked_by"),
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
                ("passport_no", "nid_no"),
            )
        }),

        ("Permanent Address", {
            "fields": (
                ("perm_province", "perm_district", "perm_municipality"),
                ("perm_ward", "perm_address", "perm_house_number"),
            )
        }),

        ("Temporary Address", {
            "fields": (
                ("temp_province", "temp_district", "temp_municipality"),
                ("temp_ward", "temp_address", "temp_house_number"),
            )
        }),

        ("Bank / Occupation", {
            "fields": (
                ("bank_name", "bank_branch", "account_number", "account_type"),
                ("occupation", "occupation_description"),
                ("income_mode", "annual_income"),
                "income_source",
                ("pan_number", "qualification"),
                "employer_name",
                "office_address",
            )
        }),

        ("Nominee", {
            "fields": (
                ("nominee_name", "nominee_relation"),
                ("nominee_dob_ad", "nominee_dob_bs"),
                "nominee_contact",
                ("guardian_name", "guardian_relation"),
            )
        }),

        ("AML / PEP", {
            "fields": ("is_pep", "is_aml"),
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

    # -------------------------------------------------------------------
    # Inject custom JS (unlock is_lock dynamically)
    # -------------------------------------------------------------------
    class Media:
        js = ("kycform/js/kyc_admin.js",)

    # -------------------------------------------------------------------
    # READ-ONLY RULES WHEN LOCKED
    # -------------------------------------------------------------------
    def get_readonly_fields(self, request, obj=None):
        base = list(self.readonly_fields)

        # Superusers can edit everything
        if request.user.is_superuser:
            return base

        # If locked → staff cannot edit anything
        if obj and obj.is_lock:
            all_fields = [f.name for f in self.model._meta.fields]
            return all_fields + base

        # Staff (not locked)
        return base + ["locked_at", "locked_by"]

    # -------------------------------------------------------------------
    # Disable Save buttons when locked
    # -------------------------------------------------------------------
    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        obj = None

        if object_id:
            obj = self.get_object(request, object_id)

        if obj and obj.is_lock and not request.user.is_superuser:
            extra_context["show_save"] = False
            extra_context["show_save_and_continue"] = False
            extra_context["show_save_and_add_another"] = False
            extra_context["show_delete"] = False

        return super().changeform_view(request, object_id, form_url, extra_context)

    # -------------------------------------------------------------------
    # SAVE LOGIC WITH locked_by
    # -------------------------------------------------------------------
    def save_model(self, request, obj, form, change):
        kyc_status = form.cleaned_data.get("kyc_status")

        # If user tries to lock without VERIFIED, deny (except superuser)
        if obj.is_lock and kyc_status != "VERIFIED" and not request.user.is_superuser:
            obj.is_lock = False

        # ALWAYS record who locked it
        if obj.is_lock:
            obj.locked_by = request.user.username

        if obj.is_lock and not obj.locked_at:
            obj.locked_at = timezone.now()

        # Also write back user status (double safety)
        if obj.user and kyc_status:
            obj.user.kyc_status = kyc_status
            obj.user.save()

        super().save_model(request, obj, form, change)

    # -------------------------------------------------------------------
    # DISPLAY HELPERS
    # -------------------------------------------------------------------
    def kyc_status_colored(self, obj):
        s = obj.user.kyc_status or "UNKNOWN"
        color = {
            "NOT_INITIATED": "gray",
            "PENDING": "orange",
            "INCOMPLETE": "blue",
            "VERIFIED": "green",
            "REJECTED": "red",
        }.get(s, "black")
        return format_html("<b style='color:{}'>{}</b>", color, s)

    kyc_status_colored.short_description = "KYC Status"

    def has_photo(self, obj):
        return bool(obj.photo)

    def extra_doc_count(self, obj):
        return len(obj.additional_docs or [])

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
        docs = obj.additional_docs or []
        if not docs:
            return "No Additional Documents"
        html = "<ul>"
        for d in docs:
            url = d.get("file_url")
            name = d.get("doc_name") or "Document"
            if url:
                html += f'<li><a href="{url}" target="_blank">{name}</a></li>'
            else:
                html += f"<li>{name}</li>"
        html += "</ul>"
        return mark_safe(html)

    def data_block(self, obj):
        import json
        return format_html(
            "<pre style='max-height:300px; overflow:auto'>{}</pre>",
            json.dumps(obj.data_json or {}, indent=2, ensure_ascii=False),
        )

    # -------------------------------------------------------------------
    # ACTIONS (Verify / Reject / Incomplete)
    # -------------------------------------------------------------------
    actions = ["mark_verified", "mark_rejected", "mark_incomplete"]

    def _apply_review(self, request, queryset, new_status, comment):
        now = timezone.now().isoformat()

        for sub in queryset:
            sub.user.kyc_status = new_status
            sub.user.save()

            audit = {
                "status": new_status,
                "reviewed_by": str(request.user),
                "reviewed_at": now,
                "comment": comment,
            }

            data = sub.data_json or {}
            data.setdefault("review_history", []).append(audit)
            data["last_review"] = audit

            sub.data_json = data
            sub.save()

    def mark_verified(self, request, queryset):
        self._apply_review(request, queryset, "VERIFIED", "Verified by admin")
        self.message_user(request, "Selected KYC marked VERIFIED.")
    mark_verified.short_description = "Mark as VERIFIED"

    def mark_rejected(self, request, queryset):
        self._apply_review(request, queryset, "REJECTED", "Rejected by admin")
        self.message_user(request, "Selected KYC marked REJECTED.")
    mark_rejected.short_description = "Mark as REJECTED"

    def mark_incomplete(self, request, queryset):
        self._apply_review(request, queryset, "INCOMPLETE", "Incomplete – needs correction")
        self.message_user(request, "Selected KYC marked INCOMPLETE.")
    mark_incomplete.short_description = "Mark as INCOMPLETE"
