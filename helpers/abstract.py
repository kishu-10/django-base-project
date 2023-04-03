from django.db import models


class BaseModelManager(models.Manager):
    def get_queryset(self):
        return super(BaseModelManager, self).get_queryset().filter(is_deleted=False)


class BaseModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    created_date = models.DateTimeField(blank=True, auto_now_add=True)
    updated_date = models.DateTimeField(blank=True, auto_now=True)
    created_by = models.ForeignKey(
        'user.AuthUser', on_delete=models.SET_NULL, blank=True, null=True,  related_name='%(app_label)s_%(class)s_created_by')
    updated_by = models.ForeignKey(
        'user.AuthUser', on_delete=models.SET_NULL, blank=True, null=True,  related_name='%(app_label)s_%(class)s_updated_by')

    admin_objects = models.Manager()
    objects = BaseModelManager()

    class Meta:
        abstract = True
