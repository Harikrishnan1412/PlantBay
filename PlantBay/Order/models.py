from django.db import models
from django.conf import settings
from django.shortcuts import reverse
from django_countries.fields import CountryField
from django.core.mail import send_mail
from PlantBay.settings import EMAIL_HOST_USER
import threading
from django.db.models.signals import post_save

# Email Thread
class EmailThread(threading.Thread):
    def __init__(self, subject, message, EMAIL_HOST_USER, recipient_list):
        self.subject = subject
        self.message = message
        self.EMAIL_HOST_USER = 'PlantBay <'+EMAIL_HOST_USER+'>'
        self.recipient_list = recipient_list
        threading.Thread.__init__(self)

    def run(self):
        send_mail(self.subject, self.message, EMAIL_HOST_USER, self.recipient_list) 

# Create your models here.
CATEGORY_CHOCIES = (
    ('P','Plants'),
    ('PS','Plan_Supplies'),
    ('GD','Garden_decorator')
)

LABEL_CHOCIES = (
    ('P','primary'),
    ('S','secondary'),
    ('D','danger')
)

ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)

class Userprofile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.user.username


class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.FloatField()
    discount_price = models.FloatField(null=True, blank=True)
    category = models.CharField(choices=CATEGORY_CHOCIES, max_length=2)
    label = models.CharField(choices=LABEL_CHOCIES, max_length=1)
    description = models.TextField()
    slug = models.SlugField()
    image = models.ImageField(blank=True, null=True)


    def __str__(self):
        return self.title
    
    # ShortCut methos for getting url
    def get_absolute_url(self):
        return reverse("Order:product", kwargs={"slug": self.slug})
    
    def get_add_to_cart_url(self):
        return reverse("Order:add_to_cart", kwargs={"slug": self.slug})
    
    def get_remove_from_cart_url(self):
        return reverse("Order:remove_from_cart", kwargs={"slug": self.slug})
    
    
    
class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True,null=True)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)


    def __str__(self):
        return f"{self.quantity} of {self.item.title}"
    
    def get_total_item_price(self):
        return self.quantity * self.item.price
    
    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price
    
    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()
    
    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()
    
class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=50)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    shipping_address = models.ForeignKey(
        'Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True
    )
    billing_address = models.ForeignKey(
        'Address', related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True
    )
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True
    )
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, blank=True, null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)


    '''
    Ordered life cycle
    1.item added to cart
    2.Adding billing Address
    3.Payment
    4.(preprocessing, processing, packing)Being delivered
    5.Received
    6.Refunds
    
    '''

    def __str__(self):
        return f"Order #{self.id}"
    
    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total = total + order_item.get_final_price()
        if self.coupon:
            total -= self.coupon.amount
        return total


class Address(models.Model):
    user =models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
    class Meta:
        verbose_name_plural = 'Addresses'


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id}"
    

class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code
    
class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"{self.pk}"
    
def userprofile_receiver(sender, instance, created, *args, **kwargs):
    if created:
        userprofile = Userprofile.objects.create(user=instance)
        print("Inside Create")
        # Send Email
        subject = 'Account is Created' 
        message = 'Hi '+instance.username+','+' Thank you for choosing PlantBay'
        email =instance.email
        recipient_list = [email]
        # send_mail(subject, message, EMAIL_HOST_USER, recipient_list, fail_silently=True) 
        EmailThread(subject, message, EMAIL_HOST_USER, recipient_list).start()
        print("Message sended")
        # End of email send

post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)