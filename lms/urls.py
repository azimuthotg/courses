from django.urls import path
from . import views

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course-list'),
    path('login/', views.LMSLoginView.as_view(), name='login'),
    path('logout/', views.LMSLogoutView.as_view(), name='logout'),
    path('course/<int:pk>/', views.CourseDetailView.as_view(), name='course-detail'),
    path('course/<int:course_pk>/lesson/<int:lesson_pk>/', views.LessonView.as_view(), name='lesson'),
    path('course/<int:course_pk>/quiz/<str:quiz_type>/', views.QuizView.as_view(), name='quiz'),
    path('certificate/<int:course_pk>/', views.CertificateDownloadView.as_view(), name='certificate'),
]
