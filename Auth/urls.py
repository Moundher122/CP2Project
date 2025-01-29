from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
urlpatterns = [
    path('Login',views.Login.as_view()),
    path('Signup',views.Signup.as_view()),
    path('Refresh',TokenRefreshView.as_view()),
    path('user',views.Deleteacc.as_view())
]
