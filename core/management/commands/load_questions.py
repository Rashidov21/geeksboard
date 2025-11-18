import json
from django.core.management.base import BaseCommand
from core.models import InteractiveItem, InteractiveCategory

class Command(BaseCommand):
    help = "Load logic questions from JSON file into InteractiveItem"

    def handle(self, *args, **kwargs):
        # Logic category ni topamiz yoki yaratamiz
        category, _ = InteractiveCategory.objects.get_or_create(name="Logic Questions")

        # JSON faylni ochamiz
        with open("questions.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        for idx, item in enumerate(data, start=1):
            question, answer = item
            InteractiveItem.objects.create(
                category=category,
                title=f"Logic Question {idx}",
                prompt=question,
                correct_answer=answer,
                type=InteractiveItem.QUESTION,
                difficulty=1,
                is_active=True
            )
        self.stdout.write(self.style.SUCCESS("Questions loaded successfully!"))
