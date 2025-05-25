from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from . import company_dashboard

urlpatterns = [
    path('Login',views.Login.as_view()),
    path('Signup',views.Signup.as_view()),
    path('Refresh',TokenRefreshView.as_view()),
    path('user',views.acc.as_view()),
    path('otpemail',views.ForgotPass.as_view()),
    path('user/<int:id>/',views.getuser.as_view()),
    path('user/<str:name>/',views.getuserwithname.as_view()),
    path('userpassword',views.reset_password.as_view()),
    path('post/<int:id>/',views.savedpost.as_view()),
    path('post',views.post.as_view()),
    path('Fcm',views.Fcm.as_view()),
    path('google',views.GoogleAuthenticate.as_view()),
    path('usertype',views.addtype.as_view()),
    path('googleauthforapp/',views.googleauthforapp.as_view()),
    path('linkedin',views.LinkedInAuthenticate.as_view()),
    path('notfi',views.notfication.as_view()),
    path('notif/<int:id>/',views.notfi.as_view()),
    path('try',views.Try.as_view()),
    path('logout',views.logout.as_view()),
    path('company/dashboard/opportunities/', company_dashboard.CompanyDashboard.as_view()),
    path('company/dashboard/recent/', company_dashboard.CompanyDashboard.as_view()),
    path('company/dashboard/all-applications/', company_dashboard.CompanyDashboard.as_view()),
    path('company/dashboard/applications/<int:postId>/', company_dashboard.CompanyDashboard.as_view()),
    path('company/dashboard/chart-data/', company_dashboard.CompanyDashboard.as_view()),
    path('company/dashboard/status-counts/', company_dashboard.CompanyDashboard.as_view()),
    path('company/dashboard/status-pie-chart/', company_dashboard.CompanyDashboard.as_view()),
    path('try',views.Try.as_view()),
]
