# Generated by Django 4.2.7 on 2023-12-17 07:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0010_alter_variation_variation_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variation',
            name='variation_category',
            field=models.CharField(choices=[('size', 'size'), ('memory', 'memory'), ('color', 'color')], max_length=100),
        ),
    ]
