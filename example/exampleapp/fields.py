from jsonattrs.fields import JSONAttributeField


class EntityAttributeField(JSONAttributeField):
    schema_selectors = (('division', 'division__department'),
                        'department')
