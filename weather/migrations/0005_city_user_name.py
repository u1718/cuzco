# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-13 08:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0004_city_turn'),
    ]

    operations = [
        migrations.AddField(
            model_name='city',
            name='user_name',
            field=models.CharField(default='teu', max_length=100),
            preserve_default=False,
        ),
    ]
