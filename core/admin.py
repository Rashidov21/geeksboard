from django.contrib import admin

from .models import (
    Badge,
    Group,
    InteractiveCategory,
    InteractiveItem,
    Mentor,
    MotivationalMessage,
    PointCategory,
    Student,
    StudentBadge,
    StudentPoint,
    Tournament,
    TournamentParticipant,
)


@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'center_name')
    search_fields = ('user__username', 'user__email', 'center_name', 'phone')


class StudentInline(admin.TabularInline):
    model = Student
    extra = 0


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'mentor', 'subject', 'schedule')
    list_filter = ('mentor', 'subject')
    search_fields = ('name', 'mentor__user__username', 'subject')
    inlines = [StudentInline]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'group', 'phone', 'parent_phone')
    list_filter = ('group',)
    search_fields = ('full_name', 'phone', 'parent_phone')


@admin.register(PointCategory)
class PointCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_score', 'is_active')
    list_editable = ('is_active', 'max_score')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(StudentPoint)
class StudentPointAdmin(admin.ModelAdmin):
    list_display = ('student', 'category', 'score', 'reason', 'date')
    list_filter = ('category', 'date')
    search_fields = ('student__full_name', 'reason')
    autocomplete_fields = ('student',)


@admin.register(InteractiveCategory)
class InteractiveCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(InteractiveItem)
class InteractiveItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'type', 'difficulty', 'time_limit', 'is_active')
    list_filter = ('category', 'type', 'is_active')
    search_fields = ('title', 'prompt')
    list_editable = ('time_limit',)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'criteria_type', 'criteria_value', 'is_active')
    list_filter = ('criteria_type', 'is_active')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)


@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
    list_display = ('student', 'badge', 'earned_at')
    list_filter = ('badge', 'earned_at')
    search_fields = ('student__full_name', 'badge__name')
    autocomplete_fields = ('student',)


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'category', 'start_time', 'end_time', 'is_active')
    list_filter = ('group', 'category', 'is_active', 'start_time')
    search_fields = ('name', 'description')
    filter_horizontal = ('questions',)
    autocomplete_fields = ('group', 'category')


@admin.register(TournamentParticipant)
class TournamentParticipantAdmin(admin.ModelAdmin):
    list_display = ('student', 'tournament', 'score', 'correct_answers', 'total_questions', 'completed_at')
    list_filter = ('tournament', 'completed_at')
    search_fields = ('student__full_name', 'tournament__name')
    autocomplete_fields = ('student', 'tournament')


@admin.register(MotivationalMessage)
class MotivationalMessageAdmin(admin.ModelAdmin):
    list_display = ('student', 'message_type', 'is_read', 'created_at')
    list_filter = ('message_type', 'is_read', 'created_at')
    search_fields = ('student__full_name', 'message')
    autocomplete_fields = ('student',)
    list_editable = ('is_read',)
