from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import AiwriteModel, CommentModel

@receiver(post_delete, sender=AiwriteModel)
def delete_related_comments(sender, instance, **kwargs):
    comments = CommentModel.objects.filter(diaries=instance)
    for comment in comments:
        comment.delete()
