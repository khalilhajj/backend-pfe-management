from django.urls import path
from .views import  ReportView

urlpatterns = [
    path('reports/', ReportView.as_view(), name='reports'),
]