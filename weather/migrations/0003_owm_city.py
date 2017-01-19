# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-17 13:26
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0002_auto_20170117_1252'),
    ]

    operations = [
        migrations.AddField(
            model_name='owm',
            name='city',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='weather.City'),
            preserve_default=False,
        ),
    ]
