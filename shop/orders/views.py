from django.shortcuts import render, redirect,get_object_or_404
from cart.models import CartItem
from .forms import OrderForm
from .models import Order, OrderProduct
import datetime
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_protect
from .models import Payment
from django.http import HttpResponseBadRequest
import json
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

@csrf_protect
def payments(request):
    try:
        body = json.loads(request.body)
        print(f"Request body: {body}")
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

    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()


        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()


    CartItem.objects.filter(user=request.user).delete()

    mail_subject = 'Succesfull ordering!'
    message = render_to_string('orders/order_recieved_email.html',{
                 'user': request.user,
                 'order': order, 
            })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    data = {
        'orders_number': order.orders_number,
        'transID' : payment.payment_id,
    }
    return JsonResponse(data)
    # return render(request, 'orders/payments.html')

# Create your views here.
@csrf_protect
def order_place(request, total=0, quantity=0):
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
            month = int(datetime.date.today().strftime('%m'))  
            day = int(datetime.date.today().strftime('%d'))
            d = datetime.datetime(year, month, day)
            current_date = d.strftime("%Y%m%d")
            orders_number = current_date + str(data.id)
            data.orders_number = orders_number
            data.save()
            order=Order.objects.get(user=current_user, is_ordered=False, orders_number=orders_number)
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
        

def order_complete(request):
    
    orders_number= request.GET.get('orders_number')
    transID= request.GET.get('payment_id')

    try:
        order = Order.objects.get(orders_number=orders_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity


        payment = Payment.objects.get(payment_id=transID)
        context = {
                'order': order,
                'ordered_products': ordered_products,
                'orders_number': order.orders_number,
                'transID': payment.payment_id,
                'payment': payment,
                'subtotal': subtotal,
        }
    
    except:
        return redirect('https://mail.google.com/')