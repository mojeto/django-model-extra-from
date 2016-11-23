#!//usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2016 NZME

from __future__ import unicode_literals, absolute_import

from collections import OrderedDict

from django import forms
from django.utils.six import iterkeys
from django_model_extra_form.forms.utils import validate_form, form_data
from json_encoder import json


class ExtraTargetSerializer(object):
    @classmethod
    def loads(cls, data):
        raise NotImplementedError

    @classmethod
    def dumps(cls, data):
        raise NotImplementedError


class RAW(ExtraTargetSerializer):

    @classmethod
    def loads(cls, data):
        return data

    @classmethod
    def dumps(cls, data):
        return data


class JSON(ExtraTargetSerializer):

    @classmethod
    def loads(cls, data):
        return json.loads(data or '{}')

    @classmethod
    def dumps(cls, data):
        return json.dumps(data)


class ExtraTarget(object):

    def __init__(self, name, *extra_forms, serializer=JSON):
        assert issubclass(serializer, ExtraTargetSerializer)
        self.name = name
        self.extra_forms = tuple(
            form if isinstance(form, ExtraForm) else ExtraForm(form)
            for form in extra_forms
        )
        self.serializer = serializer

    @property
    def field_names(self):
        return [n for form in self.extra_forms for n in form.field_names]

    @property
    def fields(self):
        form_fields = OrderedDict()
        for extra_form in self.extra_forms:
            form_fields.update(extra_form.fields)

        return form_fields

    def clean_data(self, data, validate=True):
        cleaned = OrderedDict()
        for form in self.extra_forms:
            cleaned.update(form.clean_data(data, validate))

        return cleaned

    def serialize(self, data, validate=True):
        data = self.clean_data(data, validate)
        return self.serializer.dumps(data)

    def deserialize(self, data, validate=True):
        data = self.serializer.loads(data)
        return self.clean_data(data, validate)

    def extra_data_parsed(self, instance):
        extra_data = self.deserialize(self.get_data(instance), validate=False)
        return extra_data

    def get_data(self, instance):
        return getattr(instance, self.name, None)

    def set_data(self, instance, value):
        setattr(instance, self.name, value)

    def data_from_attributes(self, instance):
        return {name: getattr(instance, name) for name in self.field_names}

    def data_in_attributes(self, instance):
        attributes = dir(instance)
        return any(name in attributes for name in self.field_names)


class ExtraForm(object):

    def __init__(self, form_class):
        assert issubclass(form_class, forms.Form)
        self.form_class = form_class

    @property
    def field_names(self):
        return [n for n in iterkeys(self.fields)]

    @property
    def fields(self):
        return self.form_class.base_fields

    def clean_data(self, data, validate=True):
        form = self.form_class(data=data)
        validate_form(form) if validate else form.full_clean()
        return form_data(form)


class ExtraFormMixin(object):
    """
    Django model mixin to add support for extra attributes coming from
    ExtraTarget and ExtraForm
    """
    extra_targets = tuple()

    def __init__(self, *args, **kwargs):
        # TODO move this somewhere to run it once per class, not instance
        self.extra_targets = tuple(
            target if isinstance(target, ExtraTarget) else ExtraTarget(*target)
            for target in self.extra_targets
        )

        if kwargs:
            # set extra form data to instance,
            # it's possible for named arguments only
            for target in self.extra_targets:
                for name in target.field_names:
                    if name in kwargs:
                        setattr(self, name, kwargs.pop(name))

        super(ExtraFormMixin, self).__init__(*args, **kwargs)

    def __getattr__(self, name):
        for target in self.extra_targets:
            if name in target.field_names:
                extra_data = target.extra_data_parsed(self)
                for key in set(target.field_names) - set(dir(self)):
                    # set extra data for missing instance attributes only
                    setattr(self, key, extra_data[key])

                return extra_data[name]

        return super(ExtraFormMixin, self).__getattr__(name)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        for target in self.extra_targets:
            if not target.get_data(self) or target.data_in_attributes(self):
                target.set_data(
                    self, target.serialize(target.data_from_attributes(self))
                )

        return super(ExtraFormMixin, self).save(
            force_insert, force_update, using, update_fields
        )