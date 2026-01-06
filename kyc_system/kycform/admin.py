# kycform/admin.py
from urllib import request
from django.db.models import Q

from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.shortcuts import render, redirect
from django import forms
from django.core.exceptions import PermissionDenied
from django.forms import ValidationError as FormValidationError
from .models import KycChangeLog, KycUserInfo, KycPolicy
from .models import KycMobileOTP


from .models import KycSubmission, KycDocument
from .forms import KycSubmissionAdminForm


# -------------------------------------------------------
# Thumbnail helper (image / PDF)
# -------------------------------------------------------
def file_thumbnail(f, width=120):
    if not f:
        return "No File"
    try:
        url = f.url
    except Exception:
        return "No File"
    if url.lower().endswith(".pdf"):
        return format_html('<a href="{}" target="_blank">Open PDF</a>', url)
    return format_html('<img src="{}" width="{}" style="object-fit:cover;"/>', url, width)


# -------------------------------------------------------
# Reject comment form (used by action)
# -------------------------------------------------------
class RejectCommentForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    comment = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Reason for rejection",
        required=True,
    )


# -------------------------------------------------------
# Admin
# -------------------------------------------------------
@admin.register(KycSubmission)
class KycSubmissionAdmin(admin.ModelAdmin):
    form = KycSubmissionAdminForm
    # --- list / search / filters ---
    list_display = (
        "user",
        "kyc_status_colored",
        "is_lock",
        "locked_by",
        "submitted_at",
        "has_photo",
        "extra_doc_count",
        "currently_reviewed_by",
        "review_started_at",
    )
    list_filter = ("is_lock", "submitted_at", "user__kyc_status")
    search_fields = (
        "user__user_id",
        "user__first_name",
        "user__last_name",
        "citizenship_no",
    )


    # --- readonly helpers (these are methods defined below) ---
    readonly_fields = (
        "policy_info_block",
        "submitted_at",
        "locked_at",
        "locked_by",
        "currently_reviewed_by",
        "review_started_at",
        "rejection_comment_display",
        "data_block",
        "photo_preview",
        "citizenship_front_preview",
        "citizenship_back_preview",
        "signature_preview",
        "passport_doc_preview",
        "extra_docs_preview",
    )

    # --- field layout ---
    fieldsets = (
         ("Policy Information", {
            "fields": ("policy_info_block",),
        }),
        ("Personal Information", {
            "fields": (
                ("salutation", "first_name", "middle_name", "last_name"),
                "full_name_nep",
                ("gender", "nationality"),
                ("dob_ad", "dob_bs"),
                ("email", "mobile"),
                 "marital_status", 
            )
        }),
        ("Citizenship / Document Info", {
            "fields": (
                ("citizenship_no", "citizenship_place"),
                ("citizen_ad", "citizen_bs"),
                ("passport_no", "nid_no"),
            )
        }),

        ('Family Details', {
            'fields': (
                ('spouse_name', 'father_name'),
                ('mother_name', 'grand_father_name'),
                ('father_in_law_name', 'son_name'),
                ('daughter_name', 'daughter_in_law_name'),
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
        ("AML / PEP", {"fields": ("is_pep", "is_aml")}),
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
        ("Submission Metadata", {
            "fields": (
                "user",
                "submitted_at",
                "kyc_status",
                "is_lock",
                "locked_at",
                "locked_by",
                "currently_reviewed_by",
                "review_started_at",
                "rejection_comment_display",
                "rejection_comment_input",
            )
        }),
        ("Raw JSON (Read-only)", {
            "classes": ("collapse",),
            "fields": ("data_block",),
        }),
    )

    class Media:
        js = ("kycform/js/kyc_admin.js",)

    # -------------------------------------------------------------------
    # ADDITION 1: get_form() → show/hide rejection_comment_input properly
    # -------------------------------------------------------------------
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

    # Determine current status
        if request.method == "POST":
            status = request.POST.get("kyc_status")
        else:
            status = obj.user.kyc_status if obj else None

    # FORCE Django to treat rejection_comment_input as a visible field
        if status in ["REJECTED", "INCOMPLETE"]:
            form.base_fields["rejection_comment_input"].widget = forms.Textarea(
                attrs={"rows": 3, "placeholder": "Provide rejection reason..."}
            )
            form.base_fields["rejection_comment_input"].required = True
        else:
            form.base_fields["rejection_comment_input"].widget = forms.HiddenInput()
            form.base_fields["rejection_comment_input"].required = False

        return form
    

    def policy_info_block(self, obj):
        if not obj or not obj.user:
            return "-"

        policies = (
            KycPolicy.objects
            .filter(user_id=obj.user.user_id)
            .values_list("policy_number", flat=True)  # ✅ FIXED
        )

        if not policies:
            return "No policies linked"

        return ", ".join(policies)

    policy_info_block.short_description = "Policies Linked to This User"


    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term
        )

        if search_term:
            # Find users having matching policy numbers
            user_ids = (
                KycPolicy.objects
                .filter(policy_number__icontains=search_term)
                .values_list("user_id", flat=True)
            )

            if user_ids:
                queryset = queryset | self.model.objects.filter(
                    user__user_id__in=user_ids
                )

        return queryset, use_distinct


    # -------------------------------------------------------------------
    # Soft lock
    # -------------------------------------------------------------------
    SOFT_LOCK_MINUTES = 10

    def _soft_lock_expired(self, obj):
        if not obj.review_started_at:
            return True
        delta = timezone.now() - obj.review_started_at
        return delta.total_seconds() > (self.SOFT_LOCK_MINUTES * 60)

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id)
        if not obj:
            return None

        if request.user.is_superuser:
            return obj

        now = timezone.now()

        if obj.currently_reviewed_by is None:
            obj.currently_reviewed_by = request.user
            obj.review_started_at = now
            obj.save(update_fields=["currently_reviewed_by", "review_started_at"])
            return obj

        if obj.currently_reviewed_by == request.user:
            return obj

        if self._soft_lock_expired(obj):
            obj.currently_reviewed_by = request.user
            obj.review_started_at = now
            obj.save(update_fields=["currently_reviewed_by", "review_started_at"])
            return obj

        raise PermissionDenied(
            f"This KYC form is currently being reviewed by {obj.currently_reviewed_by.username}. Try again later."
        )

    # -------------------------------------------------------------------
    # Read only rules
    # -------------------------------------------------------------------
    def get_readonly_fields(self, request, obj=None):
        base = list(self.readonly_fields)

        if request.user.is_superuser:
            return base

        if obj and obj.is_lock:
            all_fields = [f.name for f in self.model._meta.fields if f.name != "is_lock"]
            return all_fields + base

        return base + ["locked_at", "locked_by"]

    # -------------------------------------------------------------------
    # changeform_view
    # -------------------------------------------------------------------
    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        
         # ✅ Capture PRISTINE submission BEFORE admin edits (for audit)
        if object_id:
            try:
                request._old_submission = (
                    KycSubmission.objects
                    .select_related("user")
                    .get(pk=object_id)
                )
                request._old_kyc_status = request._old_submission.user.kyc_status
            except KycSubmission.DoesNotExist:
                request._old_submission = None
                request._old_kyc_status = None
        else:
            request._old_submission = None
            request._old_kyc_status = None

        try:
            obj = None
            if object_id:
                obj = self.get_object(request, object_id)

            if obj and obj.is_lock and not request.user.is_superuser:
                extra_context["show_save"] = False
                extra_context["show_save_and_add_another"] = False
                extra_context["show_delete"] = False

            if obj and obj.user and obj.user.kyc_status == "VERIFIED" and obj.is_lock and not request.user.is_superuser:
                extra_context["show_save"] = False
                extra_context["show_save_and_add_another"] = False
                extra_context["show_delete"] = False

            return super().changeform_view(request, object_id, form_url, extra_context)

        except PermissionDenied as exc:
            messages.error(request, str(exc))
            return redirect("admin:kycform_kycsubmission_changelist")

    # ---------------------------------------------------
    # ADMIN FIELD CHANGE AUDIT LOGGER
    # ---------------------------------------------------
    def _log_admin_field_changes(self, request, old_obj, new_obj):
        ignored_fields = {
            "id",
            "submitted_at",
            "data_json",
            "locked_at",
            "review_started_at",
             "version",   
            "rejection_comment",
        }

        for field in new_obj._meta.fields:
            field_name = field.name

            if field_name in ignored_fields:
                continue

            old_val = getattr(old_obj, field_name, None)
            new_val = getattr(new_obj, field_name, None)

            if old_val != new_val:
                KycChangeLog.objects.create(
                    submission=new_obj,
                    action="ADMIN_UPDATE",
                    field_name=field_name,
                    old_value=str(old_val),
                    new_value=str(new_val),
                    actor_type="ADMIN",
                    actor_identifier=request.user.username,
                )


    # -------------------------------------------------------------------
    # Save model
    # -------------------------------------------------------------------
    def save_model(self, request, obj, form, change):

        old_obj = getattr(request, "_old_submission", None)
        
        try:
            kyc_status = form.cleaned_data.get("kyc_status")
        except Exception:
            kyc_status = None
        
        # 🔒 REQUIRE COMMENT for REJECTED / INCOMPLETE
        comment = None
        if kyc_status in ["REJECTED", "INCOMPLETE"]:
            comment = form.cleaned_data.get("rejection_comment_input")
            if not comment:
                raise FormValidationError(
                    "Comment is required when marking KYC as INCOMPLETE or REJECTED."
                )

        if kyc_status == "VERIFIED" and not getattr(obj, "is_lock", False) and not request.user.is_superuser:
            raise FormValidationError(
                "KYC cannot be marked VERIFIED unless 'Is Lock' is checked."
            )

        if getattr(obj, "is_lock", False):
            obj.locked_by = request.user.username
            if not getattr(obj, "locked_at", None):
                obj.locked_at = timezone.now()

       # ✅ APPLY STATUS (NO LOGGING YET)
        if obj.user and kyc_status:
            obj.user.kyc_status = kyc_status
            obj.user.save()

        if obj.currently_reviewed_by == request.user:
            obj.currently_reviewed_by = None
            obj.review_started_at = None

        try:
            obj.version = (obj.version or 1) + 1
        except Exception:
            pass

        super().save_model(request, obj, form, change)

        old_status = getattr(request, "_old_kyc_status", None)
        new_status = obj.user.kyc_status if obj.user else None

         # ✅ LOG STATUS CHANGE (AFTER SAVE)
        if old_status and new_status and old_status != new_status:
            KycChangeLog.objects.create(
                submission=obj,
                action="STATUS_CHANGE",
                field_name="kyc_status",
                old_value=old_status or "",
                new_value=new_status or "",
                actor_type="ADMIN",
                actor_identifier=request.user.username,
            )
        # 📝 SAVE & LOG ADMIN COMMENT (REJECTED / INCOMPLETE)
        if kyc_status in ["REJECTED", "INCOMPLETE"] and comment:
            obj.rejection_comment = comment
            obj.save(update_fields=["rejection_comment"])

            comment_field = (
            "rejection_reason"
                if kyc_status == "REJECTED"
                else "incomplete_reason"
            )

            KycChangeLog.objects.create(
                submission=obj,
                action="ADMIN_COMMENT",
                field_name=comment_field,
                old_value="",
                new_value=comment,
                actor_type="ADMIN",
                actor_identifier=request.user.username,
            )

        # ✅ FIX 3: log field-level changes
        if old_obj:
            self._log_admin_field_changes(request, old_obj, obj)

    # -------------------------------------------------------------------
    # PREVIEW / DISPLAY HELPERS
    # -------------------------------------------------------------------
    def data_block(self, obj):
        import json
        return format_html(
            "<pre style='max-height:300px; overflow:auto'>{}</pre>",
            json.dumps(obj.data_json or {}, indent=2, ensure_ascii=False),
        )

    def has_photo(self, obj):
        return bool(obj.photo)

    def extra_doc_count(self, obj):
        # Count only ADDED documents linked to this submission that are current
        return KycDocument.objects.filter(submission=obj, doc_type="ADDITIONAL", is_current=True).count()

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
        """Show ALL ADDITIONAL docs stored in KycDocument."""
        if not obj:
            return "No Additional Documents"

        docs = KycDocument.objects.filter(
            submission=obj,
            doc_type="ADDITIONAL",
            is_current=True
        ).order_by("uploaded_at")

        if not docs.exists():
            return "No Additional Documents"

        html = "<ul>"

        for d in docs:
            try:
                url = d.file.url
            except Exception:
                url = None

            file_name = d.file_name or "Document"

            if url:
                html += f'<li><a href="{url}" target="_blank">{file_name}</a></li>'
            else:
                html += f"<li>{file_name}</li>"

        html += "</ul>"
        return mark_safe(html)


    def kyc_status_colored(self, obj):
        status = (obj.user.kyc_status if getattr(obj, "user", None) else None) or "UNKNOWN"
        color = {
            "NOT_INITIATED": "gray",
            "PENDING": "orange",
            "INCOMPLETE": "blue",
            "VERIFIED": "green",
            "REJECTED": "red",
        }.get(status, "black")
        return format_html("<b style='color:{}'>{}</b>", color, status)

    def rejection_comment_display(self, obj):
        if obj.user.kyc_status != "REJECTED":
            return "—"
        if not obj.rejection_comment:
            return "—"
        return format_html(
            "<div style='white-space:pre-wrap; border:1px solid #555; padding:8px; "
            "background:#111; border-radius:4px;'>{}</div>",
            obj.rejection_comment,
        )
    rejection_comment_display.short_description = "Rejection Comment"

    # -------------------------------------------------------------------
    # ADDITION 2: get_fieldsets() → Insert rejection_comment_input when REJECTED
    # -------------------------------------------------------------------
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        final_sets = []

        # Determine selected status
        if request.method == "POST":
            status = request.POST.get("kyc_status")
        else:
            status = obj.user.kyc_status if obj else None
        for title, options in fieldsets:
            fields = list(options.get("fields", []))

            # Identify the correct fieldset by field membership (not title!)
            # if "kyc_status" in fields and "is_lock" in fields:
                # This is guaranteed to be the Submission Metadata section
            if title == "Submission Metadata":
                    if status in ["REJECTED", "INCOMPLETE"]:
                        if "rejection_comment_input" not in fields:
                            fields.append("rejection_comment_input")

            options["fields"] = tuple(fields)
            final_sets.append((title, options))

        return final_sets

    def _clear_soft_lock(self, request, obj):
        if obj and obj.currently_reviewed_by == request.user:
            obj.currently_reviewed_by = None
            obj.review_started_at = None
            obj.save(update_fields=["currently_reviewed_by", "review_started_at"])

    def response_change(self, request, obj):
        # User pressed "Close" or navigated away after form load
        response = super().response_change(request, obj)
        self._clear_soft_lock(request, obj)
        return response
    def response_post_save_change(self, request, obj):
        response = super().response_post_save_change(request, obj)
        self._clear_soft_lock(request, obj)
        return response

    def response_post_save_add(self, request, obj):
        response = super().response_post_save_add(request, obj)
        self._clear_soft_lock(request, obj)
        return response

    # -------------------------------------------------------------------
    # ACTIONS
    # -------------------------------------------------------------------
    actions = None
    def _apply_review(self, request, queryset, new_status, comment):
        now = timezone.now().isoformat()
        for sub in queryset:
            sub.user.kyc_status = new_status
            sub.user.save()

            audit = {
                "status": new_status,
                "reviewed_by": request.user.username,
                "reviewed_at": now,
                "comment": comment or "",
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

    def mark_incomplete(self, request, queryset):
        self._apply_review(request, queryset, "INCOMPLETE", "Incomplete – needs correction")
        self.message_user(request, "Selected KYC marked INCOMPLETE.")
    mark_incomplete.short_description = "Mark as INCOMPLETE"

    def mark_rejected_with_comment(self, request, queryset):
        if "apply" in request.POST:
            form = RejectCommentForm(request.POST)
            if form.is_valid():
                comment = form.cleaned_data["comment"]
                now = timezone.now().isoformat()
                for sub in queryset:
                    sub.user.kyc_status = "REJECTED"
                    sub.user.save()
                    sub.rejection_comment = comment
                    audit = {
                        "status": "REJECTED",
                        "reviewed_by": request.user.username,
                        "reviewed_at": now,
                        "comment": comment,
                    }
                    data = sub.data_json or {}
                    data.setdefault("review_history", []).append(audit)
                    data["last_review"] = audit
                    sub.data_json = data
                    sub.save()
                self.message_user(request, "Selected KYC rejected with reason.")
                return redirect(request.get_full_path())
        else:
            form = RejectCommentForm(
                initial={"_selected_action": request.POST.getlist(admin.ACTION_CHECKBOX_NAME)}
            )
            return render(request, "admin/reject_comment.html", {"form": form})

    mark_rejected_with_comment.short_description = "Reject with reason (show comment form)"

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        return initial


@admin.register(KycChangeLog)
class KycChangeLogAdmin(admin.ModelAdmin):
    list_display = (
        "submission",
        "action",
        "field_name",
        "actor_type",
        "actor_identifier",
        "created_at",
    )
    list_filter = ("action", "actor_type", "created_at")
    search_fields = ("field_name", "old_value", "new_value", "actor_identifier")
    readonly_fields = [f.name for f in KycChangeLog._meta.fields]

    # 🔐 FORCE VISIBILITY IN SIDEBAR
    def has_module_permission(self, request):
        return True

    # 🔒 HARD READ-ONLY (AUDIT SAFE)
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
# -------------------------------------------------------
# KycMobileOTP Admin

@admin.register(KycMobileOTP)
class KycMobileOTPAdmin(admin.ModelAdmin):
    list_display = (
        "kyc_user",
        "mobile",
        "is_verified",
        "expires_at",
        "created_at",
    )

    list_filter = ("is_verified",)
    search_fields = (
        "kyc_user__user_id",
        "mobile",
    )
    ordering = ("-created_at",)
