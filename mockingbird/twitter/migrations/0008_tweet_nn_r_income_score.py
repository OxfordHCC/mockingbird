# Generated by Django 2.2.3 on 2019-08-05 14:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('twitter', '0007_auto_20190802_0056'),
    ]

    operations = [
        migrations.AddField(
            model_name='tweet',
            name='nn_r_income_score',
            field=models.FloatField(default=-1.0),
        ),
    ]