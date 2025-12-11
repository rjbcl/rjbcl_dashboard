# kycform/api_views.py
"""
JWT-based API endpoints for React frontend.
These coexist with your existing session-based views.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from django.db import transaction
import json

from .models import KycPolicy, KycUserInfo, KYCTemporary, KycSubmission
from .views import (
    normalize_status, 
    safe_model_dict, 
    process_kyc_submission,
    _save_files_and_submission
)
from django.forms.models import model_to_dict


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def api_policyholder_login(request):
    """
    JWT login endpoint for React frontend.
    Returns JWT tokens + user data.
    """
    policy_no = request.data.get("policy_no")
    password = request.data.get("password")

    if not policy_no or not password:
        return Response(
            {"error": "Policy number and password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        policy = KycPolicy.objects.get(policy_number__iexact=policy_no)
        user = KycUserInfo.objects.get(user_id=policy.user_id)
    except Exception:
        return Response(
            {"error": "Invalid policy number or user not found."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Check if password is set (user registered)
    if not user.password or user.password.strip() == "":
        return Response(
            {"error": "You are not registered. Please create an account."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Validate password
    if not check_password(password, user.password):
        return Response(
            {"error": "Incorrect password!"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Generate JWT tokens
    refresh = RefreshToken()
    refresh['user_id'] = user.user_id
    refresh['policy_no'] = policy_no

    kyc_status = normalize_status(user.kyc_status)

    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': {
            'user_id': user.user_id,
            'policy_no': policy_no,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone_number': user.phone_number,
            'kyc_status': kyc_status,
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """
    Logout endpoint (optional - frontend can just discard tokens).
    """
    return Response({'message': 'Logout successful'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_user_profile(request):
    """
    Get current user profile.
    Uses JWT token to identify user.
    """
    # Extract user_id from JWT token
    user_id = request.auth.payload.get('user_id')
    
    try:
        user = KycUserInfo.objects.get(user_id=user_id)
        policy = KycPolicy.objects.filter(user_id=user_id).first()
        
        return Response({
            'user_id': user.user_id,
            'policy_no': policy.policy_number if policy else None,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone_number': user.phone_number,
            'kyc_status': normalize_status(user.kyc_status),
        })
    except KycUserInfo.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )


# ============================================================================
# KYC DATA ENDPOINTS
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_get_kyc_data(request):
    """
    Get KYC form data (prefill) for React frontend.
    Same logic as kyc_form_view but returns JSON.
    """
    user_id = request.auth.payload.get('user_id')
    policy_no = request.auth.payload.get('policy_no')

    if not policy_no:
        return Response(
            {"error": "Policy number not found in token"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        policy = KycPolicy.objects.get(policy_number=policy_no)
        user = KycUserInfo.objects.get(user_id=policy.user_id)
    except Exception:
        return Response(
            {"error": "User or policy not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    # Stop if verified or pending
    if user.kyc_status in ["PENDING", "VERIFIED"]:
        return Response({
            "status": user.kyc_status,
            "message": "KYC already submitted",
            "can_edit": False
        })

    # Load rejection message if rejected
    rejection_message = None
    if user.kyc_status == "REJECTED":
        try:
            sub = KycSubmission.objects.get(user=user)
            rejection_message = sub.rejection_comment or "Your KYC was rejected. Please review and resubmit."
        except KycSubmission.DoesNotExist:
            rejection_message = "Your KYC was rejected. Please review and resubmit."

    # Load three sources (same as kyc_form_view)
    user_info = safe_model_dict(model_to_dict(user, exclude=["password"]))

    try:
        submission = KycSubmission.objects.get(user=user)
        submission_data = safe_model_dict(
            model_to_dict(submission, exclude=["id", "user", "submitted_at"])
        )
    except KycSubmission.DoesNotExist:
        submission = None
        submission_data = {}

    try:
        temp = KYCTemporary.objects.get(policy_no=policy_no)
        temp_data = safe_model_dict(temp.data_json)
    except KYCTemporary.DoesNotExist:
        temp_data = {}

    # Merge priority (temp > submission > user)
    merged = user_info.copy()
    for k, v in submission_data.items():
        if v not in [None, "", [], {}]:
            merged[k] = v
    for k, v in temp_data.items():
        if v not in [None, "", [], {}]:
            merged[k] = v

    # Normalize marital_status
    ms = merged.get("marital_status")
    if ms:
        s = str(ms).strip().lower()
        if s in ["married", "m", "1", "yes", "true", "विवाहित"]:
            merged["marital_status"] = "Married"
        elif s in ["unmarried", "single", "u", "0", "no", "false", "अविवाहित"]:
            merged["marital_status"] = "Unmarried"
        else:
            merged["marital_status"] = None
    else:
        merged["marital_status"] = None

    # File URLs
    if submission:
        merged["photo_url"] = submission.photo.url if submission.photo else None
        merged["citizenship_front_url"] = submission.citizenship_front.url if submission.citizenship_front else None
        merged["citizenship_back_url"] = submission.citizenship_back.url if submission.citizenship_back else None
        merged["signature_url"] = submission.signature.url if submission.signature else None
        merged["passport_doc_url"] = submission.passport_doc.url if submission.passport_doc else None
        merged["additional_docs"] = submission.additional_docs or []

    return Response({
        "kyc_data": merged,
        "rejection_message": rejection_message,
        "policy_no": policy_no,
        "can_edit": True
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_save_kyc_progress(request):
    """
    Save & Continue endpoint for React.
    Accepts multipart/form-data.
    """
    user_id = request.auth.payload.get('user_id')
    policy_no = request.auth.payload.get('policy_no')

    # Use existing save_kyc_progress logic but return JSON
    from .views import save_kyc_progress as original_save
    
    # Temporarily set session data for compatibility with existing code
    request.session = {}
    request.session['authenticated'] = True
    request.session['policy_no'] = policy_no
    
    # Call original function (it returns JsonResponse already)
    return original_save(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_submit_kyc(request):
    """
    Final KYC submission endpoint for React.
    Accepts multipart/form-data.
    """
    user_id = request.auth.payload.get('user_id')
    policy_no = request.auth.payload.get('policy_no')

    # Set session for compatibility
    request.session = {}
    request.session['authenticated'] = True
    request.session['policy_no'] = policy_no

    try:
        user = process_kyc_submission(request)
        return Response({
            "status": "success",
            "message": "KYC submitted successfully",
            "kyc_status": user.kyc_status
        })
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


# ============================================================================
# REGISTRATION ENDPOINT
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def api_policyholder_register(request):
    """
    Registration endpoint for React frontend.
    Uses same logic as policyholder_register_view.
    """
    from .views import generate_user_id
    from django.contrib.auth.hashers import make_password
    from django.db import connection
    from django.utils import timezone
    
    policy_no = request.data.get("policy_number", "").strip()
    mobile = request.data.get("mobile", "").strip()
    dob_ad = request.data.get("dob_ad", "").strip()
    first_name = request.data.get("first_name", "").strip()
    last_name = request.data.get("last_name", "").strip()
    email = request.data.get("email")

    if not (policy_no and mobile and dob_ad and first_name and last_name):
        return Response(
            {"error": "All fields are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if already registered
    kp = KycPolicy.objects.filter(policy_number__iexact=policy_no).first()
    if kp and kp.user_id:
        return Response(
            {"error": "This policy is already registered. Please login."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Lookup in core
    with connection.cursor() as cur:
        cur.execute("""
            SELECT policyno, firstname, lastname, dob, mobile
            FROM tblinsureddetail
            WHERE policyno = %s
            LIMIT 1
        """, [policy_no])
        row = cur.fetchone()

    if not row:
        return Response(
            {"error": "Policy not found in core system."},
            status=status.HTTP_404_NOT_FOUND
        )

    core_policy_no, core_first, core_last, core_dob, core_mobile = row

    # Validate DOB and mobile
    if str(core_dob) != str(dob_ad):
        return Response(
            {"error": "DOB does not match our records."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if str(core_mobile).strip() != mobile.strip():
        return Response(
            {"error": "Mobile number does not match our records."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Find related policies
    with connection.cursor() as cur:
        cur.execute("""
            SELECT policyno
            FROM tblinsureddetail
            WHERE firstname = %s
              AND lastname = %s
              AND dob = %s
              AND mobile = %s
        """, [core_first, core_last, core_dob, core_mobile])
        related = [r[0] for r in cur.fetchall()]

    related_policy_numbers = set(related)
    related_policy_numbers.add(policy_no)

    # Check existing user_id
    existing = (
        KycPolicy.objects
        .filter(policy_number__in=list(related_policy_numbers), user_id__isnull=False)
        .exclude(user_id="")
        .first()
    )

    if existing:
        user_id = existing.user_id
    else:
        user_id = generate_user_id(core_first, core_last, core_dob, core_mobile)

    try:
        with transaction.atomic():
            user_obj, created = KycUserInfo.objects.get_or_create(
                user_id=user_id,
                defaults={
                    "first_name": first_name or core_first,
                    "last_name": last_name or core_last,
                    "dob": core_dob,
                    "email": email,
                    "phone_number": mobile,
                }
            )

            if not created:
                if user_obj.phone_number and user_obj.phone_number != mobile:
                    return Response(
                        {"error": "Mobile does not match existing account."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Assign user_id to all related policies
            for pn in related_policy_numbers:
                loc = KycPolicy.objects.filter(policy_number__iexact=pn).first()
                if loc:
                    if loc.user_id != user_id:
                        loc.user_id = user_id
                        loc.save()
                else:
                    KycPolicy.objects.create(
                        policy_number=pn,
                        user_id=user_id,
                        created_at=timezone.now().date()
                    )

            # Set default password (hashed DOB)
            if not user_obj.password:
                raw_default = str(core_dob).replace("-", "")
                user_obj.password = make_password(raw_default)
                user_obj.save()

        return Response({
            "status": "success",
            "message": "Registration successful. Please login with password = DOB (YYYYMMDD)."
        })

    except Exception as e:
        return Response(
            {"error": f"Registration failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )