from django.shortcuts import render,redirect,get_object_or_404

from store.models import Product
from .forms import RegistationForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage, send_mail
from django.views.decorators.csrf import csrf_protect
from cart.models import Cart, CartItem
from cart.views import _cart_id
from orders.models import Order, OrderProduct
from smtplib import SMTPResponseException
from django.conf import settings
from django.http import HttpResponse
from .tokens import account_activation_token  
from orders.forms import OrderForm
from store.forms import ProductForm  # 


@csrf_protect
def activate(request, uidb64, token):  
    User = get_user_model()  
    try:  
        uid = force_str(urlsafe_base64_decode(uidb64))  
        user = User.objects.get(pk=uid)  
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):  
        user = None  
    if user is not None and account_activation_token.check_token(user, token):  
        user.is_active = True  
        user.save()  
        return HttpResponse('Thank you for your email confirmation. Now you can login your account.')  
    else:  
        return HttpResponse('Activation link is invalid!') 

@csrf_protect
def register(request):
    if request.method == 'POST':
        form = RegistationForm(request.POST)
        if form.is_valid():
            first_name= form.cleaned_data['first_name']
            last_name= form.cleaned_data['last_name']
            phone_number= form.cleaned_data['phone_number']
            email= form.cleaned_data['email']
            password= form.cleaned_data['password']
            username= email.split('@')[0]
            user= Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.save()

            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html',{
                 'user':user,
                 'domain': current_site, 
                 'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                 'token': default_token_generator.make_token(user), 
            })
            to_email = form.cleaned_data.get('email')
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            messages.success(request, 'Check email for verificate your account ')
            return redirect('/accounts/login/?command=verification&email='+email)
    else:
         form = RegistationForm()
        #  return render(request, 'accounts/register.html', {form: 'form'} )   
    context={
        'form':form,

    }
    return render(request, 'accounts/register.html', context)

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(email=email, password=password)

        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)

                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id_list = []

                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id_list.append(item.id)

                    for product in product_variation:
                        if product in ex_var_list:
                            index = ex_var_list.index(product)
                            item_id = id_list[index]
                            cart_item = CartItem.objects.get(id=item_id)
                            cart_item.quantity += 1
                            cart_item.user = user
                            cart_item.save()
                        else:
                            for item in cart_item:
                                item.user = user
                                item.save()
            except Cart.DoesNotExist:
                pass

            auth.login(request, user)

            # Ensure UserProfile exists for the user
            try:
                user_profile = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(user=user)

            messages.success(request, "You are now logged in")

            url = request.META.get("HTTP_REFERER")
            try:
                query = request.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')

    return render(request, 'accounts/login.html')

@login_required(login_url = 'login')
def logout(request):
    auth.logout(request)
    messages.success(request, "You are Logged out")
    return redirect('login')


def activate(request, uidb64, token):
    try:        
        uid= urlsafe_base64_decode(uidb64).decode()
        user= Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user=None

    if user is not None and default_token_generator.check_token(user, token):
         user.is_active = True
         user.save()
         messages.success(request, "Account is activated")
         return redirect('login')
    else:
         messages.error(request, 'Invalid activation link')
         print('Invalid activation link')
         return redirect('register')
         
         
@login_required(login_url='login')
def dashboard(request):
     orders =Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
     orders_count= orders.count()
     userprofile=UserProfile.objects.get(user_id=request.user.id)
     sample_product = Product.objects.first()  

     if request.user.is_superadmin:
        users = Account.objects.all()
     else:
        users = [request.user]
     context ={
          'orders_count' : orders_count,
          'userprofile': userprofile,
          'users': users,
          'sample_product':sample_product,
     }
     return render(request, 'accounts/dashboard.html', context)
   

def forgotPassword(request):
     if request.method == 'POST':
          email= request.POST['email']
          if Account.objects.filter(email=email).exists():
                user=Account.objects.get(email__exact=email)

                current_site = get_current_site(request)
                mail_subject = 'Please reset your password'
                message = render_to_string('accounts/reset_password_email.html',{
                    'user':user,
                    'domain': current_site, 
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user), 
                })
                to_email = email
                send_email = EmailMessage(mail_subject, message, to=[to_email])
                send_email.send()

                messages.success(request, "Password reset email has been sent to your email address")
                return redirect('login')


               
          else:
               messages.error(request, 'Account does not exist')
               return redirect('forgotPassword')
     return render(request, 'accounts/forgotPassword.html')


def resetpassword_validate(request, uidb64, token):
    try:        
        uid= urlsafe_base64_decode(uidb64).decode()
        user= Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user=None
    
    if user is not None and default_token_generator.check_token(user, token):
            request.session['uid']=uid
            messages.success(request, "Please reset your password")
            return redirect('resetPassword')
    else:
         messages.error(request, 'Expired link')
         return redirect('login')



def resetPassword(request):
     if request.method == 'POST':
          password = request.POST['password']
          confirm_password = request.POST['confirm_password']


          if password == confirm_password:
               uid=request.session.get('uid')
               user=Account.objects.get(pk=uid)
               user.set_password(password)
               user.save()
               messages.success(request, 'Password reset succesful')
               return redirect('login')
               
          else:
               messages.error('Password dont match')
               return redirect('resetPassword')
     else:
        return render(request, 'accounts/resetPassword.html')
     
@login_required(login_url='login')
def my_orders(request):
     orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
     context={
          'orders':orders,
     }

     return render(request, 'accounts/my_orders.html', context)

@login_required(login_url='login')
def edit_profile(request):
    userprofile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile has been updated')
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    # Safely handle profile_picture url
    if userprofile.profile_picture:
        profile_picture_url = userprofile.profile_picture.url
    else:
        profile_picture_url = None

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile_picture_url': profile_picture_url,
    }

    return render(request, 'accounts/edit_profile.html', context)





@login_required(login_url='login')
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__orders_number=order_id)
    order = Order.objects.get(orders_number=order_id)
    subtotal = 0
    for i in order_detail:
        subtotal += i.product_price * i.quantity
    context = {
       
        'order_detail': order_detail,
        'order': order,
        'subtotal': subtotal,
    }   
    return render(request, 'accounts/order_detail.html', context)



def edit_order(request, orders_number):
    order = get_object_or_404(Order, orders_number=orders_number)

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('order_detail', order_id=order.orders_number)
    else:
        form = OrderForm(instance=order)

    context = {
        'form': form,
        'order': order,
    }
    return render(request, 'orders/edit_order.html', context)

def delete_order(request, orders_number):
    order = get_object_or_404(Order, orders_number=orders_number)

    if request.user == order.user:
        order.delete()
        return redirect('dashboard')
    else:
        return render(request, 'error_page.html', {'error_message': 'You do not have permission to delete this order'})
    





def add_product(request):
    if request.user.is_superadmin:
        if request.method == 'POST':
            form = ProductForm(request.POST, request.FILES)
            if form.is_valid():
                product = form.save(commit=False)
                product.created_by = request.user
                product.save()
                return redirect('store')  
        else:
            form = ProductForm()

        context = {'form': form}
        return render(request, 'accounts/add_product.html', context)
    else:
          return HttpResponseForbidden("You don't have permission to edit this product.")

def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.user.is_superadmin or request.user == product.created_by:
        if request.method == 'POST':
            form = ProductForm(request.POST, request.FILES, instance=product)
            if form.is_valid():
                form.save()
                return redirect('store')  
        else:
            form = ProductForm(instance=product)

        context = {'form': form, 'product': product}
        return render(request, 'accounts/edit_product.html', context)
    else:
        return HttpResponseForbidden("You don't have permission to edit this product.")

def delete_product(request, product_id):
    if request.user.is_superadmin:
        product = get_object_or_404(Product, id=product_id)
        product.delete()
        return redirect('store')  
    else:
        return HttpResponseForbidden("You don't have permission to delete this product.")
    
@login_required(login_url='login')
def change_password(request):
    if request.method ==  'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success: 
                user.set_password(new_password)
                user.save()

                messages.success(request, "Password updated succesfuly")
                return redirect('change_password')
            else:
                messages.error(request, "Please enter valid current password")
                return redirect('change_password')
        else:
            messages.error(request, "Password does not match")
            return redirect('change_password')
        

    return render(request, 'accounts/change_password.html')