from django.db import models
from django.contrib.auth.models import User

class PromptHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_input = models.TextField()
    task_type = models.CharField(max_length=50)
    tone = models.CharField(max_length=50)
    generated_prompt = models.TextField()
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user_input[:40]


class PromptTemplate(models.Model):
    task_type = models.CharField(max_length=50)
    tone = models.CharField(max_length=50)
    template_text = models.TextField()

    def __str__(self):
        return f"{self.task_type} - {self.tone}"