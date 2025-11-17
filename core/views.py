import calendar
from datetime import date
from typing import Optional

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db import models
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy

from .forms import StudentPointForm
from .models import Group, InteractiveCategory, PointCategory, Student, StudentPoint


def _current_month_range(target_date: Optional[date] = None):
    today = target_date or date.today()
    start = today.replace(day=1)
    _, last_day = calendar.monthrange(today.year, today.month)
    end = today.replace(day=last_day)
    return start, end


def _require_teacher(request):
    teacher = getattr(request.user, 'teacher_profile', None)
    if not teacher:
        messages.error(request, 'No teacher profile linked to this account.')
        return None
    return teacher


class TeacherLoginView(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        return reverse('dashboard')


class TeacherLogoutView(LogoutView):
    next_page = reverse_lazy('login')


@login_required
def dashboard(request):
    teacher = _require_teacher(request)
    if not teacher:
        return redirect('login')

    groups = teacher.groups.prefetch_related('students')
    student_ids = Student.objects.filter(group__teacher=teacher).values_list('id', flat=True)
    start, end = _current_month_range()

    leaderboard = (
        Student.objects.filter(id__in=student_ids)
        .annotate(
            month_total=Sum(
                'points__score',
                filter=models.Q(points__date__range=(start, end)),
                default=0,
            )
        )
        .order_by('-month_total', 'full_name')[:5]
    )

    stats = {
        'group_count': groups.count(),
        'student_count': sum(group.students.count() for group in groups),
        'point_entries': StudentPoint.objects.filter(student__group__teacher=teacher).count(),
    }

    recent_points = (
        StudentPoint.objects.filter(student__group__teacher=teacher)
        .select_related('student', 'category')
        .order_by('-date')[:5]
    )

    context = {
        'teacher': teacher,
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
    teacher = _require_teacher(request)
    if not teacher:
        return redirect('login')

    groups = teacher.groups.annotate(student_total=Count('students')).order_by('name')
    return render(request, 'group_list.html', {'groups': groups, 'teacher': teacher})


@login_required
def student_list(request, group_id: int):
    teacher = _require_teacher(request)
    if not teacher:
        return redirect('login')

    group = get_object_or_404(Group, id=group_id, teacher=teacher)
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
            messages.success(request, f'Points updated for {target_student.full_name}.')
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
def student_rating(request, group_id: int):
    teacher = _require_teacher(request)
    if not teacher:
        return redirect('login')

    group = get_object_or_404(Group, id=group_id, teacher=teacher)
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
    teacher = _require_teacher(request)
    if not teacher:
        return redirect('login')

    categories = InteractiveCategory.objects.filter(is_active=True)
    return render(request, 'interactive/categories.html', {'categories': categories})


@login_required
def interactive_question(request, category_id: int):
    teacher = _require_teacher(request)
    if not teacher:
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
    teacher = _require_teacher(request)
    if not teacher:
        return redirect('login')

    start, end = _current_month_range()
    students = (
        Student.objects.filter(group__teacher=teacher)
        .annotate(
            month_total=Sum(
                'points__score',
                filter=models.Q(points__date__range=(start, end)),
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

