# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('auvsi_suas', '0026_mission_judge_feedback'), ]

    operations = [
        migrations.AddField(model_name='target',
                            name='description_approved',
                            field=models.NullBooleanField(), ),
    ]
