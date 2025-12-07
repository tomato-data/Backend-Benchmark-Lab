from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
import time

from .models import User
from .serializers import UserSerializer, UserCreateSerializer

# Create your views here.
SERVER_NAME = "python-django"


class HealthView(APIView):
    def get(self, request):
        return Response({"status": "ok", "server": SERVER_NAME})


class EchoView(APIView):
    def post(self, request):
        return Response(request.data)  # 받은 JSON 그대로 반환


class UserListView(APIView):
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserSerializer(user).data)


class ExternalAPIView(APIView):
    def get(self, request):
        # 100ms 지연 시뮬레이션
        start = time.perf_counter()

        # 100ms 대기 시뮬레이션 (Django는 동기이므로 time.sleep)
        time.sleep(0.1)

        latency = (time.perf_counter() - start) * 1000

        return Response(
            {
                "source": "simulated_external_api",
                "latency_ms": round(latency, 2),
                "data": {"message": "External API response"},
            }
        )


class ProtectedView(APIView):
    def get(self, request):
        # 헤더 검증
        auth = request.headers.get("Authorization", "")
        request_id = request.headers.get("X-Request-ID", "")

        if not auth.startswith("Bearer "):
            return Response(
                {"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        return Response({"message": "Access granted", "request_id": request_id})


class UploadView(APIView):
    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"detail": "No file"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"filename": file.name, "size": file.size})
