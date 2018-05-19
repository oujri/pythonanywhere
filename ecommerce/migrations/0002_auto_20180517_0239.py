# Generated by Django 2.0.4 on 2018-05-17 02:39

from django.db import migrations, models
import ecommerce.models


class Migration(migrations.Migration):

    dependencies = [
        ('ecommerce', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='brand',
            name='image',
            field=models.ImageField(blank=True, upload_to=ecommerce.models.PathAndRename('images/2018/05/17')),
        ),
        migrations.AlterField(
            model_name='commercecategory',
            name='image',
            field=models.ImageField(default='/images/categories.jpg', upload_to=ecommerce.models.PathAndRename('images/2018/05/17')),
        ),
        migrations.AlterField(
            model_name='commerceimage',
            name='image',
            field=models.ImageField(upload_to=ecommerce.models.PathAndRename('images/2018/05/17')),
        ),
        migrations.AlterField(
            model_name='product',
            name='image',
            field=models.ImageField(default='/images/categories.jpg', upload_to=ecommerce.models.PathAndRename('images/2018/05/17')),
        ),
        migrations.AlterField(
            model_name='slide',
            name='image',
            field=models.ImageField(upload_to=ecommerce.models.PathAndRename('slides/2018/05/17')),
        ),
    ]