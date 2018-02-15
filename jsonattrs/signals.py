from django.core.exceptions import FieldError

from .fields import JSONAttributes, JSONAttributeField


def attribute_model_pre_save(sender, **kwargs):
    kwargs['instance']._attr_field._pre_save_selector_check()


def fixup_instance(sender, **kwargs):
    """
    Cache JSONAttributes data on instance and vice versa for convenience.
    """
    instance = kwargs['instance']
    for model_field in instance._meta.fields:

        if not isinstance(model_field, JSONAttributeField):
            continue

        if hasattr(instance, '_attr_field'):
            raise FieldError('multiple JSONAttributeField fields: '
                             'only one is allowed per model!')

        field_name = model_field.name
        attrs = getattr(instance, field_name)

        # ensure JSONAttributeField's data is of JSONAttributes type
        if not isinstance(attrs, JSONAttributes):
            setattr(instance, field_name, JSONAttributes(attrs))
            attrs = getattr(instance, field_name)

        # Cache model instance on JSONAttributes instance and vice-versa
        attrs._instance = instance
        instance._attr_field = attrs

    if not hasattr(instance, '_attr_field'):
        raise FieldError('missing JSONAttributeField field in '
                         'fixup_instance decorator')
