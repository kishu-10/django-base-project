from rest_framework import serializers
from django.db.models import Case, CharField, Value, When


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop("fields", None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class ChoiceField(serializers.ChoiceField):
    def to_representation(self, obj):
        if obj == "" and self.allow_blank:
            return obj
        return self._choices[obj]

    def to_internal_value(self, data):
        # To support inserts with the value
        if data == "" and self.allow_blank:
            return ""

        for key, val in self._choices.items():
            if val == str(data) or key == str(data):
                return key
        self.fail("invalid_choice", input=data)


class WithChoices(Case):
    """
    Returns name of choice field in Django (For annotate case)
    """

    def __init__(self, model, field, condition=None, then=None, **lookups):
        choices = dict(model._meta.get_field(field).flatchoices)
        whens = [When(**{field: k, "then": Value(v)}) for k, v in choices.items()]
        return super().__init__(*whens, output_field=CharField())
