#!/usr/bin/env python
# -*- coding: utf-8 -*-
# MIT License - full license can be found in LICENSE file.
# Copyright (c) 2016 Jan Nakladal

from __future__ import unicode_literals, absolute_import

from django import forms
from django.contrib.postgres.fields import JSONField
from django.db import models

from django_model_extra_form.models import ExtraFormMixin, ExtraForm, \
    ExtraTarget, RAW


class Step1Form(forms.Form):
    pass


class Step2Form(forms.Form):
    pass


class Step3Form(forms.Form):
    pass


class MyModel(ExtraFormMixin, models.Model):

    extra_targets = [
        # short syntax, data from two forms into one target field
        ['step12', Step1Form, Step2Form],

        # full syntax, RAW data (dict) from prefixed form to target field
        ExtraTarget(
            'step3',
            ExtraForm(Step3Form, name_mask='prefix_{name}'),
            serializer=RAW
        )
    ]

    step12 = models.TextField(editable=False)
    step3 = JSONField(editable=False)
