from django.shortcuts import render, get_object_or_404
from .models import Product
from category.models import Category
from cart.models import CartItem
from cart.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger,Paginator
from django.http import HttpResponse
from django.db.models import Q
from django.shortcuts import render
from django.db.models import Min, Max
# Create your views here.

def store(request, category_slug=None):
    categories =None
    products=None

    if category_slug!=None:
        categories = get_object_or_404(Category, slug=category_slug)
        products= Product.objects.filter(category=categories, is_avaliable=True)
        paginator= Paginator(products, 2)
        page=request.GET.get('page')
        paged_products=paginator.get_page(page)
        product_count= products.count()
    else:
        products= Product.objects.all().filter(is_avaliable=True).order_by('id')
        paginator= Paginator(products, 6)
        page=request.GET.get('page')
        paged_products=paginator.get_page(page)
        product_count= products.count()

  
    context={
        'products': paged_products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product=Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart=CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
    }
    return render(request, 'store/product_detail.html', context)


def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products= Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
            product_count= products.count()

    context ={
        'products': products,
        'product_count': product_count,
    }
    return render(request, 'store/store.html', context)


def product_list(request):
    min_price = Product.objects.all().aggregate(Min('price'))['price__min']
    max_price = Product.objects.all().aggregate(Max('price'))['price__max']

    return render(request, 'store/product_list.html', {'min_price': min_price, 'max_price': max_price})

def filter_by_price(request):
    if request.method == 'GET':
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')

        # Assuming you have a form to get the min and max prices
        products = Product.objects.filter(price__range=(min_price, max_price))

        return render(request, 'store/filtered_product_list.html', {'products': products})