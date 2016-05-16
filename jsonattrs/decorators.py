from django.db.models.signals import post_init

from .fields import JSONAttributes


def fixup_instance(sender, **kwargs):
    instance = kwargs['instance']
    for k, v in instance.__dict__.items():
        if isinstance(v, JSONAttributes):
            v._instance = instance


def fix_model_for_attributes(cls):
    post_init.connect(fixup_instance, sender=cls)
    return cls
