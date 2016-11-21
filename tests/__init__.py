#!//usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2016 NZME

from __future__ import unicode_literals, absolute_import

from django.db import models


class FakeModel(models.Model):

    class Meta(object):
        abstract = True
        app_label = 'test'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        return  # stop model saving
