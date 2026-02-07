from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from .ai_engine import chay_gia_su  # Import hàm AI của bạn


def home(request):
    return render(request, "index.html")


@method_decorator(csrf_exempt, name="dispatch")
class ChatAPI(APIView):
    def post(self, request):
        text = request.data.get("message")
        if not text:
            return Response({"error": "No message"}, status=400)

        # Gọi con Bot xịn xò của bạn
        reply = chay_gia_su(text)

        return Response({"reply": reply})
