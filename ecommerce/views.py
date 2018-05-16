from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
#from django.contrib.auth.models import User
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from .models import *
from .models import Profile as Profil
from django.db.models import Max, Avg, Sum, Q, Count
from django.db.models.functions import Lower
from django.utils import timezone
from decimal import Decimal, Inexact
import datetime


def index(request):
    #--------------- User ---------------
    user = request.user

    #---------------- number items in wishlist
    if user.is_authenticated:
        number_items_wish_list = WishList.objects.filter(user__user=user).count()
    else:
        number_items_wish_list = 0

    #---------------- number items in compare
    if user.is_authenticated:
        number_items_compare = Compare.objects.filter(user__user=user).count()
    else:
        number_items_compare = 0

    #--------------- All Categories ---------------
    categories = all_categories()

    #--------------- Hot Categories ---------------
    hot_categories = my_featured_sale()['hot_categories']

    #--------------- All Tags ---------------
    tags = all_tags()

    #--------------- All Brands with images---------------
    brands = Brand.objects.exclude(image='')

    #--------------- Slides ---------------
    slides = Slide.objects.filter(active=True).order_by('date_add')

    #--------------- Cart ---------------
    my_cart_result = my_cart(user)
    number_products_in_cart = my_cart_result['number_products_in_cart']
    total_price_in_cart = my_cart_result['total_price_in_cart']
    cart_result = my_cart_result['cart']

    #--------------- Featured Sale ---------------
    featured_sale = my_featured_sale()['featured_sale']

    #--------------- Daily Deals ---------------
    daily_deals = Sale.objects.filter(is_daily=True).values('id').annotate(ratting=Avg('product__commerceratting__value'))
    for el in daily_deals:
        sale = Sale.objects.get(pk=el['id'])
        if el['ratting']:
            el['rattingInt'] = int(el['ratting'])
        else:
            el['rattingInt'] = 0
            el['ratting'] = 0
        el['id'] = sale
        el['quantity'] = el["id"].product.stock_set.aggregate(Sum('quantity'))["quantity__sum"]
        el['first_quantity'] = el["id"].product.stock_set.aggregate(Sum('first_quantity'))["first_quantity__sum"]
        el['percent'] = (el['quantity'] * 100) / el['first_quantity']
        el['sold'] = el['first_quantity'] - el['quantity']

    #--------------- Best Selling Products ---------------
    best_selling = OrderLine.objects.values('product__id').annotate(quantity=Sum('quantity')).order_by('-quantity')[:10]
    #convert to list
    best_selling = list(best_selling)
    # Complete 10 products
    count = len(best_selling)
    if count < 10:
        for i in range(0, Product.objects.count()):
            product_to_add = {'product__id': Product.objects.all()[i].id, 'quantity': 0}
            if product_to_add not in best_selling:
                best_selling.append(product_to_add)
            if len(best_selling) == 10:
                break
    #treatement
    for el in best_selling:
        product = Product.objects.get(pk=el['product__id'])
        el['product__id'] = product
        if (datetime.date.today() - product.date_add).days < 30:
            el['is_new'] = True
        else:
            el['is_new'] = False
        ratting = product.commerceratting_set.aggregate(ratting=Avg('value'))
        el['ratting'] = ratting['ratting']
        if el['ratting']:
            el['rattingInt'] = int(el['ratting'])
        else:
            el['rattingInt'] = 0
            el['ratting'] = 0
        sale = product.sale_set.filter(date_end__gte=timezone.now()).order_by('date_end')
        if sale.exists():
            el['sale'] = sale[0]
        else:
            el['sale'] = None

    #--------------- Most Viewed Products ---------------
    most_viewed = list()

    products_viewed = Product.objects.order_by('-number_views')[:8]
    #    CommerceRatting.objects.values('product__id').annotate(views=Count('id'), ratting=Avg('value')).order_by('-views')
    for el in products_viewed:
        ob = dict()
        ob['product'] = el
        #ratting average
        ratting = el.commerceratting_set.aggregate(ratting=Avg('value'))
        if ratting['ratting'] is not None:
            ob['ratting'] = ratting['ratting']
            ob['rattingInt'] = int(ratting['ratting'])
        else:
            ob['ratting'] = 0
            ob['rattingInt'] = 0
        most_viewed.append(ob)
        del ob

    context = {
        #for base.html
        'categories': categories,
        'number_items_wish_list': number_items_wish_list,
        'number_items_compare': number_items_compare,
        'hot_categories': hot_categories[:4],
        'tags': tags,
        'cart': cart_result,
        'total_price_in_cart': total_price_in_cart,
        'number_products_in_cart': number_products_in_cart,

        'slides': slides,
        'featured_sale': featured_sale,
        'daily_deals': daily_deals,
        'best_selling': best_selling,
        'most_viewed': most_viewed,
        'brands': brands,
    }
    return render(request, 'ecommerce/index.html', context)


def search(request):
    user = request.user

    #---------------- number items in wishlist
    if user.is_authenticated:
        number_items_wish_list = WishList.objects.filter(user__user=user).count()
    else:
        number_items_wish_list = 0

    #---------------- number items in compare
    if user.is_authenticated:
        number_items_compare = Compare.objects.filter(user__user=user).count()
    else:
        number_items_compare = 0

    # --------------- All Categories ---------------
    categories = all_categories()

    # --------------- Hot Categories ---------------
    hot_categories = my_featured_sale()['hot_categories']

    # --------------- All Tags ---------------
    tags = all_tags()

    # --------------- Cart ---------------
    my_cart_result = my_cart(user)
    number_products_in_cart = my_cart_result['number_products_in_cart']
    total_price_in_cart = my_cart_result['total_price_in_cart']
    cart_result = my_cart_result['cart']

    #Initialisation
    category_id = category = word = list_products = min_value = max_value = number_elements = sort_by = None
    brands_id = colors_id = page_range = []
    type_search = "All"

    filter_by_price = is_filtered = False
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        word = request.POST.get('word')
        min_value = request.POST.get('min_val')
        max_value = request.POST.get('max_val')
        colors_id = request.POST.getlist('color')
        brands_id = request.POST.getlist('brand')
        is_filtered = request.POST.get('filter')
        filter_by_price = request.POST.get('price')
        page = request.POST.get('page', 1)
        number_elements = request.POST.get('number_elements', 15)
        sort_by = request.POST.get("sort_by", "1")

        # Stock dans une session
        if is_filtered:
            if colors_id:
                request.session['colors_id'] = colors_id
            else:
                try:
                    del request.session['colors_id']
                except KeyError:
                    print('exception de suppression session colors')
            if brands_id:
                request.session['brands_id'] = brands_id
            else:
                try:
                    del request.session['brands_id']
                except KeyError:
                    print('exception de suppression session brands')
        elif 'colors_id' in request.session:
            colors_id = request.session['colors_id']
        elif 'brands_id' in request.session:
            colors_id = request.session['brands_id']

        if category_id:
            request.session['category_id'] = category_id
        elif 'category_id' in request.session:
            category_id = request.session['category_id']

        if word:
            request.session['word'] = word
        elif 'word' in request.session:
            word = request.session['word']

        products_results = Product.objects.filter(Q(name__icontains=word) | Q(tags__name__icontains=word))
        if sort_by == "2":
            products_results = products_results.order_by(Lower("name"))
        elif sort_by == "3":
            products_results = products_results.order_by(Lower('name')).reverse()
        elif sort_by == "4":
            products_results = products_results.order_by('price')
        elif sort_by == "5":
            products_results = products_results.order_by('-price')
        elif sort_by == "8":
            products_results = products_results.order_by(Lower('brand__name'))
        elif sort_by == "9":
            products_results = products_results.order_by(Lower('brand__name')).reverse()
        elif sort_by == "10":
            products_results = products_results.order_by('-date_add')
        elif sort_by == "11":
            products_results = products_results.order_by('date_add')
        if products_results.exists():
            if category_id[0] == '-':
                products_results = products_results.filter(cat_id=category_id[1:])
                category = CommerceSCategory.objects.get(pk=category_id[1:])
                type_search = "sub_category"
            elif not category_id == '0':
                products_results = products_results.filter(cat__category__id=category_id)
                category = CommerceCategory.objects.get(pk=category_id)
                type_search = "category"

            #----------------- filter by range price
            if filter_by_price:
                if max_value:
                    request.session['max_value'] = max_value
                    try:
                        Decimal(max_value)
                        products_results = products_results.filter(price__lte=max_value)
                    except Inexact:
                        print('exception conversion')
                else:
                    max_value = request.session['max_value']
                    try:
                        Decimal(max_value)
                        products_results = products_results.filter(price__lte=max_value)
                    except Inexact:
                        print('exception conversion')
                if min_value:
                    if min_value:
                        request.session['min_value'] = min_value
                        try:
                            Decimal(min_value)
                            products_results = products_results.filter(price__gte=min_value)
                        except Inexact:
                            print('exception conversion')
                    else:
                        min_value = request.session['min_value']
                        try:
                            Decimal(min_value)
                            products_results = products_results.filter(price__gte=min_value)
                        except Inexact:
                            print('exception conversion')

            #--------------- filter by colors
            if colors_id:
                products_results = products_results.filter(stock__color_id__in=colors_id)

            #--------------- filter by brands
            if brands_id:
                products_results = products_results.filter(brand_id__in=brands_id)

            # select id, Avg(value) from product inner join commerce_ratting
            products_results = products_results.values('id').annotate(ratting=Avg('commerceratting__value'))
            if sort_by == "6":
                products_results = products_results.order_by('-ratting')
            if sort_by == "7":
                products_results = products_results.order_by('ratting')

            for el in products_results:
                product = Product.objects.get(pk=el['id'])
                el['id'] = product

                if el['ratting']:
                    el['rattingInt'] = int(el['ratting'])
                else:
                    el['rattingInt'] = 0
                    el['ratting'] = 0

                if (timezone.localtime(timezone.now()).date() - product.date_add).days < 30:
                    el['new'] = True
                else:
                    el['new'] = False

                sale = product.sale_set.filter(date_end__gte=timezone.now()).order_by('date_end')
                if sale.exists():
                    el['sale'] = sale[0]
                else:
                    el['sale'] = None
                if product.stock_set.exists():
                    el['quantity'] = product.stock_set.aggregate(quantity=Sum('quantity'))["quantity"]
                    el['first_quantity'] = product.stock_set.aggregate(quantity=Sum('first_quantity'))["quantity"]
                else:
                    el['quantity'] = 0
                    el['first_quantity'] = 0

                images = CommerceImage.objects.filter(product=product)
                if images.exists():
                    el['image'] = images[0].image
                else:
                    el['image'] = None

                el['sold'] = el['first_quantity'] - el['quantity']

            paginator = Paginator(products_results, number_elements)
            try:
                list_products = paginator.page(page)
            except PageNotAnInteger:
                list_products = paginator.page(1)
            except EmptyPage:
                list_products = paginator.page(paginator.num_pages)

            # range for display just 7 numbers
            index_page = list_products.number - 1
            max_index = len(paginator.page_range)
            start_index = index_page - 4 if index_page >= 4 else 0
            end_index = index_page + 4 if index_page <= max_index - 4 else max_index
            page_range = list(paginator.page_range)[start_index:end_index]
    #------------------ colors, brands ------------------
    colors = Color.objects.all()
    brands = Brand.objects.all()
    if category_id:
        if category_id[0] == '-':
            colors = colors.filter(stock__product__cat_id=category_id[1:]).distinct()
            brands = brands.filter(product__cat__id=category_id[1:]).distinct()
        elif not category_id == '0' and not category_id == "+":
            colors = colors.filter(stock__product__cat__category__id=category_id).distinct()
            brands = brands.filter(product__cat__category__id=category_id).distinct()
    context = {
        #for nase
        'categories': categories,
        'number_items_wish_list': number_items_wish_list,
        'number_items_compare': number_items_compare,
        'hot_categories': hot_categories[:4],
        'tags': tags,
        'cart': cart_result,
        'total_price_in_cart': total_price_in_cart,
        'number_products_in_cart': number_products_in_cart,

        'results': list_products,
        'colors': colors,
        'brands': brands,

        'category': category,
        'type_search': type_search,
        'word': word,
        'selected_colors': list(map(int, colors_id)),
        'selected_brands': list(map(int, brands_id)),
        'filter_by_price': filter_by_price,
        'is_filtered': is_filtered,
        'max_value': max_value,
        'min_value': min_value,
        'page_range': page_range,
        'sort_by': sort_by,
        'number_elements': number_elements,
    }
    return render(request, 'ecommerce/search.html', context)


def products(request, type_search="all", id_search="0"):
    user = request.user
    #---------------- Featured brands
    brands = Brand.objects.exclude(image='').values('id').annotate(number=Count('product__id')).order_by('number')
    for el in brands:
        brand = Brand.objects.get(pk=el['id'])
        el['id'] = brand

    #---------------- number items in wishlist
    if user.is_authenticated:
        number_items_wish_list = WishList.objects.filter(user__user=user).count()
    else:
        number_items_wish_list = 0

    #---------------- number items in compare
    if user.is_authenticated:
        number_items_compare = Compare.objects.filter(user__user=user).count()
    else:
        number_items_compare = 0

    # --------------- All Categories ---------------
    categories = all_categories()

    # --------------- Hot Categories ---------------
    hot_categories = my_featured_sale()['hot_categories']

    # --------------- All Tags ---------------
    tags = all_tags()

    # --------------- Cart ---------------
    my_cart_result = my_cart(user)
    number_products_in_cart = my_cart_result['number_products_in_cart']
    total_price_in_cart = my_cart_result['total_price_in_cart']
    cart_result = my_cart_result['cart']

    #Initialisation
    list_products = None
    products_results = Product.objects.filter(id__lte=-1)
    page_range = []
    found = True
    page = request.POST.get('page', 1)
    number_elements = request.POST.get('number_elements', 15)
    sort_by = request.POST.get("sort_by", "1")

    message = "Shop by"
    name = "All"
    if type_search == "all":
        products_results = Product.objects.all()
    elif type_search == "tag":
        tags_s = Tag.objects.filter(pk=id_search)
        if tags_s.exists():
            products_results = Product.objects.filter(tags__id__exact=id_search)
            message = "shop by : {}".format(tags_s[0].name)
            name = tags_s[0].name
        else:
            found = False
    elif type_search == "brand":
        brands_s = Brand.objects.filter(pk=id_search)
        if brands_s.exists():
            products_results = Product.objects.filter(brand_id__exact=id_search)
            message = "shop by : {}".format(brands_s[0].name)
            name = brands_s[0].name
        else:
            found = False
    elif type_search == "sub_category":
        sub_categories_s = CommerceSCategory.objects.filter(pk=id_search)
        if sub_categories_s.exists():
            products_results = Product.objects.filter(cat_id__exact=id_search)
            message = "shop by : {}".format(sub_categories_s[0].name)
            name = sub_categories_s[0]
        else:
            found = False
    elif type_search == "category":
        categories_s = CommerceCategory.objects.filter(pk=id_search)
        if categories_s.exists():
            products_results = Product.objects.filter(cat__category_id__exact=id_search)
            message = "shop by : {}".format(categories_s[0].name)
            name = categories_s[0].name
        else:
            found = False
    else:
        found = False

    if sort_by == "2":
        products_results = products_results.order_by(Lower("name"))
    elif sort_by == "3":
        products_results = products_results.order_by(Lower('name')).reverse()
    elif sort_by == "4":
        products_results = products_results.order_by('price')
    elif sort_by == "5":
        products_results = products_results.order_by('-price')
    elif sort_by == "8":
        products_results = products_results.order_by(Lower('brand__name'))
    elif sort_by == "9":
        products_results = products_results.order_by(Lower('brand__name')).reverse()
    elif sort_by == "10":
        products_results = products_results.order_by('-date_add')
    elif sort_by == "11":
        products_results = products_results.order_by('date_add')
    if products_results.exists():
        # select id, Avg(value) from product inner join commerce_ratting
        products_results = products_results.values('id').annotate(ratting=Avg('commerceratting__value'))
        if sort_by == "6":
            products_results = products_results.order_by('-ratting')
        if sort_by == "7":
            products_results = products_results.order_by('ratting')

        for el in products_results:
            product = Product.objects.get(pk=el['id'])
            el['id'] = product

            if el['ratting']:
                el['rattingInt'] = int(el['ratting'])
            else:
                el['rattingInt'] = 0
                el['ratting'] = 0

            if (timezone.localtime(timezone.now()).date() - product.date_add).days < 30:
                el['new'] = True
            else:
                el['new'] = False

            sale = product.sale_set.filter(date_end__gte=timezone.now()).order_by('date_end')
            if sale.exists():
                el['sale'] = sale[0]
            else:
                el['sale'] = None

            if product.stock_set.exists():
                el['quantity'] = product.stock_set.aggregate(quantity=Sum('quantity'))["quantity"]
                el['first_quantity'] = product.stock_set.aggregate(quantity=Sum('first_quantity'))["quantity"]
            else:
                el['quantity'] = 0
                el['first_quantity'] = 0

            images = CommerceImage.objects.filter(product=product)
            if images.exists():
                el['image'] = images[0].image
            else:
                el['image'] = None

            el['sold'] = el['first_quantity'] - el['quantity']

        paginator = Paginator(products_results, number_elements)
        try:
            list_products = paginator.page(page)
        except PageNotAnInteger:
            list_products = paginator.page(1)
        except EmptyPage:
            list_products = paginator.page(paginator.num_pages)

        # range for display just 11 numbers
        index_page = list_products.number - 1
        max_index = len(paginator.page_range)
        start_index = index_page - 5 if index_page >= 4 else 0
        end_index = index_page + 5 if index_page <= max_index - 4 else max_index
        page_range = list(paginator.page_range)[start_index:end_index]
    if found is False:
        message = "Sorry we didn't found this '{}'".format(type_search)
        list_products = None
    context = {
        #for nase
        'categories': categories,
        'number_items_wish_list': number_items_wish_list,
        'number_items_compare': number_items_compare,
        'hot_categories': hot_categories[:4],
        'tags': tags,
        'cart': cart_result,
        'total_price_in_cart': total_price_in_cart,
        'number_products_in_cart': number_products_in_cart,

        'results': list_products,
        'brands': brands,
        'type_search': type_search,
        'id_search': id_search,
        'message': message,
        'name': name,

        'page_range': page_range,
        'sort_by': sort_by,
        'number_elements': number_elements,
    }
    return render(request, 'ecommerce/products.html', context)


def display_product(request, id_product="0"):
    user = request.user

    # ---------------- number items in wishlist
    if user.is_authenticated:
        number_items_wish_list = WishList.objects.filter(user__user=user).count()
    else:
        number_items_wish_list = 0

    #---------------- number items in compare
    if user.is_authenticated:
        number_items_compare = Compare.objects.filter(user__user=user).count()
    else:
        number_items_compare = 0

    # --------------- All Categories ---------------
    categories = all_categories()

    # --------------- Hot Categories ---------------
    hot_categories = my_featured_sale()['hot_categories']

    # --------------- All Tags ---------------
    tags = all_tags()

    # --------------- Cart ---------------
    my_cart_result = my_cart(user)
    number_products_in_cart = my_cart_result['number_products_in_cart']
    total_price_in_cart = my_cart_result['total_price_in_cart']
    cart_result = my_cart_result['cart']

    #--------------------------- Product ---------------------------------
    if not Product.objects.filter(pk=id_product).exists():
        return HttpResponseRedirect('/e_commerce')
    product = Product.objects.get(pk=id_product)
    product.number_views += 1
    product.save()
    #----------- Ratting
    ratting = Product.objects.filter(pk=id_product).aggregate(ratting=Avg('commerceratting__value'))['ratting']
    if ratting:
        ratting_int = int(ratting)
    else:
        ratting_int = 0
    # ----------- Sale
    sale = product.sale_set.filter(date_end__gte=timezone.now()).order_by('date_end')
    if sale.exists():
        sale = sale[0]
    else:
        sale = None
    if (timezone.localtime(timezone.now()).date() - product.date_add).days < 30:
        new = True
    else:
        new = False
    # ----------- Quantity
    quantity = product.stock_set.aggregate(Sum('quantity'))["quantity__sum"]
    if not quantity:
        quantity = 0
    first_quantity = product.stock_set.aggregate(Sum('first_quantity'))["first_quantity__sum"]
    if not first_quantity:
        first_quantity = 0
    if first_quantity == 0:
        percent = 0
    else:
        percent = (quantity * 100) / first_quantity
    sold = first_quantity - quantity
    # ----------- Accessories
    accessories = product.accessories.all()
    accessories = accessories.values('id').annotate(ratting=Avg('commerceratting__value'))
    for el in accessories:
        p = Product.objects.get(pk=el['id'])
        el['id'] = p

        if el['ratting']:
            el['rattingInt'] = int(el['ratting'])
        else:
            el['rattingInt'] = 0
            el['ratting'] = 0

        if (timezone.localtime(timezone.now()).date() - p.date_add).days < 15:
            el['new'] = True
        else:
            el['new'] = False

        sale_acc = p.sale_set.filter(date_end__gte=timezone.now()).order_by('date_end')
        if sale_acc.exists():
            el['sale'] = sale_acc[0]
        else:
            el['sale'] = None

        images = CommerceImage.objects.filter(product=p)
        if images.exists():
            el['image'] = images[0].image
        else:
            el['image'] = None

    # ----------- Latest products
    latest_products = Product.objects.all().order_by('-date_add')[:15]
    latest_products = latest_products.values('id').annotate(ratting=Avg('commerceratting__value'))
    for el in latest_products:
        p = Product.objects.get(pk=el['id'])
        el['id'] = p

        if el['ratting']:
            el['rattingInt'] = int(el['ratting'])
        else:
            el['rattingInt'] = 0
            el['ratting'] = 0

        sale_l = p.sale_set.filter(date_end__gte=timezone.now()).order_by('date_end')
        if sale_l.exists():
            el['sale'] = sale_l[0]
        else:
            el['sale'] = None
    print(latest_products)
    context = {
        # for base.html
        'categories': categories,
        'number_items_wish_list': number_items_wish_list,
        'number_items_compare': number_items_compare,
        'hot_categories': hot_categories[:4],
        'tags': tags,
        'cart': cart_result,
        'total_price_in_cart': total_price_in_cart,
        'number_products_in_cart': number_products_in_cart,

        'product': product,
        'ratting': ratting,
        'rattingInt': ratting_int,
        'sale': sale,
        'new': new,
        'quantity': quantity,
        'sold': sold,
        'percent': percent,
        'tags_p': Tag.objects.filter(product=product),
        'accessories': accessories,
        'latest_products': latest_products
    }

    return render(request, 'ecommerce/product.html', context)


def quick_view(request, id_product="0"):

    #--------------------------- Product ---------------------------------
    if not Product.objects.filter(pk=id_product).exists():
        return HttpResponseRedirect('/e_commerce')
    product = Product.objects.get(pk=id_product)
    product.number_views += 1
    product.save()
    #----------- Ratting
    ratting = Product.objects.filter(pk=id_product).aggregate(ratting=Avg('commerceratting__value'))['ratting']
    if ratting:
        ratting_int = int(ratting)
    else:
        ratting_int = 0
    # ----------- Sale
    sale = product.sale_set.filter(date_end__gte=timezone.now()).order_by('date_end')
    if sale.exists():
        sale = sale[0]
    else:
        sale = None
    if (timezone.localtime(timezone.now()).date() - product.date_add).days < 15:
        new = True
    else:
        new = False
    # ----------- Quantity
    quantity = product.stock_set.aggregate(Sum('quantity'))["quantity__sum"]
    if not quantity:
        quantity = 0
    first_quantity = product.stock_set.aggregate(Sum('first_quantity'))["first_quantity__sum"]
    if not first_quantity:
        first_quantity = 0
    if first_quantity == 0:
        percent = 0
    else:
        percent = (quantity * 100) / first_quantity
    sold = first_quantity - quantity

    context = {
        'product': product,
        'ratting': ratting,
        'rattingInt': ratting_int,
        'sale': sale,
        'new': new,
        'quantity': quantity,
        'sold': sold,
        'percent': percent,
        'tags_p': Tag.objects.filter(product=product),
    }

    return render(request, 'ecommerce/quickview.html', context)


def wish_list(request):
    user = request.user

    # ---------------- number items in wishlist
    if user.is_authenticated:
        number_items_wish_list = WishList.objects.filter(user__user=user).count()
    else:
        number_items_wish_list = 0

    #---------------- number items in compare
    if user.is_authenticated:
        number_items_compare = Compare.objects.filter(user__user=user).count()
    else:
        number_items_compare = 0

    # --------------- All Categories ---------------
    categories = all_categories()

    # --------------- Hot Categories ---------------
    hot_categories = my_featured_sale()['hot_categories']

    # --------------- All Tags ---------------
    tags = all_tags()

    # --------------- Cart ---------------
    my_cart_result = my_cart(user)
    number_products_in_cart = my_cart_result['number_products_in_cart']
    total_price_in_cart = my_cart_result['total_price_in_cart']
    cart_result = my_cart_result['cart']

    #-------------- Wish List
    if user.is_authenticated:
        wish_list_list = list()
        wish_list_result = WishList.objects.filter(user=user.profil)
        for el in wish_list_result:
            ob = dict()
            ob['el'] = el

            sale = el.product.sale_set.filter(date_end__gte=datetime.date.today())
            if sale.exists():
                ob['sale'] = sale[0]
            else:
                ob['sale'] = None

            if el.product.stock_set.exists():
                stock = el.product.stock_set.aggregate(quantity=Sum('quantity'))['quantity']
                if stock > 0:
                    ob['stock'] = 'In Stock'
                else:
                    ob['stock'] = "Out of Stock"
            else:
                ob['stock'] = 'Pre-Order'

            wish_list_list.append(ob)
            del ob
    else:
        return HttpResponseRedirect('/e_commerce')
    context = {
        # for base.html
        'categories': categories,
        'number_items_wish_list': number_items_wish_list,
        'number_items_compare': number_items_compare,
        'hot_categories': hot_categories[:4],
        'tags': tags,
        'cart': cart_result,
        'total_price_in_cart': total_price_in_cart,
        'number_products_in_cart': number_products_in_cart,

        'wish_list_list': wish_list_list
    }
    return render(request, 'ecommerce/wish_list.html', context)


def compare(request):
    user = request.user

    # ---------------- number items in wishlist
    if user.is_authenticated:
        number_items_wish_list = WishList.objects.filter(user__user=user).count()
    else:
        number_items_wish_list = 0

    #---------------- number items in compare
    if user.is_authenticated:
        number_items_compare = Compare.objects.filter(user__user=user).count()
    else:
        number_items_compare = 0

    # --------------- All Categories ---------------
    categories = all_categories()

    # --------------- Hot Categories ---------------
    hot_categories = my_featured_sale()['hot_categories']

    # --------------- All Tags ---------------
    tags = all_tags()

    # --------------- Cart ---------------
    my_cart_result = my_cart(user)
    number_products_in_cart = my_cart_result['number_products_in_cart']
    total_price_in_cart = my_cart_result['total_price_in_cart']
    cart_result = my_cart_result['cart']

    #-------------- Compare
    if user.is_authenticated:
        compare_list = list()
        compare_list_result = Compare.objects.filter(user=user.profil)[:4]
        for el in compare_list_result:
            ob = dict()
            ob['el'] = el

            sale = el.product.sale_set.filter(date_end__gte=datetime.date.today())
            if sale.exists():
                ob['sale'] = sale[0]
            else:
                ob['sale'] = None

            if el.product.stock_set.exists():
                stock = el.product.stock_set.aggregate(quantity=Sum('quantity'))['quantity']
                if stock > 0:
                    ob['stock'] = 'In Stock'
                else:
                    ob['stock'] = "Out of Stock"
            else:
                ob['stock'] = 'Pre-Order'

            if el.product.commerceratting_set.exists():
                ratting = el.product.commerceratting_set.aggregate(ratting=Avg('value'))['ratting']
                if ratting:
                    ob['ratting'] = ratting
                    ob['rattingInt'] = int(ratting)
                else:
                    ob['ratting'] = 0
                    ob['rattingInt'] = 0
            else:
                ob['ratting'] = 0
                ob['rattingInt'] = 0

            compare_list.append(ob)
            del ob
    else:
        return HttpResponseRedirect('/e_commerce')
    count_span = 1
    if compare_list:
        count_span = len(compare_list) + 1
    context = {
        # for base.html
        'categories': categories,
        'number_items_wish_list': number_items_wish_list,
        'number_items_compare': number_items_compare,
        'hot_categories': hot_categories[:4],
        'tags': tags,
        'cart': cart_result,
        'total_price_in_cart': total_price_in_cart,
        'number_products_in_cart': number_products_in_cart,

        'compare_list': compare_list,
        'count_span': count_span
    }
    return render(request, 'ecommerce/compare.html', context)


def cart(request):
    user = request.user

    # ---------------- number items in wishlist
    if user.is_authenticated:
        number_items_wish_list = WishList.objects.filter(user__user=user).count()
    else:
        number_items_wish_list = 0

    #---------------- number items in compare
    if user.is_authenticated:
        number_items_compare = Compare.objects.filter(user__user=user).count()
    else:
        number_items_compare = 0

    # --------------- All Categories ---------------
    categories = all_categories()

    # --------------- Hot Categories ---------------
    hot_categories = my_featured_sale()['hot_categories']

    # --------------- All Tags ---------------
    tags = all_tags()

    # --------------- Cart ---------------
    my_cart_result = my_cart(user)
    number_products_in_cart = my_cart_result['number_products_in_cart']
    total_price_in_cart = my_cart_result['total_price_in_cart']
    cart_result = my_cart_result['cart']

    context = {
        # for base.html
        'categories': categories,
        'number_items_wish_list': number_items_wish_list,
        'number_items_compare': number_items_compare,
        'hot_categories': hot_categories[:4],
        'tags': tags,
        'cart': cart_result,
        'total_price_in_cart': total_price_in_cart,
        'number_products_in_cart': number_products_in_cart,
    }
    return render(request, 'ecommerce/cart.html', context)


def my_account(request):
    user = request.user

    #---------------- number items in wishlist
    if user.is_authenticated:
        number_items_wish_list = WishList.objects.filter(user__user=user).count()
    else:
        number_items_wish_list = 0

    #---------------- number items in compare
    if user.is_authenticated:
        number_items_compare = Compare.objects.filter(user__user=user).count()
    else:
        number_items_compare = 0

    #request.user
    if user.is_authenticated:
        # --------------- All Categories ---------------
        categories = all_categories()

        # --------------- Hot Categories ---------------
        hot_categories = my_featured_sale()['hot_categories']

        # --------------- All Tags ---------------
        tags = all_tags()

        # --------------- Cart ---------------
        my_cart_result = my_cart(user)
        number_products_in_cart = my_cart_result['number_products_in_cart']
        total_price_in_cart = my_cart_result['total_price_in_cart']
        cart_result = my_cart_result['cart']

        #----------------initialisation
        message_error = message_success = None
        newsletter_on = False
        mailing_object = None

        #---------------- newsletter
        mailing = Mailing.objects.filter(email=user.email)
        if mailing.exists():
            mailing_object = mailing[0]
            if mailing_object.active:
                newsletter_on = True

        if request.method == "POST":
            #---------------- get data
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            if old_password and new_password and confirm_password:
                if old_password == user.password:
                    if new_password == confirm_password:
                        user.password = new_password
                    else:
                        message_error = "Confirmation wrong"
                else:
                    message_error = "Password wrong"
            elif old_password or new_password or confirm_password:
                message_error = "You must fill all the fields to change password if you want to change your password! Or leave the fields empty to change the others informations"
            if not message_error:
                first_name = request.POST.get('first_name')
                if first_name:
                    user.first_name = str(first_name).capitalize()
                else:
                    user.first_name = ""

                last_name = request.POST.get('last_name')
                if last_name:
                    user.last_name = str(last_name).upper()
                else:
                    user.last_name = ""

                email = request.POST.get('email')
                if email:
                    if user.email != email:
                        if mailing_object:
                            mailing_object.delete()
                            Mailing.objects.get_or_create(email=email, active=False)
                            mailing_object = Mailing.objects.get(email=email)
                    user.email = email
                else:
                    user.email = ""
                    if mailing_object:
                        mailing_object.delete()
                        mailing_object = None
                telephone = request.POST.get('telephone')
                if telephone:
                    user.profil.tel = telephone
                    user.profil.save()
                else:
                    user.profil.tel = ""
                    user.profil.save()

                newsletter = request.POST.get('newsletter')
                if newsletter == "1":
                    if mailing_object:
                        mailing_object.active = True
                        mailing_object.save()
                    else:
                        Mailing.objects.create(email=email, active=True)
                    newsletter_on = True
                else:
                    if mailing_object:
                        mailing_object.active = False
                        mailing_object.save()
                    newsletter_on = False

                #Billing Address
                p_address = request.POST.get('P_address')
                p_company = request.POST.get('P_company')
                p_city = request.POST.get('P_city')
                p_postcode = request.POST.get('P_postcode')
                p_country = request.POST.get('P_country')
                p_region = request.POST.get('P_region')
                if BillingAddress.objects.filter(user=user.profil).exists():
                    user.profil.billingaddress.address = p_address
                    user.profil.billingaddress.city = p_city
                    user.profil.billingaddress.post_code = p_postcode
                    user.profil.billingaddress.country = p_country
                    user.profil.billingaddress.region = p_region
                else:
                    BillingAddress.objects.create(address=p_address, city=p_city, post_code=p_postcode, country=p_country, region=p_region, user=user.profil)

                if p_company:
                    user.profil.billingaddress.company = p_company
                else:
                    user.profil.billingaddress.company = ""

                #Shipping Address
                s_company = request.POST.get('S_company')
                s_address = request.POST.get('S_address')
                s_city = request.POST.get('S_city')
                s_postcode = request.POST.get('S_postcode')
                s_country = request.POST.get('S_country')
                s_region = request.POST.get('S_region')
                if ShippingAddress.objects.filter(user=user.profil).exists():
                    user.profil.shippingaddress.address = s_address
                    user.profil.shippingaddress.city = s_city
                    user.profil.shippingaddress.post_code = s_postcode
                    user.profil.shippingaddress.country = s_country
                    user.profil.shippingaddress.region = s_region
                else:
                    ShippingAddress.objects.create(address=s_address, city=s_city, post_code=s_postcode, country=s_country, region=s_region, user=user.profil)

                if s_company:
                    user.profil.shippingaddress.company = s_company
                else:
                    user.profil.shippingaddress.company = ""

                user.profil.shippingaddress.save()
                user.profil.billingaddress.save()
                user.profil.save()
                user.save()
                message_success = "Your account is up to date"

        context = {
            #for base.html
            'categories': categories,
            'number_items_wish_list': number_items_wish_list,
            'number_items_compare': number_items_compare,
            'hot_categories': hot_categories[:4],
            'tags': tags,
            'cart': cart_result,
            'total_price_in_cart': total_price_in_cart,
            'number_products_in_cart': number_products_in_cart,

            'newsletter_on': newsletter_on,
            'message_error': message_error,
            'message_success': message_success,
            'user': user
        }
        return render(request, 'ecommerce/my-account.html', context)


def contact_us(request):
    user = request.user

    # ---------------- number items in wishlist
    if user.is_authenticated:
        number_items_wish_list = WishList.objects.filter(user__user=user).count()
    else:
        number_items_wish_list = 0

    #---------------- number items in compare
    if user.is_authenticated:
        number_items_compare = Compare.objects.filter(user__user=user).count()
    else:
        number_items_compare = 0

    # --------------- All Categories ---------------
    categories = all_categories()

    # --------------- Hot Categories ---------------
    hot_categories = my_featured_sale()['hot_categories']

    # --------------- All Tags ---------------
    tags = all_tags()

    # --------------- Cart ---------------
    my_cart_result = my_cart(user)
    number_products_in_cart = my_cart_result['number_products_in_cart']
    total_price_in_cart = my_cart_result['total_price_in_cart']
    cart_result = my_cart_result['cart']

    #---------------- message
    message_success = None
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")
        Message.objects.create(name=name, email=email, message=message)
        message_success = "Your message has been sent"

    context = {
        # for base.html
        'categories': categories,
        'number_items_wish_list': number_items_wish_list,
        'number_items_compare': number_items_compare,
        'hot_categories': hot_categories[:4],
        'tags': tags,
        'cart': cart_result,
        'total_price_in_cart': total_price_in_cart,
        'number_products_in_cart': number_products_in_cart,

        'message_success': message_success,
    }
    return render(request, 'ecommerce/contact-us.html', context)


def faq(request):
    user = request.user

    # ---------------- number items in wishlist
    if user.is_authenticated:
        number_items_wish_list = WishList.objects.filter(user__user=user).count()
    else:
        number_items_wish_list = 0

    #---------------- number items in compare
    if user.is_authenticated:
        number_items_compare = Compare.objects.filter(user__user=user).count()
    else:
        number_items_compare = 0

    # --------------- All Categories ---------------
    categories = all_categories()

    # --------------- Hot Categories ---------------
    hot_categories = my_featured_sale()['hot_categories']

    # --------------- All Tags ---------------
    tags = all_tags()

    # --------------- Cart ---------------
    my_cart_result = my_cart(user)
    number_products_in_cart = my_cart_result['number_products_in_cart']
    total_price_in_cart = my_cart_result['total_price_in_cart']
    cart_result = my_cart_result['cart']

    context = {
        # for base.html
        'categories': categories,
        'number_items_wish_list': number_items_wish_list,
        'number_items_compare': number_items_compare,
        'hot_categories': hot_categories[:4],
        'tags': tags,
        'cart': cart_result,
        'total_price_in_cart': total_price_in_cart,
        'number_products_in_cart': number_products_in_cart,
    }
    return render(request, 'ecommerce/faq.html', context)


def sitemap(request):
    user = request.user

    # ---------------- number items in wishlist
    if user.is_authenticated:
        number_items_wish_list = WishList.objects.filter(user__user=user).count()
    else:
        number_items_wish_list = 0

    #---------------- number items in compare
    if user.is_authenticated:
        number_items_compare = Compare.objects.filter(user__user=user).count()
    else:
        number_items_compare = 0

    # --------------- All Categories ---------------
    categories = all_categories()

    # --------------- Hot Categories ---------------
    hot_categories = my_featured_sale()['hot_categories']

    # --------------- All Tags ---------------
    tags = all_tags()

    # --------------- Cart ---------------
    my_cart_result = my_cart(user)
    number_products_in_cart = my_cart_result['number_products_in_cart']
    total_price_in_cart = my_cart_result['total_price_in_cart']
    cart_result = my_cart_result['cart']

    context = {
        # for base.html
        'categories': categories,
        'number_items_wish_list': number_items_wish_list,
        'number_items_compare': number_items_compare,
        'hot_categories': hot_categories[:4],
        'tags': tags,
        'cart': cart_result,
        'total_price_in_cart': total_price_in_cart,
        'number_products_in_cart': number_products_in_cart,
        'brands': Brand.objects.all()
    }
    return render(request, 'ecommerce/sitemap.html', context)


def about_us(request):
    user = request.user

    # ---------------- number items in wishlist
    if user.is_authenticated:
        number_items_wish_list = WishList.objects.filter(user__user=user).count()
    else:
        number_items_wish_list = 0

    #---------------- number items in compare
    if user.is_authenticated:
        number_items_compare = Compare.objects.filter(user__user=user).count()
    else:
        number_items_compare = 0

    # --------------- All Categories ---------------
    categories = all_categories()

    # --------------- Hot Categories ---------------
    hot_categories = my_featured_sale()['hot_categories']

    # --------------- All Tags ---------------
    tags = all_tags()

    # --------------- Cart ---------------
    my_cart_result = my_cart(user)
    number_products_in_cart = my_cart_result['number_products_in_cart']
    total_price_in_cart = my_cart_result['total_price_in_cart']
    cart_result = my_cart_result['cart']

    context = {
        # for base.html
        'categories': categories,
        'number_items_wish_list': number_items_wish_list,
        'number_items_compare': number_items_compare,
        'hot_categories': hot_categories[:4],
        'tags': tags,
        'cart': cart_result,
        'total_price_in_cart': total_price_in_cart,
        'number_products_in_cart': number_products_in_cart,
    }
    return render(request, 'ecommerce/about-us.html', context)


def checkout(request):
    user = request.user
    if not ShippingAddress.objects.filter(user=user.profil).exists() or not BillingAddress.objects.filter( user=user.profil).exists():
        return HttpResponseRedirect('e_commerce/my-account')
    elif request.method == 'POST':
        comment = request.POST.get('comment', '')
        method_shipping = request.POST.get('shipping_method', 'Free Shipping')
        method_payment = request.POST.get('payment_method', 'Cas On Delivery')
        order = Order(user=user.profil,payment_method=method_payment, delivery_method=method_shipping, comment=comment, amount=0)
        order.save()
        total_price_in_cart = 0
        cart_result = Cart.objects.filter(user=user.profil)
        for el in cart_result:
            stock = el.product.stock_set.filter(color=el.color)
            if stock.exists():
                el.product.price = el.product.price + stock.all()[0].price_sup
            sale = el.product.sale_set.filter(date_end__gte=datetime.date.today())
            if sale.exists():
                el.product.price = el.product.price - ((el.product.price * sale.all()[0].percentage) / 100)
            total = el.product.price * el.quantity
            order_line = OrderLine(quantity=el.quantity, total=total, order=order, product=Product.objects.get(pk=el.product.pk), color=el.color)
            order_line.save()
            total_price_in_cart += total
        #--- Order
        if method_shipping == "Flat Shipping Rate":
            order.amount = (total_price_in_cart + 50)
        else:
            order.amount = total_price_in_cart
        order.save()
        #Cart.objects.filter(user=user.profil).delete()
        return HttpResponse("your order was checked out ! order {} amout : {}".format(order.pk, order.amount))
    elif not user.is_authenticated:
        return HttpResponseRedirect('/e_commerce/')
    else:
        # ---------------- number items in wishlist
        number_items_wish_list = WishList.objects.filter(user__user=user).count()

        # ---------------- number items in compare
        number_items_compare = Compare.objects.filter(user__user=user).count()

        # --------------- All Categories ---------------
        categories = all_categories()

        # --------------- Hot Categories ---------------
        hot_categories = my_featured_sale()['hot_categories']

        # --------------- All Tags ---------------
        tags = all_tags()

        # --------------- Cart ---------------
        my_cart_result = my_cart(user)
        number_products_in_cart = my_cart_result['number_products_in_cart']
        total_price_in_cart = my_cart_result['total_price_in_cart']
        cart_result = my_cart_result['cart']

        #---------------- checkout
        context = {
            # for base.html
            'categories': categories,
            'number_items_wish_list': number_items_wish_list,
            'number_items_compare': number_items_compare,
            'hot_categories': hot_categories[:4],
            'tags': tags,
            'cart': cart_result,
            'total_price_in_cart': total_price_in_cart,
            'number_products_in_cart': number_products_in_cart,
        }
        return render(request, 'ecommerce/checkout.html', context)


#----------------- functions add remove update
def add_to_wish(request):
    product_id = request.GET.get('product', "None")
    message_error = ""
    number_products_in_wish_list = ""
    if request.user.is_authenticated:
        if product_id != "None":
            user = request.user
            products_wish = Product.objects.filter(pk=product_id)
            if products_wish.exists():
                if not WishList.objects.filter(user=user.profil, product=products_wish[0]).exists():
                    WishList.objects.create(user=user.profil, product=products_wish[0])
                    wish_list_result = WishList.objects.filter(user=user.profil)
                    number_products_in_wish_list = wish_list_result.count()
                else:
                    message_error = "Product exists already in your wish list"
            else:
                message_error = "Product doesn't exist"
        else:
            message_error = "Error"
    else:
        message_error = "You should log in!"
    data = {
        'message_error': message_error,
        'number_products_in_wish_list': number_products_in_wish_list
    }
    return JsonResponse(data)


def add_to_compare(request):
    product_id = request.GET.get('product', "None")
    message_error = ""
    number_products_in_compare = ""
    print('1')
    if request.user.is_authenticated:
        print('2')
        if product_id != "None":
            print('3')
            user = request.user
            products_compare = Product.objects.filter(pk=product_id)
            if products_compare.exists():
                print('4')
                if not Compare.objects.filter(user=user.profil, product=products_compare[0]).exists():
                    print('5')
                    Compare.objects.create(user=user.profil, product=products_compare[0])
                    compare_result = Compare.objects.filter(user=user.profil)
                    number_products_in_compare = compare_result.count()
                else:
                    message_error = "Product exists already in your Compare list"
            else:
                message_error = "Product doesn't exist"
        else:
            message_error = "Error"
    else:
        message_error = "You should log in!"
    data = {
        'message_error': message_error,
        'number_products_in_compare': number_products_in_compare
    }
    return JsonResponse(data)


def add_to_cart(request):
    product_id = request.GET.get('product', "None")
    message_error = ""
    color_id = request.GET.get('option[231]', "None")
    quantity = request.GET.get('quantity', 1)
    price = total_price_in_cart = number_products_in_cart = ""
    if request.user.is_authenticated:
        if product_id != "None":
            user = request.user
            products_wish = Product.objects.filter(pk=product_id)
            if products_wish.exists():
                if color_id == "None" or color_id == "0":
                    stock = Stock.objects.filter(product=products_wish[0])
                else:
                    stock = Stock.objects.filter(product=products_wish[0], color_id=color_id)
                if stock.exists():
                    cart_objects = Cart.objects.filter(user=user.profil, product=products_wish[0], color=stock[0].color)
                    if not cart_objects.exists():
                        Cart.objects.create(user=user.profil, product=products_wish[0], color=stock[0].color, quantity=quantity)
                        color_id = stock[0].color.pk
                        cart_result = Cart.objects.filter(user=user.profil)
                        number_products_in_cart = cart_result.count()
                        total_price_in_cart = 0
                        for el in cart_result:
                            stock = el.product.stock_set.filter(color=el.color)
                            if stock.exists():
                                el.product.price = el.product.price + stock.all()[0].price_sup
                            sale = el.product.sale_set.filter(date_end__gte=datetime.date.today())
                            if sale.exists():
                                el.product.price = el.product.price - (
                                            (el.product.price * sale.all()[0].percentage) / 100)
                            if el.product == products_wish[0]:
                                price = Decimal(el.product.price) * Decimal(quantity)
                            total_price_in_cart += (el.product.price * el.quantity)
                            print('price : {} ' .format(price))
                    else:
                        message_error = "Product exists already in your cart"
                else:
                    message_error = "Product out of stock"
            else:
                message_error = "Product doesn't exist"
    else:
        message_error = "You should log in!"
    data = {
        'message_error': message_error,
        'total_price_in_cart': total_price_in_cart,
        'number_products_in_cart': number_products_in_cart,
        'price': price,
        'color_id': color_id,
        'quantity': quantity
    }
    return JsonResponse(data)


def remove_from_page_cart(request):
    if request.method == "POST":
        message_error = None
        user = request.user
        id_cart = request.POST.get('cart')
        cart_object = Cart.objects.filter(pk=id_cart)
        if cart_object.exists():
            cart_object = cart_object[0]
            cart_object.delete()
        else:
            message_error = "Product doesn't exist in your cart"
        if message_error:
            # ---------------- number items in wishlist
            if user.is_authenticated:
                number_items_wish_list = WishList.objects.filter(user__user=user).count()
            else:
                number_items_wish_list = 0

            # ---------------- number items in compare
            if user.is_authenticated:
                number_items_compare = Compare.objects.filter(user__user=user).count()
            else:
                number_items_compare = 0

            # --------------- All Categories ---------------
            categories = all_categories()

            # --------------- Hot Categories ---------------
            hot_categories = my_featured_sale()['hot_categories']

            # --------------- All Tags ---------------
            tags = all_tags()

            # --------------- Cart ---------------
            my_cart_result = my_cart(user)
            number_products_in_cart = my_cart_result['number_products_in_cart']
            total_price_in_cart = my_cart_result['total_price_in_cart']
            cart_result = my_cart_result['cart']

            context = {
                # for base.html
                'categories': categories,
                'number_items_wish_list': number_items_wish_list,
                'number_items_compare': number_items_compare,
                'hot_categories': hot_categories[:4],
                'tags': tags,
                'cart': cart_result,
                'total_price_in_cart': total_price_in_cart,
                'number_products_in_cart': number_products_in_cart,

                'message_error': message_error
            }
            return render(request, 'ecommerce/cart.html', context)

    next_page = request.POST.get('next', '/')
    return HttpResponseRedirect(next_page)


def remove_from_cart(request):
    message_error = ""
    total_price_in_cart = number_products_in_cart = ""
    user = request.user
    id_cart = request.GET.get('cart', "None")
    cart_object = Cart.objects.filter(pk=id_cart)
    if cart_object.exists():
        cart_object = cart_object[0]
        cart_object.delete()

        cart_result = Cart.objects.filter(user=user.profil)
        number_products_in_cart = cart_result.count()
        total_price_in_cart = 0
        for el in cart_result:
            stock = el.product.stock_set.filter(color=el.color)
            if stock.exists():
                el.product.price = el.product.price + stock.all()[0].price_sup
            sale = el.product.sale_set.filter(date_end__gte=datetime.date.today())
            if sale.exists():
                el.product.price = el.product.price - (
                        (el.product.price * sale.all()[0].percentage) / 100)
            total_price_in_cart += (el.product.price * el.quantity)
    else:
        message_error = "Product doesn't exist in your cart"
    data = {
        'message_error': message_error,
        'total_price_in_cart': total_price_in_cart,
        'number_products_in_cart': number_products_in_cart,
    }
    return JsonResponse(data)


def update_cart(request):
    if request.method == "POST":
        message_error = None
        user = request.user
        id_cart = request.POST.get('cart')
        cart_object = Color.objects.filter(pk=id_cart)
        if cart_object.exists():
            cart_object = cart_object[0]
            cart_object.quantity = request.POST.get('quantity', 1)
            cart_object.save()
        else:
            message_error = "Product doesn't exist in your cart"
        if message_error:
            # ---------------- number items in wishlist
            if user.is_authenticated:
                number_items_wish_list = WishList.objects.filter(user__user=user).count()
            else:
                number_items_wish_list = 0

            # ---------------- number items in compare
            if user.is_authenticated:
                number_items_compare = Compare.objects.filter(user__user=user).count()
            else:
                number_items_compare = 0

            # --------------- All Categories ---------------
            categories = all_categories()

            # --------------- Hot Categories ---------------
            hot_categories = my_featured_sale()['hot_categories']

            # --------------- All Tags ---------------
            tags = all_tags()

            # --------------- Cart ---------------
            my_cart_result = my_cart(user)
            number_products_in_cart = my_cart_result['number_products_in_cart']
            total_price_in_cart = my_cart_result['total_price_in_cart']
            cart_result = my_cart_result['cart']

            context = {
                # for base.html
                'categories': categories,
                'number_items_wish_list': number_items_wish_list,
                'number_items_compare': number_items_compare,
                'hot_categories': hot_categories[:4],
                'tags': tags,
                'cart': cart_result,
                'total_price_in_cart': total_price_in_cart,
                'number_products_in_cart': number_products_in_cart,

                'message_error': message_error
            }
            return render(request, 'ecommerce/cart.html', context)
    next_page = request.POST.get('next', '/')
    return HttpResponseRedirect(next_page)


def update_color_cart(request):
    if request.method == "POST":
        message_error = None
        user = request.user
        id_cart = request.POST.get('cart')
        id_color = request.POST.get('option[231]')
        cart_object = Cart.objects.filter(pk=id_cart)
        if cart_object.exists():
            cart_object = cart_object[0]
            cart_object.color = Color.objects.get(pk=id_color)
            cart_object.save()
        else:
            message_error = "Product doesn't exist"
        if message_error:
            # ---------------- number items in wishlist
            if user.is_authenticated:
                number_items_wish_list = WishList.objects.filter(user__user=user).count()
            else:
                number_items_wish_list = 0

            # ---------------- number items in compare
            if user.is_authenticated:
                number_items_compare = Compare.objects.filter(user__user=user).count()
            else:
                number_items_compare = 0

            # --------------- All Categories ---------------
            categories = all_categories()

            # --------------- Hot Categories ---------------
            hot_categories = my_featured_sale()['hot_categories']

            # --------------- All Tags ---------------
            tags = all_tags()

            # --------------- Cart ---------------
            my_cart_result = my_cart(user)
            number_products_in_cart = my_cart_result['number_products_in_cart']
            total_price_in_cart = my_cart_result['total_price_in_cart']
            cart_result = my_cart_result['cart']

            context = {
                # for base.html
                'categories': categories,
                'number_items_wish_list': number_items_wish_list,
                'number_items_compare': number_items_compare,
                'hot_categories': hot_categories[:4],
                'tags': tags,
                'cart': cart_result,
                'total_price_in_cart': total_price_in_cart,
                'number_products_in_cart': number_products_in_cart,

                'message_error': message_error
            }
            return render(request, 'ecommerce/cart.html', context)
    next_page = request.POST.get('next', '/')
    return HttpResponseRedirect(next_page)


def add_from_wish(request):
    if request.method == "POST":
        message_error = None
        user = request.user
        id_product = request.POST.get('product')
        products_wish = Product.objects.filter(pk=id_product)
        if products_wish.exists():
            wish_object = WishList.objects.filter(user=user.profil, product=products_wish[0])
            if wish_object.exists():
                stock = Stock.objects.filter(product=products_wish[0])
                if stock.exists():
                    if not Cart.objects.filter(user=user.profil, product=products_wish[0], color=stock[0].color).exists():
                        Cart.objects.create(user=user.profil, product=products_wish[0], color=stock[0].color)
                    else:
                        message_error = "Product exists already in your cart"
                else:
                    message_error = "Product out of stock"
            else:
                message_error = "Product doesn't exists in your wish list"
        else:
            message_error = "Product doesn't exist"
        if message_error:
            user = request.user

            # ---------------- number items in wishlist
            if user.is_authenticated:
                number_items_wish_list = WishList.objects.filter(user__user=user).count()
            else:
                number_items_wish_list = 0

            # ---------------- number items in compare
            if user.is_authenticated:
                number_items_compare = Compare.objects.filter(user__user=user).count()
            else:
                number_items_compare = 0

            # --------------- All Categories ---------------
            categories = all_categories()

            # --------------- Hot Categories ---------------
            hot_categories = my_featured_sale()['hot_categories']

            # --------------- All Tags ---------------
            tags = all_tags()

            # --------------- Cart ---------------
            my_cart_result = my_cart(user)
            number_products_in_cart = my_cart_result['number_products_in_cart']
            total_price_in_cart = my_cart_result['total_price_in_cart']
            cart_result = my_cart_result['cart']

            # -------------- Wish List
            if user.is_authenticated:
                wish_list_list = list()
                wish_list_result = WishList.objects.filter(user=user.profil)
                for el in wish_list_result:
                    ob = dict()
                    ob['el'] = el

                    sale = el.product.sale_set.filter(date_end__gte=datetime.date.today())
                    if sale.exists():
                        ob['sale'] = sale[0]
                    else:
                        ob['sale'] = None

                    if el.product.stock_set.exists():
                        stock = el.product.stock_set.aggregate(quantity=Sum('quantity'))['quantity']
                        if stock > 0:
                            ob['stock'] = 'In Stock'
                        else:
                            ob['stock'] = "Out of Stock"
                    else:
                        ob['stock'] = 'Pre-Order'

                    wish_list_list.append(ob)
                    del ob
            else:
                return HttpResponseRedirect('/e_commerce')
            context = {
                # for base.html
                'categories': categories,
                'number_items_wish_list': number_items_wish_list,
                'number_items_compare': number_items_compare,
                'hot_categories': hot_categories[:4],
                'tags': tags,
                'cart': cart_result,
                'total_price_in_cart': total_price_in_cart,
                'number_products_in_cart': number_products_in_cart,

                'wish_list_list': wish_list_list,
                'message_error': message_error
            }
            return render(request, 'ecommerce/wish_list.html', context)

    return HttpResponseRedirect('/e_commerce/wish_list')


def remove_from_wish(request):
    if request.method == "POST":
        user = request.user
        id_product = request.POST.get('product')
        products_wish = Product.objects.filter(pk=id_product)
        if products_wish.exists():
            wish_object = WishList.objects.filter(user=user.profil, product=products_wish[0])
            if wish_object.exists():
                wish_object = wish_object[0]
                wish_object.delete()
    return HttpResponseRedirect('/e_commerce/wish_list')


def add_from_compare(request):
    if request.method == "POST":
        message_error = None
        user = request.user
        id_product = request.POST.get('product')
        products_compare = Product.objects.filter(pk=id_product)
        if products_compare.exists():
            compare_object = Compare.objects.filter(user=user.profil, product=products_compare[0])
            if compare_object.exists():
                stock = Stock.objects.filter(product=products_compare[0])
                if stock.exists():
                    if not Cart.objects.filter(user=user.profil, product=products_compare[0], color=stock[0].color).exists():
                        Cart.objects.create(user=user.profil, product=products_compare[0], color=stock[0].color)
                    else:
                        message_error = "Product exists already in your cart"
                else:
                    message_error = "Product out of stock"
            else:
                message_error = "Product doesn't exists in your compare list"
        else:
            message_error = "Product doesn't exist"
        if message_error:
            user = request.user

            # ---------------- number items in wishlist
            if user.is_authenticated:
                number_items_wish_list = WishList.objects.filter(user__user=user).count()
            else:
                number_items_wish_list = 0

            # ---------------- number items in compare
            if user.is_authenticated:
                number_items_compare = Compare.objects.filter(user__user=user).count()
            else:
                number_items_compare = 0

            # --------------- All Categories ---------------
            categories = all_categories()

            # --------------- Hot Categories ---------------
            hot_categories = my_featured_sale()['hot_categories']

            # --------------- All Tags ---------------
            tags = all_tags()

            # --------------- Cart ---------------
            my_cart_result = my_cart(user)
            number_products_in_cart = my_cart_result['number_products_in_cart']
            total_price_in_cart = my_cart_result['total_price_in_cart']
            cart_result = my_cart_result['cart']

            # -------------- Compare
            if user.is_authenticated:
                compare_list = list()
                compare_list_result = Compare.objects.filter(user=user.profil)[:4]
                for el in compare_list_result:
                    ob = dict()
                    ob['el'] = el

                    sale = el.product.sale_set.filter(date_end__gte=datetime.date.today())
                    if sale.exists():
                        ob['sale'] = sale[0]
                    else:
                        ob['sale'] = None

                    if el.product.stock_set.exists():
                        stock = el.product.stock_set.aggregate(quantity=Sum('quantity'))['quantity']
                        if stock > 0:
                            ob['stock'] = 'In Stock'
                        else:
                            ob['stock'] = "Out of Stock"
                    else:
                        ob['stock'] = 'Pre-Order'

                    if el.product.commerceratting_set.exists():
                        ratting = el.product.commerceratting_set.aggregate(ratting=Avg('value'))['ratting']
                        if ratting:
                            ob['ratting'] = ratting
                            ob['rattingInt'] = int(ratting)
                        else:
                            ob['ratting'] = 0
                            ob['rattingInt'] = 0
                    else:
                        ob['ratting'] = 0
                        ob['rattingInt'] = 0

                    compare_list.append(ob)
                    del ob
            else:
                return HttpResponseRedirect('/e_commerce')
            count_span = 1
            if compare_list:
                count_span = len(compare_list) + 1
            context = {
                # for base.html
                'categories': categories,
                'number_items_wish_list': number_items_wish_list,
                'number_items_compare': number_items_compare,
                'hot_categories': hot_categories[:4],
                'tags': tags,
                'cart': cart_result,
                'total_price_in_cart': total_price_in_cart,
                'number_products_in_cart': number_products_in_cart,

                'compare_list': compare_list,
                'count_span': count_span,
                'message_error': message_error
            }
            return render(request, 'ecommerce/compare.html', context)

    return HttpResponseRedirect('/e_commerce/wish_list')


def remove_from_compare(request):
    if request.method == "POST":
        user = request.user
        id_product = request.POST.get('product')
        products_compare = Product.objects.filter(pk=id_product)
        if products_compare.exists():
            compare_object = Compare.objects.filter(user=user.profil, product=products_compare[0])
            if compare_object.exists():
                compare_object = compare_object[0]
                compare_object.delete()
    return HttpResponseRedirect('/e_commerce/compare')


#------------------- Methods
def all_categories():
    return CommerceCategory.objects.all()


def all_tags():
    return Tag.objects.all()


def my_cart(user):
    number_products_in_cart = 0
    total_price_in_cart = 0
    cart_result = None
    if user.is_authenticated:
        cart_result = Cart.objects.filter(user=user.profil)
        for el in cart_result:
            stock = el.product.stock_set.filter(color=el.color).exclude(color__name__exact="None")
            if stock.exists():
                el.product.price = el.product.price + stock.all()[0].price_sup
            number_products_in_cart += 1
            sale = el.product.sale_set.filter(date_end__gte=datetime.date.today())
            if sale.exists():
                el.product.price = el.product.price - ((el.product.price * sale.all()[0].percentage) / 100)
            total_price_in_cart += (el.product.price * el.quantity)
    return {'cart': cart_result, 'number_products_in_cart': number_products_in_cart, 'total_price_in_cart': total_price_in_cart}


def my_featured_sale():
    hot_categories = list()
    featured_sale = Sale.objects.filter(date_end__gte=datetime.date.today()).values('product__cat__category') \
                        .annotate(Max('percentage')).order_by('-percentage__max')[:6]
    for el in featured_sale:
        cat = CommerceCategory.objects.get(pk=el["product__cat__category"])
        hot_categories.append(cat)
        el["product__cat__category"] = cat
    # Complete 4 categories
    count = len(hot_categories)
    if count < 4:
        for i in range(0, CommerceCategory.objects.count()):
            category_to_add = CommerceCategory.objects.all()[i]
            if category_to_add not in hot_categories:
                hot_categories.append(category_to_add)
            if len(hot_categories) == 4:
                break
    return {'hot_categories': hot_categories, 'featured_sale': featured_sale}


def test(request, id_request):
    return HttpResponse("hi {}".format(id_request))
