from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuthViewSet, SkillViewSet, CandidateViewSet,
    CompanyViewSet, JobViewSet, ApplicationViewSet,
    SavedJobViewSet, AIMatchingAPIView, BIDashboardViewSet
)

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'skills', SkillViewSet, basename='skill')
router.register(r'candidates', CandidateViewSet, basename='candidate')
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'applications', ApplicationViewSet, basename='application')
router.register(r'saved-jobs', SavedJobViewSet, basename='saved-job')
router.register(r'bi', BIDashboardViewSet, basename='bi')

urlpatterns = [
    path('', include(router.urls)),
    path('ai/match/', AIMatchingAPIView.as_view(), name='ai-match'),
]
