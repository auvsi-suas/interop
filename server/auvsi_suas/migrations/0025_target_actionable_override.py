# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('auvsi_suas', '0024_remove_qrc'), ]

    operations = [
        migrations.AddField(model_name='target',
                            name='actionable_override',
                            field=models.BooleanField(default=False), ),
    ]
