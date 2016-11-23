#!//usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2016 NZME

from __future__ import unicode_literals, absolute_import

from collections import OrderedDict

from django_model_extra_form.contrib.rest_framework.field_mapping import \
    map_form_to_serializer


class ExtraFormSerializerMixin(object):

    def build_property_field(self, field_name, model_class):
        """
        some model properties can be extra data fields
        """
        if field_name in extra_form_fields_names(model_class):
            return self.build_extra_form_field(field_name, model_class)

        return super(ExtraFormSerializerMixin, self).build_property_field(
            field_name, model_class
        )

    def build_unknown_field(self, field_name, model_class):
        """
        some unknown fields can be extra data fields
        """
        if field_name in extra_form_fields_names(model_class):
            return self.build_extra_form_field(field_name, model_class)

        return super(ExtraFormSerializerMixin, self).build_unknown_field(
            field_name, model_class
        )

    def build_extra_form_field(self, field_name, model_class):
        """
        map django form field into rest framework serializer field
        """
        form_field_class = extra_form_fields(model_class)[field_name]
        field_class, field_kwargs = map_form_to_serializer(form_field_class)
        return field_class, field_kwargs


def extra_form_fields_names(model_class):
    return [n for t in model_class().extra_targets for n in t.field_names]


def extra_form_fields(model_class):
    fields = OrderedDict()
    for target in model_class().extra_targets:
        fields.update(target.fields)

    return fields
