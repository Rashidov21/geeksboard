from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.mentor_register, name='register'),
    path('login/', views.MentorLoginView.as_view(), name='login'),
    path('logout/', views.MentorLogoutView.as_view(), name='logout'),
    path('', views.dashboard, name='dashboard'),
    # Groups
    path('groups/', views.group_list, name='group_list'),
    path('groups/create/', views.group_create, name='group_create'),
    # Group-specific routes (more specific first)
    path('groups/<int:group_id>/students/create/', views.student_create, name='student_create'),
    path('groups/<int:group_id>/rating/', views.student_rating, name='student_rating'),
    path('groups/<int:group_id>/edit/', views.group_edit, name='group_edit'),
    path('groups/<int:group_id>/delete/', views.group_delete, name='group_delete'),
    path('groups/<int:group_id>/', views.student_list, name='student_list'),
    path('students/<int:student_id>/', views.student_profile, name='student_profile'),
    path('students/<int:student_id>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:student_id>/delete/', views.student_delete, name='student_delete'),
    # Points
    path('points/<int:point_id>/edit/', views.point_edit, name='point_edit'),
    path('points/<int:point_id>/delete/', views.delete_point, name='delete_point'),
    # Interactive
    path('interactive/', views.interactive_categories, name='interactive_categories'),
    path('interactive/<int:category_id>/', views.interactive_question, name='interactive_question'),
    path('best-student/', views.best_student, name='best_student'),
]


