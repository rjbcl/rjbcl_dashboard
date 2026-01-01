import secrets
from django.core.cache import cache
from django.contrib.auth.hashers import check_password
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.middleware.csrf import get_token

# Import your models (replace 'kycform' with your actual app name)
from kycform.models import KycPolicy, KycUserInfo, KycSubmission, KycChangeLog
from kycform.views import resolve_policy_identity  # Import your existing function
from django.core.exceptions import ValidationError


def normalize_status(status_value):
    """Helper function to normalize KYC status"""
    if not status_value:
        return ""
    return str(status_value).strip().upper()


@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCSRFToken(APIView):
    def get(self, request):
        csrf_token = get_token(request)
        return Response({
            'detail': 'CSRF cookie set',
            'csrfToken': csrf_token
        })


@method_decorator(csrf_protect, name='dispatch')
class PolicyHolderLoginView(APIView):
    def post(self, request):
        policy_no = request.data.get('policy_number')
        password = request.data.get('password')

        # Validation
        if not policy_no or not password:
            return Response(
                {'error': 'Policy number and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Strip whitespace
        policy_no = policy_no.strip()
        password = password.strip()

        # --------------------------------------
        # Validate policy + user
        # --------------------------------------
        try:
            policy = KycPolicy.objects.get(policy_number__iexact=policy_no)
            user = KycUserInfo.objects.get(user_id=policy.user_id)
        except KycPolicy.DoesNotExist:
            return Response(
                {'error': 'Invalid policy number or user not found.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except KycUserInfo.DoesNotExist:
            return Response(
                {'error': 'Invalid policy number or user not found.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {'error': 'An error occurred. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # --------------------------------------
        # Check if password is set (user registered or not)
        # --------------------------------------
        if not user.password or user.password.strip() == "":
            return Response(
                {'error': 'You are not registered. Please create an account.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # --------------------------------------
        # Validate password using Django hashing
        # --------------------------------------
        if not check_password(password, user.password):
            return Response(
                {'error': 'Incorrect password!'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # --------------------------------------
        # SUCCESSFUL LOGIN → SET SESSION
        # --------------------------------------
        request.session['authenticated'] = True
        request.session['policy_no'] = policy_no
        request.session.save()

        # Generate a one-time token for cross-origin redirect
        token = secrets.token_urlsafe(32)
        cache.set(f'login_token_{token}', {
            'policy_no': policy_no,
            'authenticated': True
        }, timeout=60)  # 60 second expiry

        # --------------------------------------
        # KYC routing logic
        # --------------------------------------
        kyc_status = normalize_status(user.kyc_status)
        
        # Determine redirect URL with token
        if kyc_status in ["NOT_INITIATED", "INCOMPLETE", "REJECTED", ""]:
            redirect_url = f"http://localhost:8000/kyc-form/?policy_no={policy_no}&token={token}"
        elif kyc_status in ["PENDING", "VERIFIED"]:
            redirect_url = f"http://localhost:8000/dashboard/?policy_no={policy_no}&token={token}"
        else:
            redirect_url = f"http://localhost:8000/kyc-form/?policy_no={policy_no}&token={token}"

        return Response({
            'detail': 'Successfully logged in',
            'success': True,
            'user': {
                'policy_number': policy_no,
                'user_id': user.user_id,
                'kyc_status': kyc_status,
            },
            'redirect_url': redirect_url
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_protect, name='dispatch')
class LogoutView(APIView):
    def post(self, request):
        request.session.flush()
        return Response({
            'detail': 'Successfully logged out'
        }, status=status.HTTP_200_OK)


class CheckAuthView(APIView):
    def get(self, request):
        is_authenticated = request.session.get('authenticated', False)
        policy_no = request.session.get('policy_no', None)
        
        if is_authenticated and policy_no:
            try:
                policy = KycPolicy.objects.get(policy_number__iexact=policy_no)
                user = KycUserInfo.objects.get(user_id=policy.user_id)
                
                return Response({
                    'isAuthenticated': True,
                    'user': {
                        'policy_number': policy_no,
                        'user_id': user.user_id,
                        'kyc_status': normalize_status(user.kyc_status),
                    }
                })
            except Exception:
                request.session.flush()
                return Response({'isAuthenticated': False})
        
        return Response({'isAuthenticated': False})
    



@method_decorator(csrf_protect, name='dispatch')
class DirectKYCEntryView(APIView):
    """
    Direct KYC entry without login.
    User provides policy number and DOB to access KYC form.
    """
    
    def post(self, request):
        policy_no = (request.data.get('policy_no') or '').strip()
        dob_ad = (request.data.get('dob_ad') or '').strip()

        # Validation
        if not policy_no or not dob_ad:
            return Response(
                {'error': 'Policy number and date of birth are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # -------------------------------------------------
        # VALIDATE POLICY + DOB (using your existing function)
        # -------------------------------------------------
        try:
            user, user_id = resolve_policy_identity(
                policy_no=policy_no,
                dob_ad=dob_ad,
            )
        except ValidationError:
            return Response(
                {'error': 'Invalid policy number or date of birth. Please check and try again.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {'error': 'An error occurred. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # -------------------------------------------------
        # 🚫 BLOCK DIRECT KYC FOR NON-EDITABLE STATUS
        # -------------------------------------------------
        if user.kyc_status in ["PENDING", "VERIFIED"]:
            return Response(
                {'error': 'KYC already submitted. Please contact your branch for further assistance.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # -------------------------------------------------
        # 🔐 CLEAN SESSION (CRITICAL)
        # -------------------------------------------------
        request.session.flush()
        request.session.cycle_key()

        # -------------------------------------------------
        # SESSION BINDING (STRICT)
        # -------------------------------------------------
        request.session["kyc_access_mode"] = "DIRECT_KYC"
        request.session["kyc_policy_no"] = policy_no
        request.session["kyc_user_id"] = user_id
        request.session["kyc_dob"] = user.dob.isoformat()
        request.session.save()

        # -------------------------------------------------
        # AUDIT LOG
        # -------------------------------------------------
        submission = KycSubmission.objects.filter(user=user).first()
        if submission:
            KycChangeLog.objects.create(
                submission=submission,
                action="CREATE",
                actor_type="SYSTEM",
                actor_identifier="DIRECT_KYC",
                comment=f"Direct KYC access granted for policy {policy_no}",
            )

        # Generate one-time token for redirect
        token = secrets.token_urlsafe(32)
        cache.set(f'direct_kyc_token_{token}', {
            'kyc_access_mode': 'DIRECT_KYC',
            'kyc_policy_no': policy_no,
            'kyc_user_id': user_id,
            'kyc_dob': user.dob.isoformat(),
        }, timeout=60)

        # Build redirect URL
        redirect_url = f"http://localhost:8000/kyc-form/?token={token}"

        return Response({
            'detail': 'Access granted',
            'success': True,
            'user': {
                'policy_number': policy_no,
                'user_id': user_id,
            },
            'redirect_url': redirect_url
        }, status=status.HTTP_200_OK)