# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-09-23 07:28
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jsonattrs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='attribute',
            name='choice_labels',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=512), null=True, size=None),
        ),
    ]
