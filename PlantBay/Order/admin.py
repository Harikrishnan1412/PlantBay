from django.contrib import admin
from .models import Item, Order, OrderItem, Payment, Coupon, Refund, Address
# Register your models here.

def make_refund_accepted(modeladmin, request, quaryset):
    quaryset.update(refund_requested=False, refund_granted=True)

make_refund_accepted.short_description = 'Update order to refund Granted'

class OrderAdmin(admin.ModelAdmin):
    list_display = ['user',
                    'ordered',
                    'being_delivered',
                    'received',
                    'refund_requested',
                    'refund_granted',
                    'billing_address',
                    'shipping_address',
                    'payment',
                    'coupon'
                    ]
    list_display_links = [
        'user',
        'billing_address',
        'shipping_address',
        'payment',
        'coupon'
    ]
    search_fields = [
        'user__user',
        'ref_code'
    ]
    list_filter = ['ordered',
                    'being_delivered',
                    'received',
                    'refund_requested',
                    'refund_granted'
                    ]
    actions = [make_refund_accepted]

class AddressAdmin(admin.ModelAdmin):
    list_display = [
                    'user',
                    'street_address',
                    'apartment_address',
                    'country',
                    'zip',
                    'address_type',
                    'default'
    ]

    list_filter = ['default', 'address_type', 'country']

    search_fields = ['user', 'street_address', 'apartment_address', 'zip']

admin.site.register(Item)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Address, AddressAdmin)
