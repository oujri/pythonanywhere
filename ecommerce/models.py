from django.db import models
from django.contrib.auth.models import User
import time
import os
import uuid
from django.utils.deconstruct import deconstructible
from django.utils import timezone


# For rename the file before save
@deconstructible
class PathAndRename(object):
    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        # eg: filename = 'my uploaded file.jpg'
        ext = filename.split('.')[-1]  # eg: 'jpg'
        uid = uuid.uuid4().hex[:10]  # eg: '567ae32f97'

        # eg: 'my-uploaded-file'
        new_name = '-'.join(filename.replace('.%s' % ext, '').split())

        # eg: 'my-uploaded-file_64c942aa64.jpg'
        renamed_filename = '%(new_name)s_%(uid)s.%(ext)s' % {'new_name': new_name, 'uid': uid, 'ext': ext}

        # eg: 'images/2017/01/29/my-uploaded-file_64c942aa64.jpg'
        return os.path.join(self.path, renamed_filename)


class Profile(models.Model):
    user = models.OneToOneField(User, blank=True, null=True, on_delete=models.CASCADE)
    tel = models.CharField(max_length=300, blank=True, null=True, default="")

    def __str__(self):
        return self.user.username


class Address(models.Model):
    company = models.CharField(max_length=254, blank=True)
    address = models.TextField()
    city = models.CharField(max_length=254)
    post_code = models.CharField(max_length=254)
    country = models.CharField(max_length=254)
    region = models.CharField(max_length=254)


class CommerceCategory(models.Model):
    name = models.CharField(max_length=200)
    image_path = time.strftime('images/%Y/%m/%d')
    image = models.ImageField(upload_to=PathAndRename(image_path), default='/images/categories.jpg')

    def __str__(self):
        return self.name


class CommerceSCategory(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(CommerceCategory, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=200)
    image_path = time.strftime('images/%Y/%m/%d')
    image = models.ImageField(upload_to=PathAndRename(image_path), blank=True)

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    image_path = time.strftime('images/%Y/%m/%d')
    image = models.ImageField(upload_to=PathAndRename(image_path), default='/images/categories.jpg')
    date_add = models.DateField(auto_now_add=True)
    cat = models.ForeignKey(CommerceSCategory, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, blank=True)
    accessories = models.ManyToManyField("self", blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    number_views = models.IntegerField(default=0, null=False, blank=False, editable=True)

    def __str__(self):
        return self.name


class CommerceInformation(models.Model):
    value = models.TextField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return 'info {0} {1}'.format(str(self.pk), self.product.name)


class CommerceImage(models.Model):
    image_path = time.strftime('images/%Y/%m/%d')
    image = models.ImageField(upload_to=PathAndRename(image_path))
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return 'image {0} {1}'.format(str(self.pk), self.product.name)


class CommerceRatting(models.Model):
    value = models.DecimalField(max_digits=5, decimal_places=2)
    comment = models.TextField(blank=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(max_length=254),
    date_add = models.DateField(auto_now_add=True, editable=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return "vote {0},  {1} : {2}".format(str(self.pk), str(self.value), self.product.name)


class Color(models.Model):
    name = models.CharField(max_length=200)
    code_hex = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Stock(models.Model):
    quantity = models.IntegerField(default=0)
    first_quantity = models.IntegerField(default=0)
    price_sup = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return '{0} de {1} {2}'.format(str(self.quantity), self.product.name, self.color.name)
    
    def new_price(self):
        return self.product.price + self.price_sup
    
    def percent(self):
        return (self.quantity * 100) / self.first_quantity
    
    def sold(self):
        return self.first_quantity - self.quantity


class Specification(models.Model):
    name = models.CharField(max_length=200)
    value = models.CharField(max_length=1000)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return self.name + ' ' + self.product.name


class Sale(models.Model):
    percentage = models.IntegerField()
    date_end = models.DateTimeField(blank=False, default=timezone.now)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    is_daily = models.BooleanField(default=False)

    def __str__(self):
        return str(self.percentage) + "% for " + self.product.name
    
    def new_price(self):
        return self.product.price - ((self.product.price*self.percentage)/100) 


class WishList(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.user.username + ' ' + self.product.name


class Cart(models.Model):
    quantity = models.IntegerField(default=1)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)

    def total(self):
        return self.product.price * self.quantity

    def __str__(self):
        return '{0} {1} de {2}'.format(str(self.quantity), self.product.name, self.user.user.username)


payment_method = (('Cash On Delivery', 'Cash On Delivery'), ('Paypal', 'Paypal'))
delivery_method = (('Free Shipping', 'Free Shipping'), ('Flat Shipping Rate', 'Flat Shipping Rate'))


class Order(models.Model):
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=200, default="Shipped")
    payment_method = models.CharField(max_length=20, choices=payment_method, default='Cash On Delivery')
    delivery_method = models.CharField(max_length=20, choices=delivery_method, default='Free Shipping')
    comment = models.TextField(null=True)
    track_number = models.CharField(max_length=300, null=True)
    date_complete = models.DateField(null=True)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return 'Order {0} de {1}'.format(str(self.pk), self.user.user.username)


class OrderLine(models.Model):
    quantity = models.IntegerField()
    total = models.DecimalField(max_digits=15, decimal_places=2)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.ForeignKey(Color, on_delete=models.CASCADE)


class Slide(models.Model):
    image_path = time.strftime('slides/%Y/%m/%d')
    image = models.ImageField(upload_to=PathAndRename(image_path))
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    date_add = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)


class ShippingAddress(Address):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return '{0} {1}'.format(self.user.user.username, self.address)


class BillingAddress(Address):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return '{0} {1}'.format(self.user.user.username, self.address)


class Mailing(models.Model):
    email = models.EmailField(unique=True)
    active = models.BooleanField(default=True)
    date_add = models.DateField(auto_now_add=True)

    def __str__(self):
        return "{} is {}".format(self.email, self.active)


class Message(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    date_add = models.DateField(auto_now_add=True)

    def __str__(self):
        return "{} said '{}...'".format(self.name, self.message[:200])


class Description(models.Model):
    text = models.TextField()
    product = models.OneToOneField(Product, blank=False, null=False, on_delete=models.CASCADE)

    def __str__(self):
        return "{} : {}".format(self.product.name, self.text[:200])


class Compare(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.user.username + ' ' + self.product.name
