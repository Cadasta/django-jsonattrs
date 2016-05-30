from django.db.models.signals import post_init

from .fields import JSONAttributes, JSONAttributeField


def fixup_instance(sender, **kwargs):
    instance = kwargs['instance']
    for f in instance._meta.fields:
        if isinstance(f, JSONAttributeField):
            fi = getattr(instance, f.name)
            if not isinstance(fi, JSONAttributes):
                setattr(instance, f.name, JSONAttributes())
            getattr(instance, f.name)._instance = instance
            getattr(instance, f.name).setup_from_dict(fi)


def fix_model_for_attributes(cls):
    post_init.connect(fixup_instance, sender=cls)
    return cls
