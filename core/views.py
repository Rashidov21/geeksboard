import calendar
from datetime import date
from typing import Optional

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db import models
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_http_methods

from .forms import MentorRegistrationForm, StudentPointForm
from .models import Group, InteractiveCategory, PointCategory, Student, StudentPoint


def _current_month_range(target_date: Optional[date] = None):
    today = target_date or date.today()
    start = today.replace(day=1)
    _, last_day = calendar.monthrange(today.year, today.month)
    end = today.replace(day=last_day)
    return start, end


def _require_mentor(request):
    mentor = getattr(request.user, 'mentor_profile', None)
    if not mentor:
        messages.error(request, 'No mentor profile linked to this account.')
        return None
    return mentor


def mentor_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = MentorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to GeeksBoard.')
            return redirect('dashboard')
    else:
        form = MentorRegistrationForm()
    
    return render(request, 'register.html', {'form': form})


class MentorLoginView(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        return reverse('dashboard')


class MentorLogoutView(LogoutView):
    next_page = reverse_lazy('login')


@login_required
def dashboard(request):
    mentor = _require_mentor(request)
    if not mentor:
        return redirect('login')

    groups = mentor.groups.prefetch_related('students')
    student_ids = Student.objects.filter(group__mentor=mentor).values_list('id', flat=True)
    start, end = _current_month_range()

    leaderboard = (
        Student.objects.filter(id__in=student_ids)
        .annotate(
            month_total=Sum(
                'points__score',
                filter=models.Q(points__date__date__range=(start, end)),
                default=0,
            )
        )
        .order_by('-month_total', 'full_name')[:5]
    )

    stats = {
        'group_count': groups.count(),
        'student_count': sum(group.students.count() for group in groups),
        'point_entries': StudentPoint.objects.filter(student__group__mentor=mentor).count(),
    }

    recent_points = (
        StudentPoint.objects.filter(student__group__mentor=mentor)
        .select_related('student', 'category')
        .order_by('-date')[:5]
    )

    context = {
        'mentor': mentor,
        'groups': groups,
        'leaderboard': leaderboard,
        'stats': stats,
        'recent_points': recent_points,
        'categories': PointCategory.objects.filter(is_active=True),
        'interactive_categories': InteractiveCategory.objects.filter(is_active=True)[:4],
    }
    return render(request, 'dashboard.html', context)


@login_required
def group_list(request):
    mentor = _require_mentor(request)
    if not mentor:
        return redirect('login')

    groups = mentor.groups.annotate(student_total=Count('students')).order_by('name')
    return render(request, 'group_list.html', {'groups': groups, 'mentor': mentor})


@login_required
def student_list(request, group_id: int):
    mentor = _require_mentor(request)
    if not mentor:
        return redirect('login')

    group = get_object_or_404(Group, id=group_id, mentor=mentor)
    students = (
        group.students.annotate(total_points=Sum('points__score', default=0))
        .prefetch_related('points__category')
        .order_by('full_name')
    )
    form = StudentPointForm()

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        form = StudentPointForm(request.POST)
        if student_id and form.is_valid():
            target_student = get_object_or_404(Student, id=student_id, group=group)
            point = form.save(commit=False)
            point.student = target_student
            point.save()
            action = 'added' if point.score > 0 else 'removed'
            messages.success(request, f'Points {action} for {target_student.full_name}.')
            return redirect('student_list', group_id=group.id)
        messages.error(request, 'Please correct the errors in the form.')

    context = {
        'group': group,
        'students': students,
        'form': form,
        'categories': PointCategory.objects.filter(is_active=True),
    }
    return render(request, 'student_list.html', context)


@login_required
def student_profile(request, student_id: int):
    mentor = _require_mentor(request)
    if not mentor:
        return redirect('login')

    student = get_object_or_404(Student, id=student_id, group__mentor=mentor)
    points = student.points.select_related('category').order_by('-date')
    
    total_points = sum(p.score for p in points)
    
    context = {
        'student': student,
        'points': points,
        'total_points': total_points,
    }
    return render(request, 'student_profile.html', context)


@login_required
@require_http_methods(["POST"])
def delete_point(request, point_id: int):
    mentor = _require_mentor(request)
    if not mentor:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=403)
    
    point = get_object_or_404(StudentPoint, id=point_id, student__group__mentor=mentor)
    student_name = point.student.full_name
    point.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': f'Point entry deleted for {student_name}'})
    
    messages.success(request, f'Point entry deleted for {student_name}.')
    return redirect('student_profile', student_id=point.student.id)


@login_required
def student_rating(request, group_id: int):
    mentor = _require_mentor(request)
    if not mentor:
        return redirect('login')

    group = get_object_or_404(Group, id=group_id, mentor=mentor)
    students = (
        group.students.annotate(total_points=Sum('points__score', default=0))
        .order_by('-total_points', 'full_name')
    )

    categories = PointCategory.objects.filter(is_active=True)
    breakdown = []
    for student in students:
        category_scores = [
            student.points.filter(category=category).aggregate(total=Sum('score'))['total'] or 0
            for category in categories
        ]
        breakdown.append({'student': student, 'scores': category_scores})

    context = {
        'group': group,
        'categories': categories,
        'breakdown': breakdown,
    }
    return render(request, 'student_rating.html', context)


@login_required
def interactive_categories(request):
    mentor = _require_mentor(request)
    if not mentor:
        return redirect('login')

    categories = InteractiveCategory.objects.filter(is_active=True)
    return render(request, 'interactive/categories.html', {'categories': categories})


@login_required
def interactive_question(request, category_id: int):
    mentor = _require_mentor(request)
    if not mentor:
        return redirect('login')

    category = get_object_or_404(InteractiveCategory, id=category_id, is_active=True)
    mode = request.GET.get('mode', 'random')
    items = category.items.filter(is_active=True)

    if not items.exists():
        messages.info(request, 'No interactive items available for this category.')
        return redirect('interactive_categories')

    if mode == 'sequential':
        index = request.session.get(f'interactive_index_{category.id}', 0)
        item = items[index % items.count()]
        request.session[f'interactive_index_{category.id}'] = index + 1
    else:
        item = items.order_by('?').first()

    context = {
        'category': category,
        'item': item,
        'mode': mode,
    }
    return render(request, 'interactive/question.html', context)


@login_required
def best_student(request):
    mentor = _require_mentor(request)
    if not mentor:
        return redirect('login')

    start, end = _current_month_range()
    students = (
        Student.objects.filter(group__mentor=mentor)
        .annotate(
            month_total=Sum(
                'points__score',
                filter=models.Q(points__date__date__range=(start, end)),
                default=0,
            )
        )
        .order_by('-month_total', 'full_name')
    )
    best = students.first()

    context = {
        'students': students,
        'best': best,
        'month_label': start.strftime('%B %Y'),
    }
    return render(request, 'best_student.html', context)

