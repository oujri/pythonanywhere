# Generated by Django 2.0.4 on 2018-05-06 22:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0002_contact'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profil',
            name='date_naissance',
        ),
        migrations.RemoveField(
            model_name='profil',
            name='entreprise',
        ),
        migrations.RemoveField(
            model_name='profil',
            name='facebook',
        ),
        migrations.RemoveField(
            model_name='profil',
            name='fonction',
        ),
        migrations.RemoveField(
            model_name='profil',
            name='instagram',
        ),
        migrations.RemoveField(
            model_name='profil',
            name='linkedin',
        ),
        migrations.RemoveField(
            model_name='profil',
            name='pays',
        ),
        migrations.RemoveField(
            model_name='profil',
            name='photo_couverture',
        ),
        migrations.RemoveField(
            model_name='profil',
            name='photo_profil',
        ),
        migrations.RemoveField(
            model_name='profil',
            name='service',
        ),
        migrations.RemoveField(
            model_name='profil',
            name='tel',
        ),
        migrations.RemoveField(
            model_name='profil',
            name='ville',
        ),
        migrations.RemoveField(
            model_name='profil',
            name='website',
        ),
        migrations.RemoveField(
            model_name='profil',
            name='youtube',
        ),
    ]
