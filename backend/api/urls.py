from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuthViewSet, SkillViewSet, CandidateViewSet,
    CompanyViewSet, JobViewSet, ApplicationViewSet,
    SavedJobViewSet, AIMatchingAPIView, BIDashboardViewSet,
    ExtractSkillsAPIView, ParseCVAPIView, RecommendJobsAPIView, AIEvaluationAPIView
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
    path('ai/extract-skills/', ExtractSkillsAPIView.as_view(), name='ai-extract-skills'),
    path('ai/parse-cv/', ParseCVAPIView.as_view(), name='ai-parse-cv'),
    path('ai/recommend-jobs/', RecommendJobsAPIView.as_view(), name='ai-recommend-jobs'),
    path('ai/evaluation/', AIEvaluationAPIView.as_view(), name='ai-evaluation'),
]
