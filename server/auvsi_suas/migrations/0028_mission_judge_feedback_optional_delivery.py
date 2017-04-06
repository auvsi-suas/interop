# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('auvsi_suas', '0027_target_description_approved'), ]

    operations = [
        migrations.AlterField(model_name='missionjudgefeedback',
                              name='air_delivery_accuracy_ft',
                              field=models.FloatField(null=True), ),
    ]
