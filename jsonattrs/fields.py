from django.contrib.postgres.fields import JSONField


class JSONAttributeField(JSONField):
    def schema(self):
        pass

    def attributes(self):
        pass
