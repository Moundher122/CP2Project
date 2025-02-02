
from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [
    path('opportunity/', views.opportunity_crud.as_view()),
    path('team/',views.team_crud.as_view()),
    path('team/managing/',views.team_managing.as_view()),
    path('application/<int:id>/',views.applications.as_view())
]