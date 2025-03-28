import csv
from dataclasses import field
import datetime
from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Order,OrderItem


def export_to_csv(modeladmin,request,queryset):
    opts = modeladmin.model._meta
    content_disposition = (
        f'attachment; filename={opts.verbose_name}.csv'
    )
    response = HttpResponse(content_type='text/csv')
    response['Content_Disposition'] = content_disposition
    writer = csv.writer(response)
    fields =[
        field 
        for field in opts.get_fields()
        if not field.many_to_many and not field.one_to_many
    ]
    writer.writerow(field.verbose_name for field in fields)
    for obj in queryset:
        data_row = []
        for field in fields:
            value = getattr(obj,field.name)
            if isinstance(value,datetime.datetime):
                value = value.strftime ("%d/%m/%Y")
            data_row.append(value)
        writer.writerow(data_row)
    return response

export_to_csv.short_description  = 'Export to CSV'


class OrderItemInline(admin.TabularInline):
    model  = OrderItem
    raw_id_fields = ['product']

# Register your models here.
def order_payment(obj):
    url = obj.get_stripe_uri()
    if obj.stripe_id:
        html = f'<a href="{url}" target="_blank">{obj.stripe_id}'
        return mark_safe(html)
order_payment.short_description = 'Stripe Payment'

def order_details(obj):
    url = reverse('orders:admin_order_details',args=[obj.id])
    return mark_safe(f'<a href={url}>View</a>')

def order_pdf(obj):
    url = reverse('orders:admin_order_pdf',args=[obj.id])
    return mark_safe(f'<a href={url}>Pdf</a>')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id','first_name','last_name','email','address','city','postal_code','paid','created','updated','stripe_id',order_payment,order_details,order_pdf
    ]
    list_filters = ['paid','created','filter']
    inlines   = [OrderItemInline]
    actions = [export_to_csv]
