from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Q, F
from functools import wraps
from .models import (Product, Category, Supplier, PurchaseOrder,
                     SalesOrder, StockMovement, UserProfile,
                     SalesOrderItem, PurchaseOrderItem, AdminNote)


# ─────────────────────────────────────────
# Role decorators
# ─────────────────────────────────────────

def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        try:
            if request.user.profile.is_admin:
                return view_func(request, *args, **kwargs)
        except UserProfile.DoesNotExist:
            pass
        messages.error(request, 'Access denied. Admin only.')
        return redirect('customer_dashboard')
    return wrapper


def customer_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        try:
            if request.user.profile.is_customer:
                return view_func(request, *args, **kwargs)
        except UserProfile.DoesNotExist:
            pass
        return redirect('admin_dashboard')
    return wrapper


# ─────────────────────────────────────────
# Auth / redirect after login
# ─────────────────────────────────────────

@login_required
def home(request):
    try:
        if request.user.profile.is_admin:
            return redirect('admin_dashboard')
    except UserProfile.DoesNotExist:
        pass
    return redirect('customer_dashboard')


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()

        errors = []

        if not username:
            errors.append('Username is required.')
        elif User.objects.filter(username=username).exists():
            errors.append('Username already taken.')

        if not email:
            errors.append('Email is required.')
        elif User.objects.filter(email=email).exists():
            errors.append('Email already registered.')

        if len(password1) < 8:
            errors.append('Password must be at least 8 characters.')

        if password1 != password2:
            errors.append('Passwords do not match.')

        if errors:
            return render(request, 'inventory/register.html', {
                'errors': errors,
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )

        login(request, user)
        messages.success(request, f'Welcome to XAMA, {user.username}! Your account has been created.')
        return redirect('customer_dashboard')

    return render(request, 'inventory/register.html')


# ─────────────────────────────────────────
# ADMIN VIEWS
# ─────────────────────────────────────────

@admin_required
def admin_dashboard(request):
    total_products = Product.objects.count()
    low_stock_count = Product.objects.filter(status='low_stock').count()
    out_of_stock_count = Product.objects.filter(status='out_of_stock').count()
    total_value = Product.objects.aggregate(
        total=Sum(F('quantity') * F('unit_price'))
    )['total'] or 0
    pending_purchase_orders = PurchaseOrder.objects.filter(status='pending').count()
    pending_sales_orders = SalesOrder.objects.filter(status='pending').count()
    recent_products = Product.objects.select_related('category', 'supplier').all()[:10]
    low_stock_products = Product.objects.filter(
        Q(status='low_stock') | Q(status='out_of_stock')
    )[:5]
    total_customers = UserProfile.objects.filter(role='customer').count()
    notes = AdminNote.objects.all()

    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'total_value': total_value,
        'pending_purchase_orders': pending_purchase_orders,
        'pending_sales_orders': pending_sales_orders,
        'recent_products': recent_products,
        'low_stock_products': low_stock_products,
        'total_customers': total_customers,
        'notes': notes,
    }
    return render(request, 'inventory/admin/dashboard.html', context)


@admin_required
def product_list(request):
    products = Product.objects.select_related('category', 'supplier').all()
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(Q(name__icontains=search_query) | Q(sku__icontains=search_query))
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)
    status = request.GET.get('status', '')
    if status:
        products = products.filter(status=status)
    categories = Category.objects.all()
    context = {'products': products, 'categories': categories, 'search_query': search_query}
    return render(request, 'inventory/admin/product_list.html', context)


@admin_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    stock_movements = StockMovement.objects.filter(product=product)[:10]
    context = {'product': product, 'stock_movements': stock_movements}
    return render(request, 'inventory/admin/product_detail.html', context)


@admin_required
def product_create(request):
    if request.method == 'POST':
        product = Product.objects.create(
            sku=request.POST.get('sku'),
            name=request.POST.get('name'),
            description=request.POST.get('description', ''),
            category_id=request.POST.get('category') or None,
            supplier_id=request.POST.get('supplier') or None,
            unit_price=request.POST.get('unit_price'),
            quantity=request.POST.get('quantity', 0),
            reorder_level=request.POST.get('reorder_level', 10),
        )
        if 'image' in request.FILES:
            product.image = request.FILES['image']
            product.save()
        messages.success(request, f'Product {product.name} created successfully!')
        return redirect('product_list')
    context = {'categories': Category.objects.all(), 'suppliers': Supplier.objects.all()}
    return render(request, 'inventory/admin/product_form.html', context)


@admin_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.sku = request.POST.get('sku')
        product.name = request.POST.get('name')
        product.description = request.POST.get('description', '')
        product.category_id = request.POST.get('category') or None
        product.supplier_id = request.POST.get('supplier') or None
        product.unit_price = request.POST.get('unit_price')
        product.quantity = request.POST.get('quantity', 0)
        product.reorder_level = request.POST.get('reorder_level', 10)
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        product.save()
        messages.success(request, f'Product {product.name} updated!')
        return redirect('product_detail', pk=product.pk)
    context = {
        'product': product,
        'categories': Category.objects.all(),
        'suppliers': Supplier.objects.all(),
    }
    return render(request, 'inventory/admin/product_form.html', context)


@admin_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted.')
        return redirect('product_list')
    return render(request, 'inventory/admin/product_confirm_delete.html', {'product': product})


@admin_required
def category_list(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        if name:
            Category.objects.create(name=name, description=description)
            messages.success(request, f'Category "{name}" added!')
        return redirect('category_list')
    categories = Category.objects.annotate(product_count=Count('product'))
    return render(request, 'inventory/admin/category_list.html', {'categories': categories})


@admin_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted.')
    return redirect('category_list')


@admin_required
def supplier_list(request):
    if request.method == 'POST':
        Supplier.objects.create(
            name=request.POST.get('name'),
            contact_person=request.POST.get('contact_person'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address', ''),
        )
        messages.success(request, 'Supplier added!')
        return redirect('supplier_list')
    suppliers = Supplier.objects.annotate(product_count=Count('product'))
    return render(request, 'inventory/admin/supplier_list.html', {'suppliers': suppliers})


@admin_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, 'Supplier deleted.')
    return redirect('supplier_list')


@admin_required
def purchase_order_list(request):
    orders = PurchaseOrder.objects.select_related('supplier').all()
    return render(request, 'inventory/admin/purchase_order_list.html', {'orders': orders})


@admin_required
def sales_order_list(request):
    orders = SalesOrder.objects.select_related('created_by').all()
    return render(request, 'inventory/admin/sales_order_list.html', {'orders': orders})


@admin_required
def sales_order_detail(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status:
            order.status = new_status
            order.save()
            messages.success(request, f'Order status updated to {new_status}.')
        return redirect('admin_sales_order_detail', pk=pk)
    return render(request, 'inventory/admin/sales_order_detail.html', {'order': order})


@admin_required
def user_list(request):
    profiles = UserProfile.objects.select_related('user').all()
    return render(request, 'inventory/admin/user_list.html', {'profiles': profiles})


@admin_required
def user_role_update(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk)
    if request.method == 'POST':
        profile.role = request.POST.get('role')
        profile.save()
        messages.success(request, f'{profile.user.username} role updated to {profile.role}.')
    return redirect('user_list')


@admin_required
def note_create(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        priority = request.POST.get('priority', 'normal')
        if title and content:
            AdminNote.objects.create(
                title=title,
                content=content,
                priority=priority,
                created_by=request.user,
            )
            messages.success(request, 'Note added!')
        return redirect('admin_dashboard')
    return redirect('admin_dashboard')


@admin_required
def note_delete(request, pk):
    note = get_object_or_404(AdminNote, pk=pk)
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Note deleted.')
    return redirect('admin_dashboard')


@admin_required
def note_update(request, pk):
    note = get_object_or_404(AdminNote, pk=pk)
    if request.method == 'POST':
        note.title = request.POST.get('title', '').strip()
        note.content = request.POST.get('content', '').strip()
        note.priority = request.POST.get('priority', 'normal')
        note.save()
        messages.success(request, 'Note updated!')
    return redirect('admin_dashboard')


# ─────────────────────────────────────────
# CUSTOMER VIEWS
# ─────────────────────────────────────────

@customer_required
def customer_dashboard(request):
    products = Product.objects.filter(status='in_stock').select_related('category')[:12]
    categories = Category.objects.all()
    my_orders = SalesOrder.objects.filter(created_by=request.user).order_by('-order_date')[:5]
    context = {'products': products, 'categories': categories, 'my_orders': my_orders}
    return render(request, 'inventory/customer/dashboard.html', context)


@customer_required
def customer_product_browse(request):
    products = Product.objects.filter(
        status__in=['in_stock', 'low_stock']
    ).select_related('category')
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(Q(name__icontains=search_query) | Q(category__name__icontains=search_query))
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)
    categories = Category.objects.all()
    context = {'products': products, 'categories': categories, 'search_query': search_query}
    return render(request, 'inventory/customer/product_browse.html', context)


@customer_required
def customer_place_order(request):
    if request.method == 'POST':
        import random, string
        order_number = ''.join(random.choices(string.digits, k=8))
        product_ids = request.POST.getlist('product_id')
        quantities = request.POST.getlist('quantity')

        if not product_ids:
            messages.error(request, 'Please select at least one product.')
            return redirect('customer_place_order')

        order = SalesOrder.objects.create(
            order_number=order_number,
            customer_name=request.POST.get('customer_name'),
            customer_email=request.user.email,
            customer_phone=request.POST.get('customer_phone'),
            shipping_address=request.POST.get('shipping_address'),
            notes=request.POST.get('notes', ''),
            created_by=request.user,
        )
        for pid, qty in zip(product_ids, quantities):
            if pid and qty and int(qty) > 0:
                product = Product.objects.get(pk=pid)
                SalesOrderItem.objects.create(
                    sales_order=order,
                    product=product,
                    quantity=int(qty),
                    unit_price=product.unit_price,
                )
        messages.success(request, f'Order #{order.order_number} placed successfully!')
        return redirect('customer_my_orders')

    products = Product.objects.filter(status__in=['in_stock', 'low_stock'])
    return render(request, 'inventory/customer/place_order.html', {'products': products})


@customer_required
def customer_my_orders(request):
    orders = SalesOrder.objects.filter(created_by=request.user).prefetch_related('items__product')
    return render(request, 'inventory/customer/my_orders.html', {'orders': orders})