# Generated by Django 2.0.4 on 2018-04-30 13:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='RequestArchive',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('req_date', models.DateTimeField(verbose_name='request date')),
                ('name', models.CharField(max_length=100)),
                ('tn', models.CharField(max_length=100)),
                ('cod', models.CharField(max_length=100)),
                ('message', models.CharField(max_length=100)),
                ('cnt', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'weather_req_arc',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('ds_owm', models.URLField()),
                ('ds_yahoo', models.URLField(max_length=250)),
                ('turn', models.BooleanField(default=True)),
                ('user_name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='OWM',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('req_date', models.DateTimeField(verbose_name='request date')),
                ('iden', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=100)),
                ('coord_lon', models.CharField(max_length=100)),
                ('coord_lat', models.CharField(max_length=100)),
                ('country', models.CharField(max_length=100)),
                ('population', models.CharField(max_length=100)),
                ('sys_population', models.CharField(max_length=100)),
                ('cod', models.CharField(max_length=100)),
                ('message', models.CharField(max_length=100)),
                ('cnt', models.CharField(max_length=100)),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='weather.City')),
            ],
        ),
        migrations.CreateModel(
            name='OWMForecast',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('forecast_text', models.CharField(max_length=1200)),
                ('owm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='weather.OWM')),
            ],
        ),
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
                ('yql_resp_text', models.CharField(max_length=3500)),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='weather.City')),
            ],
        ),
        migrations.CreateModel(
            name='YahooForecast',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('forecast_text', models.CharField(max_length=1200)),
                ('yahoo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='weather.Yahoo')),
            ],
        ),
    ]
