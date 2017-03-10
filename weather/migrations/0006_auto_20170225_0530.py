# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-25 05:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0005_city_user_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Yahoo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('req_date', models.DateTimeField(verbose_name='request date')),
                ('name', models.CharField(max_length=100)),
                ('coord_lon', models.CharField(max_length=100)),
                ('coord_lat', models.CharField(max_length=100)),
                ('country', models.CharField(max_length=100)),
                ('region', models.CharField(max_length=100)),
                ('yql_resp_text', models.CharField(max_length=1200)),
            ],
        ),
        migrations.CreateModel(
            name='YahooForecast',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('forecast_text', models.CharField(max_length=1200)),
                ('owm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='weather.OWM')),
            ],
        ),
        migrations.AddField(
            model_name='city',
            name='ds_yahoo',
            field=models.URLField(default='q'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='yahoo',
            name='city',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='weather.City'),
        ),
    ]