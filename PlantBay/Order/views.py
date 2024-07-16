import time
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from .models import  Coupon, Item, OrderItem, Order,Payment, Refund, Address
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from .forms import CheckoutForm, CouponForm, RefundForm
import stripe
import random
import string
from django.core.mail import send_mail
from PlantBay.settings import EMAIL_HOST_USER
import threading
stripe.api_key = settings.STRIPE_SECRET_KEY

# Email thread
class EmailThread(threading.Thread):
    def __init__(self, subject, message, EMAIL_HOST_USER, recipient_list):
        self.subject = subject
        self.message = message
        self.EMAIL_HOST_USER = 'PlantBay <'+EMAIL_HOST_USER+'>'
        self.recipient_list = recipient_list
        threading.Thread.__init__(self)

    def run(self):
        send_mail(self.subject, self.message, EMAIL_HOST_USER, self.recipient_list) 



def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid

# Create your views here.
# def item_list(request):
#     context = {
#         'object_list':Item.objects.all()
#     }
#     return render(request, "product.html", context)



class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user= self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                'form':form,
                'couponform': CouponForm(),
                'order':order,
                'DISPLAY_COUPON_FORM':True
            }

            shipping_address_qs = Address.objects.filter(
                user = self.request.user,
                address_type = 'S',
                default = True
            )

            if shipping_address_qs.exists():
                context.update({
                    'default_shipping_address' : shipping_address_qs[0]
                })

            billing_address_qs = Address.objects.filter(
                user = self.request.user,
                address_type = 'B',
                default = True
            )

            if shipping_address_qs.exists():
                context.update({
                    'default_billing_address' : billing_address_qs[0]
                })

            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You dont have a active order")
            return redirect("Order:checkout")
        
    
    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user = self.request.user, ordered=False)
            if form.is_valid():
                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print("Using the defualt shipping address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:

                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')
                    same_billing_address =form.cleaned_data.get('same_billing_address')
                    save_info =form.cleaned_data.get('save_info')
                    #payment_option = form.cleaned_data.get('payment_option')
                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                            shipping_address = Address(
                                user=self.request.user,
                                street_address=shipping_address1,
                                apartment_address=shipping_address2,
                                country=shipping_country,
                                zip=shipping_zip,
                                address_type='S'
                            )
                            shipping_address.save()

                            order.shipping_address = shipping_address
                            order.save()

                            set_default_shipping = form.cleaned_data.get(
                                'set_default_shipping')
                            if set_default_shipping:
                                shipping_address.default = True
                                shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")

                set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                if set_default_shipping:
                    shipping_address.default = True
                    shipping_address.save()

                else:
                    messages.info(
                        self.request, "Please fill in the required shipping address fields")
                    
                # Billing Address from form
                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")

                payment_option = form.cleaned_data.get('payment_option')
                if payment_option == 'S':
                    return redirect('Order:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('Order:payment', payment_option='paypal')
                else:
                    messages.warning(
                        self.request, "Invalid payment option selected")
                    return redirect('Order:checkout')
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("Order:order-summary")
        


class HomeView(ListView):
    model = Item
    paginate_by = 4
    template_name = "home.html"

# class Home_plant_View(View):
#     model = Item
#     paginate_by = 1
#     def get(self, *args, **kwargs):
#         try:
#             items = Item.objects.filter(category= 'P')
#             context = {
#                 'object_list':items
#             }
#             return render(self.request, 'home.html', context)
#         except ObjectDoesNotExist:
#             messages.info(self.request, "Sorry, there no product available")
#             return redirect('/')

class SearchView(ListView):
    model = Item
    paginate_by = 4
    template_name = 'home.html'
    context_object_name = 'object_list'
    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            items = Item.objects.filter(title=query)
            return items
        else:
            messages.info(self.request, "Sorry, there are no products available")
            return Item.objects.none()


class Home_plant_View(ListView):
    model = Item
    paginate_by = 4
    template_name = 'home.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        try:
            items = Item.objects.filter(category='P')
            return items
        except ObjectDoesNotExist:
            messages.info(self.request, "Sorry, there are no products available")
            return Item.objects.none()

class Home_plant_supply_View(ListView):
    model = Item
    paginate_by = 4
    template_name = 'home.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        try:
            items = Item.objects.filter(category='PS')
            return items
        except ObjectDoesNotExist:
            messages.info(self.request, "Sorry, there are no products available")
            return Item.objects.none()
        
class Home_plant_decor_View(ListView):
    model = Item
    paginate_by = 4
    template_name = 'home.html'
    context_object_name = 'object_list'

    def get_queryset(self):
        try:
            items = Item.objects.filter(category='GD')
            return items
        except ObjectDoesNotExist:
            messages.info(self.request, "Sorry, there are no products available")
            return Item.objects.none()


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user = self.request.user, ordered=False)
            context = {
                'object':order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have active Order.")
            return redirect("/")
        

class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"

# Below is the home page function view
# def home(request):
#     context = {
#         'object_list':Item.objects.all()
#     }
#     return render(request,"home.html", context)

# Funtion or Add to cart
@login_required
def user_order(request):
    orders = Order.objects.filter(user = request.user, ordered=True)
    context = {
        'orders':orders
    }
    return render(request, "Order/order.html", context)



@login_required
def add_to_cart(request,slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user = request.user,
        ordered = False
                                                 )
    order_qs = Order.objects.filter(user=request.user, ordered = False)
    # If items in cart for the users
    if order_qs.exists():
        order = order_qs[0]
        # Check if order item is already order then increase the Quantity
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity is updated,.")
        else:
            messages.info(request, "This item is added to the cart.")
            order.items.add(order_item)
    # If no item in cart  
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user = request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item is added to the cart.")
    return redirect("Order:order_summary")

@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    # Collect order of the User
    order_qs = Order.objects.filter(
        user = request.user,
        ordered = False
    )
    if order_qs.exists():
        order = order_qs[0]
        # In the collected order check for particular Item
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item = item,
                user = request.user,
                ordered = False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "This item is removed from your cart.")
            return redirect("Order:order_summary")
        else:
            messages.info(request, "This item is not in the cart.")
            return redirect("Order:order_summary")
    else:
        messages.info(request, "You dont have an active order.")
        return redirect("Order:order_summary")

@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    # Collect order of the User
    order_qs = Order.objects.filter(
        user = request.user,
        ordered = False
    )
    if order_qs.exists():
        order = order_qs[0]
        # In the collected order check for particular Item
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item = item,
                user = request.user,
                ordered = False
            )[0]
            if order_item.quantity >1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity is removed.")
            return redirect("Order:order_summary")
        else:
            messages.info(request, "This item is not in the cart.")
            return redirect("Order:order_summary")
    else:
        messages.info(request, "You dont have an active order.")
        return redirect("Order:order_summary")
    
def create_or_get_customer(email):
    try:
        # Check if customer exists in Stripe by email
        customers = stripe.Customer.list(email=email)
        if customers.data:
            # Customer exists, return the first customer found
            return customers.data[0]  # Assuming there's only one customer with the email
        else:
            # Customer does not exist, create a new customer
            customer = stripe.Customer.create(email=email)
            return customer
    except stripe.error.StripeError as e:
        # Handle Stripe errors
        print(f"Stripe error: {e}")
        return None
    
class PaymentView(View):
    def get(self, *args, **kwargs):
        print("INside Payment Get")
        order = Order.objects.get(user = self.request.user, ordered=False)
        print(settings.STRIPE_PUBLIC_KEY)
        if order.billing_address:
            context = {
                'STRIPE_PUBLIC_KEY' : settings.STRIPE_PUBLIC_KEY,
                'order':order,
                'DISPLAY_COUPON_FORM':False
            }
            return render(self.request, "payment.html", context)
        else:
            messages.warning(
                self.request, "You have not added a billing address")
            return redirect("Order:checkout")
    
    def post(self, *args, **kwargs):
        print("POST Payment view method")
        #time.sleep(10)
        #print(Order.objects.get(user = self.request.user))
        order = Order.objects.get(user = self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        print("This is Token")
        print(self.request.POST)
        print(token)
        amount = int(order.get_total()*100)

        try:
            print("Inside charge try")
            #print(self.request.user.email)

            customer = create_or_get_customer(email=self.request.user.email)

            source = stripe.Source.create(
                type='card',  # Example: Use 'card' for credit/debit card
                token=self.request.POST.get('stripeToken')  # Token from Stripe.js or Elements
            )

            # customer = stripe.Customer.create(
            # email=self.request.user.email,
            # source=source.id
            #  )
            
            # if 'source' not in customer:
            #     # If not attached, create and attach the source
            #     stripe.Customer.create_source(
            #         customer.id,
            #         source=self.request.POST.get('stripeToken')
            #     )

            print("Passed Customer")
            charge = stripe.Charge.create(
                customer=customer.id,
                amount=amount,
                currency='usd',
                description='Payment for Order {}'.format(order.id),
                source= source.id # Source token from Stripe.js or Elements self.request.POST.get('stripeToken')
            )
            # Create Payment
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()
            #Every item in order make it ordered
            order_item = order.items.all()
            order_item.update(ordered=True)
            for item in order_item:
                item.save()
            # assign payment in Order
            order.ordered = True
            order.payment = payment
            order.ref_code = create_ref_code()
            order.save()
            subject = 'Payment is Done' 
            message = 'Hi '+str(self.request.user)+','+' Thank you for purchasing in PlantBay'+'\n You can track your order in website'
            email =str(self.request.user.email)
            recipient_list = [email]
            # send_mail(subject, message, EMAIL_HOST_USER, recipient_list, fail_silently=True) 
            EmailThread(subject, message, EMAIL_HOST_USER, recipient_list).start()
            print("Message sended")
            messages.success(self.request, "Your order is sucessful!")
            return redirect("/")
        except stripe.error.StripeError as e:
            print("this is error message")
            print(e)
            messages.warning(self.request, "There is an Error, please try again ")
            return redirect("/")

def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except:
        messages.info(request, "Thi coupon does ot exist")
        return redirect("Order:checkout")
   
class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user= self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("Order:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You dont have a active order")
                return redirect("Order:checkout")
            
class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form':form
        }
        return render(self.request, "request_refund.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            #edit order
            try:
                order = Order.objects.get(ref_code = ref_code)
                order.refund_requested = True
                order.save()
                #makingg refund request
                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()
                messages.info(self.request, "Your request is received")
                return redirect('Order:request_refund')
            except ObjectDoesNotExist:
                messages.info(self.request, "You dont have a active order")
                return redirect('Order:request_refund')
            
            


    
        

   

