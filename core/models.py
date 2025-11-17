from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

User = get_user_model()


class Teacher(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
    )
    center_name = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return self.user.get_full_name() or self.user.username


class Group(models.Model):
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='groups',
    )
    name = models.CharField(max_length=150)
    subject = models.CharField(max_length=120, blank=True)
    schedule = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('teacher', 'name')
        ordering = ['name']

    def __str__(self) -> str:
        return f'{self.name} ({self.teacher})'

    def student_count(self) -> int:
        return self.students.count()

    def monthly_ranking(self, month: timezone.datetime | None = None):
        month = month or timezone.now()
        start = month.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
        return (
            self.students.annotate(
                monthly_total=models.Sum(
                    'points__score',
                    filter=models.Q(points__date__gte=start, points__date__lt=end),
                )
            )
            .order_by('-monthly_total', 'full_name')
            .values('id', 'full_name', 'monthly_total')
        )


class Student(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='students',
    )
    full_name = models.CharField(max_length=200)
    birth_date = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    parent_phone = models.CharField(max_length=32, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['full_name']

    def __str__(self) -> str:
        return self.full_name

    def get_score_breakdown(self, start_date=None, end_date=None):
        qs = self.points.all()
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lt=end_date)
        return (
            qs.values('category__name')
            .annotate(total=models.Sum('score'))
            .order_by('category__name')
        )

    def total_score(self, start_date=None, end_date=None) -> int:
        qs = self.points.all()
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lt=end_date)
        return qs.aggregate(total=models.Sum('score'))['total'] or 0


class PointCategory(models.Model):
    PARTICIPATION = 'participation'
    ATTENDANCE = 'attendance'
    HOMEWORK = 'homework'
    DISCIPLINE = 'discipline'
    KNOWLEDGE = 'knowledge'

    CATEGORY_CHOICES = [
        (PARTICIPATION, 'Participation'),
        (ATTENDANCE, 'Attendance'),
        (HOMEWORK, 'Homework'),
        (DISCIPLINE, 'Discipline'),
        (KNOWLEDGE, 'Knowledge'),
    ]

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    max_score = models.PositiveSmallIntegerField(default=10)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class StudentPoint(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='points',
    )
    category = models.ForeignKey(
        PointCategory,
        on_delete=models.CASCADE,
        related_name='student_points',
    )
    score = models.SmallIntegerField()
    date = models.DateTimeField(default=timezone.now)
    reason = models.CharField(max_length=255, blank=True)
    is_cancelled = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date']

    def __str__(self) -> str:
        return f'{self.student} - {self.category} ({self.score})'

    def clean(self):
        if abs(self.score) > self.category.max_score:
            raise ValidationError('Score cannot exceed category max score range')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class InteractiveCategory(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(
        max_length=20,
        help_text='Tailwind color keyword such as emerald, purple, sky',
        default='sky',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class InteractiveItem(models.Model):
    QUESTION = 'question'
    REBUS = 'rebus'
    MATH = 'math'
    IT = 'it'
    QUIZ = 'quiz'

    TYPE_CHOICES = [
        (QUESTION, 'Logic Question'),
        (REBUS, 'Rebus'),
        (MATH, 'Quick Math'),
        (IT, 'IT Question'),
        (QUIZ, 'Mini Quiz'),
    ]

    category = models.ForeignKey(
        InteractiveCategory,
        on_delete=models.CASCADE,
        related_name='items',
    )
    title = models.CharField(max_length=200)
    prompt = models.TextField()
    correct_answer = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=QUESTION)
    difficulty = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'difficulty', 'title']

    def __str__(self) -> str:
        return self.title
