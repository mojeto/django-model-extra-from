#!/usr/bin/env python
# -*- coding: utf-8 -*-
# MIT License - full license can be found in LICENSE file.
# Copyright (c) 2016 Jan Nakladal

from __future__ import unicode_literals, absolute_import

import datetime
from decimal import Decimal

import pytest
from django import forms
from django.db import models
from django.utils.timezone import utc
from django_model_extra_form.forms import DateField, TimeField, DateTimeField
from django_model_extra_form.forms.utils import FormValidationError
from django_model_extra_form.models import ExtraFormMixin, ExtraForm, \
    ExtraTarget, RAW


class FakeModel(models.Model):

    class Meta(object):
        abstract = True
        app_label = 'test'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        return  # stop model saving


class Step1Form(forms.Form):
    date = DateField()
    time = TimeField()
    datetime = DateTimeField()


class Step2Form(forms.Form):
    number = forms.DecimalField(
        initial=Decimal('0.1'), max_digits=6, decimal_places=2
    )


class Step3Form(forms.Form):
    string = forms.CharField(max_length=23, required=False)
    end_datetime = DateTimeField()


class ExtraModel(ExtraFormMixin, FakeModel):

    extra_targets = [
        # short syntax, data from two forms into one target field
        ['step12', Step1Form, Step2Form],

        # full syntax, RAW data (dict) from prefixed form to target field
        ExtraTarget('step3', ExtraForm(Step3Form), serializer=RAW)
    ]

    step12 = models.TextField(editable=False)
    # commented out to not be depend on postgres libraries
    # from django.contrib.postgres.fields import JSONField
    # step3 = JSONField(editable=False)
    step3 = {}  # RAW serializer expect dictionary as value


def test_initial_extra_data():
    instance = ExtraModel()
    assert instance.date is None
    assert instance.time is None
    assert instance.datetime is None
    assert instance.number == Decimal('0.1')
    assert instance.string == ''
    assert instance.end_datetime is None


def test_set_extra_data():
    date = datetime.date(2016, 2, 29)
    time = datetime.time(1, 2, 3)
    dt = datetime.datetime.combine(date, time).replace(tzinfo=utc)
    end = dt + datetime.timedelta(days=1)
    instance = ExtraModel(date=date, time=time, datetime=dt, end_datetime=end)
    assert instance.date == date
    assert instance.time == time
    assert instance.datetime == dt
    assert instance.number == Decimal('0.1')
    assert instance.string == ''
    assert instance.end_datetime == end

    instance = ExtraModel()
    instance.date = date
    instance.time = time
    instance.datetime = dt
    instance.end_datetime = end
    assert instance.date == date
    assert instance.time == time
    assert instance.datetime == dt
    assert instance.number == Decimal('0.1')
    assert instance.string == ''
    assert instance.end_datetime == end


def test_edit_some_extra_data():
    instance = ExtraModel()
    instance.string = 'test'
    assert instance.date is None
    assert instance.time is None
    assert instance.datetime is None
    assert instance.number == Decimal('0.1')
    assert instance.string == 'test'
    assert instance.end_datetime is None


def test_load_extra_data():
    date = datetime.date(2016, 2, 29)
    time = datetime.time(1, 2, 3)
    dt = datetime.datetime.combine(date, time).replace(tzinfo=utc)
    end = dt - datetime.timedelta(days=1)
    instance = ExtraModel(
        step12='{"date": "2016-02-29", "time": "01:02:03", '
               '"datetime": "2016-02-29T01:02:03Z", "number": 0.2}'
    )
    # step3 has to be set this way as it isn't model field currently
    instance.step3 = {'string': 'testing string', 'end_datetime': end}
    assert instance.date == date
    assert instance.time == time
    assert instance.datetime == dt
    assert instance.number == Decimal('0.2')
    assert instance.string == 'testing string'
    assert instance.end_datetime == end


def test_save_extra_data():
    instance = ExtraModel()
    instance.date = datetime.date(2016, 2, 29)
    instance.time = datetime.time(1, 2, 3)
    instance.datetime = datetime.datetime.combine(
        instance.date, instance.time
    ).replace(tzinfo=utc)
    instance.number = Decimal('0.2')
    instance.string = 'testing string'
    instance.end_datetime = instance.datetime + datetime.timedelta(days=1)

    assert instance.step12 == ''
    assert instance.step3 == {}
    instance.save()  # fake save by FakeModel
    step12 = '{"date": "2016-02-29", "time": "01:02:03", ' \
             '"datetime": "2016-02-29T01:02:03+00:00", "number": 0.2}'

    step3 = {'string': 'testing string', 'end_datetime': instance.end_datetime}

    assert instance.step12 == step12
    assert instance.step3 == step3


def test_create_with_extra_data():
    dt = datetime.datetime(2016, 2, 29, 1, 2, 3, tzinfo=utc)
    end = dt + datetime.timedelta(days=1)
    instance = ExtraModel.objects.create(
        date=datetime.date(2016, 2, 29),
        time=datetime.time(1, 2, 3),
        datetime=dt,
        number=Decimal('0.2'),
        string='testing string',
        end_datetime=end
    )
    step12 = '{"date": "2016-02-29", "time": "01:02:03", ' \
             '"datetime": "2016-02-29T01:02:03+00:00", "number": 0.2}'
    step3 = {'string': 'testing string', 'end_datetime': end}

    assert instance.step12 == step12
    assert instance.step3 == step3


def test_extra_data_validation():
    instance = ExtraModel()
    msg = "This field is required."
    with pytest.raises(FormValidationError) as exc_info:
        instance.save()

    messages = exc_info.value.message_dict
    assert 'time' in messages
    assert msg == messages['time'][0]
    assert 'date' in messages
    assert msg == messages['date'][0]
    assert 'datetime' in messages
    assert msg == messages['datetime'][0]
    # not present as it doesn't merge all validation exception from all forms
    # assert 'end_datetime' in messages
    # assert msg == messages['end_datetime'][0]
