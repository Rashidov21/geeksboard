from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

User = get_user_model()


class Mentor(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='mentor_profile',
    )
    phone = models.CharField(max_length=32, blank=True)
    address = models.TextField(blank=True)
    center_name = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.user.get_full_name() or self.user.username


class Group(models.Model):
    mentor = models.ForeignKey(
        Mentor,
        on_delete=models.CASCADE,
        related_name='groups',
    )
    name = models.CharField(max_length=150)
    subject = models.CharField(max_length=120, blank=True)
    schedule = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('mentor', 'name')
        ordering = ['name']

    def __str__(self) -> str:
        return f'{self.name} ({self.mentor})'

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

    def get_level(self) -> str:
        """Returns student level based on total points: Beginner, Intermediate, or Pro"""
        total = self.total_score()
        if total < 51:
            return 'Beginner'
        elif total < 151:
            return 'Intermediate'
        else:
            return 'Pro'

    def get_level_thresholds(self) -> dict:
        """Returns the point thresholds for each level"""
        total = self.total_score()
        if total < 51:
            return {
                'current': 'Beginner',
                'current_min': 0,
                'current_max': 50,
                'next': 'Intermediate',
                'next_min': 51,
                'next_max': 150,
            }
        elif total < 151:
            return {
                'current': 'Intermediate',
                'current_min': 51,
                'current_max': 150,
                'next': 'Pro',
                'next_min': 151,
                'next_max': float('inf'),
            }
        else:
            return {
                'current': 'Pro',
                'current_min': 151,
                'current_max': float('inf'),
                'next': None,
                'next_min': None,
                'next_max': None,
            }

    def get_progress_percentage(self) -> float:
        """Returns progress percentage toward next level (0-100)"""
        thresholds = self.get_level_thresholds()
        if thresholds['next'] is None:
            return 100.0  # Max level reached
        
        total = self.total_score()
        current_range = thresholds['current_max'] - thresholds['current_min'] + 1
        progress_in_range = total - thresholds['current_min']
        return min(100.0, (progress_in_range / current_range) * 100)

    def get_trend(self, days=30) -> dict:
        """Returns trend data comparing current period to previous period"""
        from datetime import timedelta
        now = timezone.now()
        current_start = now - timedelta(days=days)
        previous_start = current_start - timedelta(days=days)
        
        current_points = self.total_score(start_date=current_start)
        previous_points = self.total_score(start_date=previous_start, end_date=current_start)
        
        if previous_points == 0:
            change_percent = 100.0 if current_points > 0 else 0.0
        else:
            change_percent = ((current_points - previous_points) / abs(previous_points)) * 100
        
        return {
            'current': current_points,
            'previous': previous_points,
            'change': current_points - previous_points,
            'change_percent': change_percent,
            'direction': 'up' if current_points > previous_points else 'down' if current_points < previous_points else 'neutral'
        }


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
    score = models.SmallIntegerField(help_text='Can be positive (added) or negative (removed)')
    reason = models.CharField(max_length=255, blank=True, help_text='Why points were given or removed')
    date = models.DateTimeField(default=timezone.now)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self) -> str:
        return f'{self.student} - {self.category} ({self.score})'

    def clean(self):
        abs_score = abs(self.score)
        if abs_score > self.category.max_score:
            raise ValidationError(f'Absolute score cannot exceed category max score ({self.category.max_score})')

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
    time_limit = models.PositiveSmallIntegerField(
        default=60,
        help_text='Time limit in seconds for answering this question'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'difficulty', 'title']

    def __str__(self) -> str:
        return self.title


class Badge(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField()
    icon = models.CharField(
        max_length=50,
        default='🏆',
        help_text='Emoji or icon identifier'
    )
    criteria_type = models.CharField(
        max_length=50,
        choices=[
            ('homework_completion', 'Homework Completion %'),
            ('total_points', 'Total Points'),
            ('participation_count', 'Participation Count'),
            ('attendance_count', 'Attendance Count'),
            ('top_rank', 'Top Rank in Group'),
        ],
        default='total_points'
    )
    criteria_value = models.PositiveIntegerField(
        help_text='Threshold value for earning this badge (e.g., 90 for 90% homework completion)'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class StudentBadge(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='badges_earned'
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name='student_badges'
    )
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'badge')
        ordering = ['-earned_at']

    def __str__(self) -> str:
        return f'{self.student} - {self.badge}'


class Tournament(models.Model):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='tournaments'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        InteractiveCategory,
        on_delete=models.CASCADE,
        related_name='tournaments'
    )
    questions = models.ManyToManyField(
        InteractiveItem,
        related_name='tournaments',
        blank=True
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    points_per_question = models.PositiveSmallIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_time']

    def __str__(self) -> str:
        return f'{self.name} - {self.group}'


class TournamentParticipant(models.Model):
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='tournament_participations'
    )
    score = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveSmallIntegerField(default=0)
    total_questions = models.PositiveSmallIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('tournament', 'student')
        ordering = ['-score', 'completed_at']

    def __str__(self) -> str:
        return f'{self.student} - {self.tournament} ({self.score} pts)'


class MotivationalMessage(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='motivational_messages'
    )
    message = models.TextField()
    message_type = models.CharField(
        max_length=50,
        choices=[
            ('improvement', 'Improvement'),
            ('achievement', 'Achievement'),
            ('encouragement', 'Encouragement'),
            ('milestone', 'Milestone'),
        ],
        default='encouragement'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.student} - {self.message[:50]}'
