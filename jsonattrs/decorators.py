from django.db.models.signals import post_init, pre_save

from .signals import fixup_instance, attribute_model_pre_save


def fix_model_for_attributes(cls):
    post_init.connect(fixup_instance, sender=cls)
    pre_save.connect(attribute_model_pre_save, sender=cls)
    return cls
