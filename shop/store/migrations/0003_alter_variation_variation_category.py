# Generated by Django 4.2.7 on 2023-12-03 01:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_variation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variation',
            name='variation_category',
            field=models.CharField(choices=[('color', 'color'), ('memory', 'memory'), ('size', 'size')], max_length=100),
        ),
    ]
