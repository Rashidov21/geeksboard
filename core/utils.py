"""
Utility functions for gamification features
"""
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional

from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.utils import timezone

from .models import Badge, PointCategory, Student, StudentBadge, StudentPoint

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def check_and_assign_badges(student: Student) -> list:
    """
    Check if student qualifies for any badges and assign them.
    Returns list of newly earned badges.
    """
    newly_earned = []
    active_badges = Badge.objects.filter(is_active=True)
    
    for badge in active_badges:
        # Skip if student already has this badge
        if StudentBadge.objects.filter(student=student, badge=badge).exists():
            continue
        
        qualifies = False
        
        if badge.criteria_type == 'total_points':
            total = student.total_score()
            qualifies = total >= badge.criteria_value
            
        elif badge.criteria_type == 'homework_completion':
            # Calculate homework completion percentage
            homework_category = PointCategory.objects.filter(
                slug='homework'
            ).first()
            if homework_category:
                homework_points = StudentPoint.objects.filter(
                    student=student,
                    category=homework_category,
                    score__gt=0
                ).count()
                # This is simplified - you might want to track total homework assigned
                # For now, we'll use a threshold of homework points
                qualifies = homework_points >= badge.criteria_value
                
        elif badge.criteria_type == 'participation_count':
            participation_category = PointCategory.objects.filter(
                slug='participation'
            ).first()
            if participation_category:
                count = StudentPoint.objects.filter(
                    student=student,
                    category=participation_category,
                    score__gt=0
                ).count()
                qualifies = count >= badge.criteria_value
                
        elif badge.criteria_type == 'attendance_count':
            attendance_category = PointCategory.objects.filter(
                slug='attendance'
            ).first()
            if attendance_category:
                count = StudentPoint.objects.filter(
                    student=student,
                    category=attendance_category,
                    score__gt=0
                ).count()
                qualifies = count >= badge.criteria_value
                
        elif badge.criteria_type == 'top_rank':
            # Check if student is in top N of their group
            group_students = student.group.students.annotate(
                total_points=Sum('points__score', default=0)
            ).order_by('-total_points')
            student_rank = list(group_students.values_list('id', flat=True)).index(student.id) + 1
            qualifies = student_rank <= badge.criteria_value
        
        if qualifies:
            StudentBadge.objects.create(student=student, badge=badge)
            newly_earned.append(badge)
    
    return newly_earned


def generate_motivational_message(student: Student) -> Optional[str]:
    """
    Generate a motivational message based on student's recent performance.
    """
    trend = student.get_trend(days=30)
    total_points = student.total_score()
    level = student.get_level()
    
    messages = []
    
    # Trend-based messages
    if trend['direction'] == 'up' and trend['change'] > 0:
        change_percent = abs(trend['change_percent'])
        if change_percent > 50:
            messages.append(f"Amazing progress! Your score increased by {change_percent:.0f}% this month! 🚀")
        elif change_percent > 20:
            messages.append(f"Great job! You increased your score by {change_percent:.0f}% this month! 📈")
        else:
            messages.append(f"Keep it up! Your score improved by {change_percent:.0f}% this month! 💪")
    
    elif trend['direction'] == 'down' and trend['change'] < 0:
        messages.append("Don't give up! Every challenge is an opportunity to grow. You've got this! 💪")
    
    # Level-based messages
    if level == 'Pro':
        messages.append("Outstanding! You've reached Pro level! 🌟")
    elif level == 'Intermediate':
        progress = student.get_progress_percentage()
        if progress > 80:
            messages.append(f"You're almost at Pro level! Just {100 - progress:.0f}% more to go! 🎯")
    
    # Points milestone messages
    if total_points >= 200:
        messages.append("Incredible achievement! You've crossed 200 points! 🏆")
    elif total_points >= 100:
        messages.append("Fantastic! You've reached 100 points! Keep pushing forward! ⭐")
    elif total_points >= 50:
        messages.append("Well done! You've hit 50 points! You're making great progress! 🎉")
    
    # Badge count messages
    badge_count = student.badges_earned.count()
    if badge_count > 0:
        messages.append(f"Impressive! You've earned {badge_count} badge{'s' if badge_count > 1 else ''}! 🏅")
    
    # Return the most relevant message
    if messages:
        return messages[0]
    
    return "Keep up the excellent work! Every effort counts! 💫"


def assign_monthly_rewards(month: Optional[datetime] = None) -> dict:
    """
    Assign monthly reward points to top students in each group.
    Returns dict with statistics.
    """
    if month is None:
        month = timezone.now()
    
    start = month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    
    stats = {
        'groups_processed': 0,
        'students_rewarded': 0,
        'points_awarded': 0,
    }
    
    from .models import Group
    
    groups = Group.objects.all()
    homework_category = PointCategory.objects.filter(slug='homework').first()
    
    for group in groups:
        stats['groups_processed'] += 1
        
        # Get top 3 students for the month
        top_students = (
            group.students.annotate(
                monthly_total=Sum(
                    'points__score',
                    filter=Q(points__date__gte=start, points__date__lt=end),
                    default=0
                )
            )
            .filter(monthly_total__gt=0)
            .order_by('-monthly_total')[:3]
        )
        
        # Award points: 1st place = 15, 2nd place = 10, 3rd place = 5
        rewards = [15, 10, 5]
        
        for idx, student in enumerate(top_students):
            if idx < len(rewards):
                reward_points = rewards[idx]
                
                # Create reward point entry
                StudentPoint.objects.create(
                    student=student,
                    category=homework_category or PointCategory.objects.first(),
                    score=reward_points,
                    reason='Monthly Reward',
                    note=f'Top {idx + 1} student for {start.strftime("%B %Y")}'
                )
                
                stats['students_rewarded'] += 1
                stats['points_awarded'] += reward_points
                
                # Check for badges after reward
                check_and_assign_badges(student)
    
    return stats


def generate_certificate_pdf(student: Student, month: Optional[datetime] = None) -> Optional[BytesIO]:
    """
    Generate a PDF certificate for the best student of the month.
    Returns BytesIO object with PDF content, or None if reportlab is not available.
    """
    if not REPORTLAB_AVAILABLE:
        return None
    
    if month is None:
        month = timezone.now()
    
    month_name = month.strftime('%B %Y')
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=36,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
        alignment=1,  # Center
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=18,
        textColor=colors.HexColor('#4b5563'),
        spaceAfter=20,
        alignment=1,
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=15,
        alignment=1,
    )
    
    name_style = ParagraphStyle(
        'CustomName',
        parent=styles['Heading2'],
        fontSize=28,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
        alignment=1,
        fontName='Helvetica-Bold'
    )
    
    # Title
    story.append(Spacer(1, 0.8*inch))
    story.append(Paragraph("CERTIFICATE OF EXCELLENCE", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Subtitle
    story.append(Paragraph("This is to certify that", subtitle_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Student name
    story.append(Paragraph(f"<b>{student.full_name}</b>", name_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Achievement text
    story.append(Paragraph(
        f"has been recognized as the <b>Best Student</b> of {month_name}",
        body_style
    ))
    story.append(Spacer(1, 0.1*inch))
    
    # Group and points
    total_points = student.total_score()
    story.append(Paragraph(
        f"in <b>{student.group.name}</b> with a total of <b>{total_points} points</b>",
        body_style
    ))
    story.append(Spacer(1, 0.4*inch))
    
    # Level
    level = student.get_level()
    story.append(Paragraph(
        f"Current Level: <b>{level}</b>",
        body_style
    ))
    story.append(Spacer(1, 0.5*inch))
    
    # Date
    date_style = ParagraphStyle(
        'CustomDate',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#6b7280'),
        alignment=1,
    )
    story.append(Paragraph(
        f"Date: {timezone.now().strftime('%B %d, %Y')}",
        date_style
    ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

