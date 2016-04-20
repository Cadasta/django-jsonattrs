from jsonattrs.fields import JSONAttributeField


class EntityAttributeField(JSONAttributeField):
    schema_selectors = (('organization', 'project__organization'),
                        'project')
