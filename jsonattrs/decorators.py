from django.db.models.signals import post_init


def fixup_instance(sender, **kwargs):
    instance = kwargs['instance']
    instance.attrs._instance = instance


def fix_model_for_attributes(cls):
    post_init.connect(fixup_instance, sender=cls)
    return cls
