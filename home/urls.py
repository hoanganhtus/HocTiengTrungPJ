from django.urls import path
from . import views  # Import views từ thư mục hiện tại

urlpatterns = [
    # Đường dẫn rỗng '' nghĩa là trang chủ
    path("", views.home_view, name="home"),
    path("add-vocabulary/", views.add_vocabulary_view, name="add_vocabulary"),
]
