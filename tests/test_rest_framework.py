#!//usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2016 NZME

from __future__ import unicode_literals, absolute_import

import datetime
from decimal import Decimal

import pytest
from django import forms
from django.utils.timezone import utc
from django_model_extra_form.contrib.rest_framework.field_mapping import \
    map_form_to_serializer
from django_model_extra_form.contrib.rest_framework.fields import FormField
from django_model_extra_form.contrib.rest_framework.serializers import \
    ExtraFormSerializerMixin, extra_form_fields_names
from rest_framework.serializers import ModelSerializer
from tests.test_extra_form import ExtraModel


class OKFormField(forms.Field):

    def to_python(self, value):
        return 'ok', value


@pytest.fixture(params=[OKFormField])
def serializer_field(request):
    form_field_class = request.param
    serializer_field_class, kwargs = map_form_to_serializer(form_field_class())
    assert serializer_field_class is FormField
    field = serializer_field_class(**kwargs)
    return field


def test_field_serialization(serializer_field):
    value = serializer_field.to_representation('test value')
    assert value == '"test value"'


def to_internal_value(serializer_field):
    value = serializer_field.to_internal_value('test value')
    assert value == ['ok', 'test value']


class ExtraSerializer(ExtraFormSerializerMixin, ModelSerializer):

    class Meta(object):
        model = ExtraModel
        fields = tuple(extra_form_fields_names(ExtraModel))


@pytest.fixture()
def initial_data():
    return dict(
            date=datetime.date(2016, 2, 29),
            time=datetime.time(1, 2, 3),
            datetime=datetime.datetime(2016, 2, 29, 1, 2, 3, tzinfo=utc),
            string='some dummy data',
            end_datetime=datetime.datetime(2016, 3, 1, 1, 2, 3, tzinfo=utc),
        )


@pytest.fixture()
def validated_data(initial_data):
    return dict(
        number=Decimal('0.1'),
        **initial_data
    )


@pytest.fixture()
def extra_model_instance(initial_data):
    instance = ExtraModel(**initial_data)
    instance.save()
    return instance


@pytest.fixture()
def data(validated_data):
    dec = '{{:.{}f}}'.format(
        ExtraModel.extra_targets[0][2].base_fields['number'].decimal_places
    )
    return dict(
        date=validated_data['date'].isoformat(),
        time=validated_data['time'].isoformat(),
        datetime=validated_data['datetime'].isoformat()[:19] + 'Z',
        end_datetime=validated_data['end_datetime'].isoformat()[:19] + 'Z',
        string='some dummy data',
        number=dec.format(validated_data['number']),
    )


def test_serialize_extra_data(extra_model_instance, data):
    serializer = ExtraSerializer(instance=extra_model_instance)
    serializer_data = serializer.data
    assert data == serializer_data


def test_deserialize_extra_data(data, validated_data):
    serializer = ExtraSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    data = serializer.validated_data
    assert data == validated_data
