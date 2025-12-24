from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCSRFToken(APIView):
    def get(self, request):
        return Response({'detail': 'CSRF cookie set'})

@method_decorator(csrf_protect, name='dispatch')
class PolicyHolderLoginView(APIView):
    def post(self, request):
        policy_number = request.data.get('policy_number')
        password = request.data.get('password')

        if not policy_number or not password:
            return Response(
                {'error': 'Please provide both policy number and password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate using policy number as username
        user = authenticate(request, username=policy_number, password=password)

        if user is not None:
            login(request, user)
            return Response({
                'detail': 'Successfully logged in',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Invalid policy number or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )

@method_decorator(csrf_protect, name='dispatch')
class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response({'detail': 'Successfully logged out'}, status=status.HTTP_200_OK)

class CheckAuthView(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                'isAuthenticated': True,
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'email': request.user.email,
                }
            })
        return Response({'isAuthenticated': False})