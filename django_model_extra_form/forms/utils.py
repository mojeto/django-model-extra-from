#!//usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2016 NZME

from __future__ import unicode_literals, absolute_import

import copy
from collections import OrderedDict

from django.core.exceptions import ValidationError
from django.utils.six import iterkeys, iteritems


class FormValidationError(ValidationError):

    def __init__(self, errors, message=None, *args, **kwargs):
        self.errors = errors
        super(FormValidationError, self).__init__(
            message or errors,
            *args,
            **kwargs
        )


def validate_form(form):
    if not form.is_valid():
        raise FormValidationError(form.errors)


def form_data(form, dict_class=None):
    dict_class = dict_class or OrderedDict
    if not form.is_bound:
        # get initial values from empty form
        def get_value(key):
            return form[key].value()

    else:
        try:
            cleaned_data = form.cleaned_data
        except AttributeError as e:
            raise ValueError('{}. You have to call form.is_valid() or '
                             'form.full_clean() first.'.format(e))

        # unbound_form is source of initial values for missing form fields only
        unbound_form = copy.copy(form)
        unbound_form.is_bound = False

        def get_value(key):
            if key in cleaned_data:
                return cleaned_data[key]
            else:
                return unbound_form[key].value()

    return dict_class((key, get_value(key)) for key in iterkeys(form.fields))


def set_form_data_to_instance(form, instance):
    for key, value in iteritems(form_data(form)):
        setattr(instance, key, value)


def get_form_data_from_instance(form, instance, dict_class=None):
    dict_class = dict_class or OrderedDict
    return dict_class(
        (key, getattr(instance, key)) for key in iterkeys(form.base_fields)
    )
