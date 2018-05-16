from django.urls import path
from ecommerce import views

app_name = 'e_commerce'
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:id_request>/', views.test, name='test'),
    path('search/', views.search, name='search'),
    path('products/', views.products, name='products'),
    path('products/<str:type_search>/<str:id_search>/', views.products, name='products'),
    path('product/', views.display_product, name='product'),
    path('product/<str:id_product>/', views.display_product, name='product'),
    path('quick_view/<str:id_product>/', views.quick_view, name='quick_view'),
    path('checkout/', views.checkout, name='checkout'),
    #--------------- Cart
    path('cart/', views.cart, name='cart'),
    path('cart/update_cart/', views.update_cart, name='update_cart'),
    path('cart/update_color_cart', views.update_color_cart, name='update_color_cart'),
    path('cart/remove_from_page_cart', views.remove_from_page_cart, name='remove_from_page_cart'),
    path('wish_list/', views.wish_list, name='wish_list'),
    path('wish_list/add_from_wish/', views.add_from_wish, name='add_from_wish'),
    path('wish_list/remove_from_wish/', views.remove_from_wish, name='remove_from_wish'),
    path('compare/', views.compare, name='compare'),
    path('compare/add_from_compare/', views.add_from_compare, name='add_from_compare'),
    path('compare/remove_from_compare/', views.remove_from_compare, name='remove_from_compare'),
    path('add_to_compare', views.add_to_compare, name='add_to_compare'),
    path('add_to_wish_list', views.add_to_wish, name='add_to_wish_list'),
    path('add_to_cart', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart', views.remove_from_cart, name='remove_from_cart'),
    # ------------ Easy
    path('contact-us/', views.contact_us, name='contact-us'),
    path('my-account/', views.my_account, name='my_account'),
    # ------------ Static pages
    path('FAQ/', views.faq, name='faq'),
    path('sitemap/', views.sitemap, name='sitemap'),
    path('about-us/', views.about_us, name='about-us'),
]
