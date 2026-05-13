from django.urls import path

from . import views


urlpatterns = [
    path('', views.StaffDashboardView.as_view(), name='staff-dashboard'),
    path('courses/', views.StaffCourseListView.as_view(), name='staff-course-list'),
    path('courses/create/', views.StaffCourseCreateView.as_view(), name='staff-course-create'),
    path('courses/<int:pk>/edit/', views.StaffCourseEditView.as_view(), name='staff-course-edit'),
    path('courses/<int:pk>/delete/', views.StaffCourseDeleteView.as_view(), name='staff-course-delete'),
    path('courses/<int:course_pk>/lessons/create/', views.StaffLessonCreateView.as_view(), name='staff-lesson-create'),
    path('courses/<int:course_pk>/lessons/<int:pk>/edit/', views.StaffLessonEditView.as_view(), name='staff-lesson-edit'),
    path('courses/<int:course_pk>/lessons/<int:pk>/delete/', views.StaffLessonDeleteView.as_view(), name='staff-lesson-delete'),
    path('courses/<int:course_pk>/quiz/<str:quiz_type>/', views.StaffQuizEditView.as_view(), name='staff-quiz-edit'),
    path('courses/<int:course_pk>/quiz/<str:quiz_type>/questions/create/', views.StaffQuestionCreateView.as_view(), name='staff-question-create'),
    path('courses/<int:course_pk>/quiz/<str:quiz_type>/questions/<int:pk>/edit/', views.StaffQuestionEditView.as_view(), name='staff-question-edit'),
    path('courses/<int:course_pk>/quiz/<str:quiz_type>/questions/<int:pk>/delete/', views.StaffQuestionDeleteView.as_view(), name='staff-question-delete'),
    path('courses/<int:pk>/report/', views.StaffCourseReportView.as_view(), name='staff-course-report'),
    path('courses/<int:pk>/report/export/', views.StaffCourseReportExportView.as_view(), name='staff-course-report-export'),
    path('users/import/', views.BulkUserImportView.as_view(), name='staff-bulk-user-import'),
]
