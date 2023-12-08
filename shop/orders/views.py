from django.shortcuts import render, redirect
from cart.models import CartItem
from .forms import OrderForm
from .models import Order
import datetime
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
from .models import Payment
from django.http import HttpResponseBadRequest
import json


@csrf_protect
def payments(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        print(f"Request body: {request.body}")
        return HttpResponseBadRequest("Invalid JSON data in the request body.")

    required_keys = ['orderID', 'transID', 'payment_method', 'status']

    if not all(key in body for key in required_keys):
        return HttpResponseBadRequest("Missing required keys in the JSON data.")

    try:
        order = Order.objects.get(user=request.user, is_ordered=False, orders_number=body['orderID'])
    except Order.DoesNotExist:
        return HttpResponseBadRequest("Order not found.")

    payment = Payment(
        user=request.user,
        payment_id=body['transID'],
        payment_method=body['payment_method'],
        amount_id=order.order_total,
        status=body['status'],
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    return render(request, 'orders/payments.html')

# Create your views here.
@csrf_protect
def order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        print(form.is_valid()) 
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone_number = form.cleaned_data['phone_number']
            data.email = form.cleaned_data['email']
            data.address = form.cleaned_data['address']
            data.country = form.cleaned_data['country']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            year = int(datetime.date.today().strftime('%Y'))
            month = int(datetime.date.today().strftime('%d'))
            day = int(datetime.date.today().strftime('%m'))
            d = datetime.datetime(year, month, day)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.orders_number = order_number
            data.save()
            order=Order.objects.get(user=current_user, is_ordered=False, orders_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,

            }
            return render(request, 'orders/payments.html', context)
        else:
            print(form.errors)
            return HttpResponse("Not valid Form")
    else:
        return redirect('checkout')
        

 