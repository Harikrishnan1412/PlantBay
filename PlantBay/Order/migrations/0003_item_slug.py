# Generated by Django 5.0.6 on 2024-07-04 01:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Order', '0002_item_category_item_label'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='slug',
            field=models.SlugField(default='test-product'),
            preserve_default=False,
        ),
    ]