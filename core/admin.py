from django.contrib import admin

from .models import (
    Group,
    InteractiveCategory,
    InteractiveItem,
    PointCategory,
    Student,
    StudentPoint,
    Teacher,
)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'center_name')
    search_fields = ('user__username', 'user__email', 'center_name')


class StudentInline(admin.TabularInline):
    model = Student
    extra = 0


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'subject', 'schedule')
    list_filter = ('teacher', 'subject')
    search_fields = ('name', 'teacher__user__username')
    inlines = [StudentInline]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'group', 'phone')
    list_filter = ('group',)
    search_fields = ('full_name', 'phone')


@admin.register(PointCategory)
class PointCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_score', 'is_active')
    list_editable = ('is_active', 'max_score')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(StudentPoint)
class StudentPointAdmin(admin.ModelAdmin):
    list_display = ('student', 'category', 'score', 'date')
    list_filter = ('category', 'date')
    search_fields = ('student__full_name',)
    autocomplete_fields = ('student',)


@admin.register(InteractiveCategory)
class InteractiveCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'is_active')
    list_editable = ('is_active',)


@admin.register(InteractiveItem)
class InteractiveItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'type', 'difficulty', 'is_active')
    list_filter = ('category', 'type', 'is_active')
    search_fields = ('title', 'prompt')
