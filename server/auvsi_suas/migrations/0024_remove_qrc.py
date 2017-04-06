# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('auvsi_suas', '0023_index_together_user_timestamp'), ]

    operations = [
        migrations.AlterField(
            model_name='target',
            name='target_type',
            field=models.IntegerField(choices=[(1, b'standard'), (
                3, b'off_axis'), (4, b'emergent')]), ),
    ]
