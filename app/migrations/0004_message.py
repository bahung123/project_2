# Generated by Django 5.1.3 on 2024-12-20 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_delete_payment'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('text', models.TextField()),
                ('timestamp', models.DateTimeField(blank=True, null=True)),
                ('is_read', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'message',
                'managed': False,
            },
        ),
    ]