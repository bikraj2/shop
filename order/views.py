import weasyprint
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from cart.cart import Cart
from order.forms import OrderCreateForm
from .models import Order, OrderItem
from order.tasks import order_created
from django.contrib.admin.views.decorators import staff_member_required
def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form =  OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save()
            if cart.coupon:
                order.coupon = cart.coupon
                order.discount = cart.coupon.discount
                order.save()
            for item in cart:
                OrderItem.objects.create(
                    orders = order,
                    product = item['product'],
                    price = item['price'],
                    quantity = item['quantity']
                )
            cart.clear()
            order_created.delay(order.id)
            request.session['order_id'] = order.id
            return redirect('payment:process')
    else:
        form = OrderCreateForm()
        return render(
            request,
           'orders/order/create.html',
            {
                'cart':cart, 'form':form
            }
        )

@staff_member_required
def admin_order_details(request,order_id):
    order = get_object_or_404(Order,id=order_id)
    return render(
        request,'admin/orders/order/detail.html',
        {
            'order':order
        }
    )


@staff_member_required
def admin_order_pdf(request,order_id):
    order = get_object_or_404(Order,id=order_id)
    html = render_to_string('orders/order/pdf.html', {'order':order})
    response = HttpResponse(content_type = 'application/pdf')
    response['Content-Disposition'] = f'filename=order_{order_id}.pdf'
    weasyprint.HTML(string=html).write_pdf(
        response,
        stylesheets=[weasyprint.CSS(finders.find('css/pdf.css'))])
    return response
