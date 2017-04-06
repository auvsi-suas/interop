# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auvsi_suas', '0025_target_actionable_override'),
    ]

    operations = [
        migrations.CreateModel(
            name='MissionJudgeFeedback',
            fields=[
                ('id', models.AutoField(verbose_name='ID',
                                        serialize=False,
                                        auto_created=True,
                                        primary_key=True)),
                ('flight_time', models.DurationField()),
                ('post_process_time', models.DurationField()),
                ('used_timeout', models.BooleanField()),
                ('safety_pilot_takeovers', models.IntegerField()),
                ('manual_flight_time', models.DurationField()),
                ('waypoints_captured', models.IntegerField()),
                ('out_of_bounds', models.IntegerField()),
                ('unsafe_out_of_bounds', models.IntegerField()),
                ('air_delivery_accuracy_ft', models.FloatField()),
                ('operational_excellence_percent', models.FloatField()),
                ('mission', models.ForeignKey(to='auvsi_suas.MissionConfig')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ], ),
        migrations.AlterUniqueTogether(
            name='missionjudgefeedback',
            unique_together=set([('mission', 'user')]), ),
    ]
