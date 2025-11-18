from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.mentor_register, name='register'),
    path('login/', views.MentorLoginView.as_view(), name='login'),
    path('logout/', views.MentorLogoutView.as_view(), name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('groups/', views.group_list, name='group_list'),
    path('groups/<int:group_id>/', views.student_list, name='student_list'),
    path('groups/<int:group_id>/rating/', views.student_rating, name='student_rating'),
    path('students/<int:student_id>/', views.student_profile, name='student_profile'),
    path('points/<int:point_id>/delete/', views.delete_point, name='delete_point'),
    path('interactive/', views.interactive_categories, name='interactive_categories'),
    path('interactive/<int:category_id>/', views.interactive_question, name='interactive_question'),
    path('best-student/', views.best_student, name='best_student'),
]


