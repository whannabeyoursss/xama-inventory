from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),

    # ADMIN
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/products/', views.product_list, name='product_list'),
    path('admin-panel/products/create/', views.product_create, name='product_create'),
    path('admin-panel/products/<int:pk>/', views.product_detail, name='product_detail'),
    path('admin-panel/products/<int:pk>/update/', views.product_update, name='product_update'),
    path('admin-panel/products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('admin-panel/categories/', views.category_list, name='category_list'),
    path('admin-panel/categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('admin-panel/suppliers/', views.supplier_list, name='supplier_list'),
    path('admin-panel/suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
    path('admin-panel/purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    path('admin-panel/sales-orders/', views.sales_order_list, name='sales_order_list'),
    path('admin-panel/sales-orders/<int:pk>/', views.sales_order_detail, name='admin_sales_order_detail'),
    path('admin-panel/users/', views.user_list, name='user_list'),
    path('admin-panel/users/<int:pk>/role/', views.user_role_update, name='user_role_update'),
    path('admin-panel/notes/create/', views.note_create, name='note_create'),
    path('admin-panel/notes/<int:pk>/delete/', views.note_delete, name='note_delete'),
    path('admin-panel/notes/<int:pk>/update/', views.note_update, name='note_update'),

    # CUSTOMER
    path('shop/', views.customer_dashboard, name='customer_dashboard'),
    path('shop/products/', views.customer_product_browse, name='customer_product_browse'),
    path('shop/place-order/', views.customer_place_order, name='customer_place_order'),
    path('shop/my-orders/', views.customer_my_orders, name='customer_my_orders'),
]