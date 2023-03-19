from django.db import models
from .validators import validate_not_empty


class Contact(models.Model):
    name = models.CharField(max_length=100, validators=[validate_not_empty])
    email = models.EmailField()
    subject = models.CharField(max_length=100)
    body = models.TextField(validators=[validate_not_empty])
    is_answered = models.BooleanField(default=False)
