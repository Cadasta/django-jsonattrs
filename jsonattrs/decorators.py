from django.db.models.signals import post_init, pre_save
from django.core.exceptions import FieldError

from .fields import JSONAttributes, JSONAttributeField
from .signals import attribute_model_pre_save


def fixup_instance(sender, **kwargs):
    instance = kwargs['instance']
    for f in instance._meta.fields:
        if isinstance(f, JSONAttributeField):
            fi = getattr(instance, f.name)
            if not isinstance(fi, JSONAttributes):
                setattr(instance, f.name, JSONAttributes())
            fld = getattr(instance, f.name)
            fld._instance = instance
            if hasattr(instance, '_attr_field'):
                raise FieldError('multiple JSONAttributeField fields: '
                                 'only one is allowed per model!')
            instance._attr_field = fld
            fld.setup_from_dict(fi)
    if not hasattr(instance, '_attr_field'):
        raise FieldError('missing JSONAttributeField field in '
                         'fixup_instance decorator')


def fix_model_for_attributes(cls):
    post_init.connect(fixup_instance, sender=cls)
    pre_save.connect(attribute_model_pre_save, sender=cls)
    return cls
