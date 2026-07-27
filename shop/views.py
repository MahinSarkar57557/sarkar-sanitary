from django.shortcuts import render, redirect, get_object_or_404
from .models import Category, SubCategory, Product, Cart, Order, OrderItem, ContactMessage
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from decimal import Decimal
from django.db.models import Q  # 🔍 সার্চের জন্য ইমপোর্ট করা হলো

# ==========================================
# ১. মেইন হোমপেজ ভিউ (সার্চ সুবিধাসহ)
# ==========================================
def index(request):
    categories = Category.objects.all()
    
    selected_category_id = request.GET.get('category')
    selected_subcategory_id = request.GET.get('subcategory')
    search_query = request.GET.get('q')  # 📩 সার্চ বক্সের ইনপুট (name="q") রিসিভ করা
    
    selected_cat = None
    selected_sub = None
    subcategories = None
    
    products = Product.objects.all()

    # ১.১. ক্যাটাগরি ফিল্টার
    if selected_category_id:
        selected_cat = get_object_or_404(Category, id=selected_category_id)
        subcategories = selected_cat.subcategories.all()
        products = products.filter(category=selected_cat)

    # ১.২. সাব-ক্যাটাগরি ফিল্টার
    if selected_subcategory_id:
        selected_sub = get_object_or_404(SubCategory, id=selected_subcategory_id)
        products = products.filter(subcategory=selected_sub)

    # 🔍 ১.৩. সার্চ বার ফিল্টার (নাম, ব্র্যান্ড, ক্যাটাগরি বা সাব-ক্যাটাগরি মিললে ফিল্টার হবে)
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(subcategory__name__icontains=search_query)
        ).distinct()

    context = {
        'categories': categories,
        'subcategories': subcategories,
        'selected_cat': selected_cat,
        'selected_sub': selected_sub,
        'products': products,
        'query': search_query,  # সার্চের ইনপুট টেমপ্লেটে ধরে রাখার জন্য
    }
    return render(request, 'shop/index.html', context)


# ==========================================
# ২. প্রোডাক্ট ডিটেইলস ভিউ
# ==========================================
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'shop/product_detail.html', {'product': product})


# ==========================================
# ৩. কার্ট ম্যানেজমেন্ট সেকশন 
# ==========================================
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    qty = 1
    if request.method == 'POST':
        qty = int(request.POST.get('quantity', 1))
        
    if product.stock < qty:
        messages.error(request, f"দুঃখিত, পর্যাপ্ত স্টক নেই! মাত্র {product.stock} টি উপলব্ধ।")
        return redirect('product_detail', product_id=product_id)

    if request.user.is_authenticated:
        cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
        if not created:
            cart_item.quantity += qty
        else:
            cart_item.quantity = qty
        cart_item.save()
    else:
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        if product_id_str in cart:
            cart[product_id_str] += qty
        else:
            cart[product_id_str] = qty
            
        request.session['cart'] = cart
        
    messages.success(request, f"{product.name} সফলভাবে কার্টে যোগ হয়েছে।")
    return redirect('cart_view')


def remove_from_cart(request, product_id):
    if request.user.is_authenticated:
        product = get_object_or_404(Product, id=product_id)
        cart_item = Cart.objects.filter(user=request.user, product=product).first()
        if cart_item:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
    else:
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        if product_id_str in cart:
            if cart[product_id_str] > 1:
                cart[product_id_str] -= 1
            else:
                del cart[product_id_str]
            request.session['cart'] = cart
            
    return redirect('cart_view')


def delete_cart_item(request, product_id):
    if request.user.is_authenticated:
        product = get_object_or_404(Product, id=product_id)
        Cart.objects.filter(user=request.user, product=product).delete()
    else:
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        if product_id_str in cart:
            del cart[product_id_str]
            request.session['cart'] = cart
            
    messages.success(request, "প্রোডাক্টটি কার্ট থেকে সম্পূর্ণ মুছে ফেলা হয়েছে।")
    return redirect('cart_view')


def cart_view(request):
    cart_items = []
    subtotal = 0
    
    if request.user.is_authenticated:
        db_items = Cart.objects.filter(user=request.user)
        subtotal = sum(item.total_price for item in db_items)
        cart_items = db_items
    else:
        cart = request.session.get('cart', {})
        for product_id, quantity in cart.items():
            product = Product.objects.filter(id=int(product_id)).first()
            if product:
                total_price = product.price * quantity
                subtotal += total_price
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'total_price': total_price
                })
                
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
    }
    return render(request, 'shop/cart.html', context)


# ==========================================
# ৪. ফিক্সড চেকআউট সেকশন (OrderItem ক্রিয়েটসহ)
# ==========================================
def checkout_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        shipping_area = request.POST.get('shipping_area')  
        location = request.POST.get('location')
        
        shipping_charge = Decimal(shipping_area) if shipping_area else Decimal('0')
        cart_subtotal = 0
        items_to_create = [] # অর্ডার আইটেমের ডেটা জমানোর জন্য
        
        if request.user.is_authenticated:
            cart_items = Cart.objects.filter(user=request.user)
            if not cart_items.exists():
                return redirect('index')
                
            cart_subtotal = sum(item.total_price for item in cart_items)
            for item in cart_items:
                items_to_create.append({
                    'product': item.product,
                    'quantity': item.quantity,
                    'price': item.product.price
                })
            clear_cart_action = lambda: cart_items.delete()
        else:
            cart = request.session.get('cart', {})
            if not cart:
                return redirect('index')
                
            for product_id, quantity in cart.items():
                product = Product.objects.filter(id=int(product_id)).first()
                if product:
                    cart_subtotal += (product.price * quantity)
                    items_to_create.append({
                        'product': product,
                        'quantity': quantity,
                        'price': product.price
                    })
            clear_cart_action = lambda: request.session.pop('cart', None)

        grand_total = cart_subtotal + shipping_charge
        
        # ১. অর্ডার ক্রিয়েট করা
        order_user = request.user if request.user.is_authenticated else None
        order = Order.objects.create(
            user=order_user,
            name=name,
            phone=phone,
            location=f"{location} (Shipping: ৳{int(shipping_charge)})",
            total_amount=grand_total,
            status='Pending'
        )
        
        # ২. OrderItem টেবিল আইটেম যুক্ত করা
        for item_data in items_to_create:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                quantity=item_data['quantity'],
                price=item_data['price']
            )
        
        # ৩. কার্ট খালি করে দেওয়া
        clear_cart_action()
        
        messages.success(request, f"ধন্যবাদ {name}! আপনার অর্ডারটি সফলভাবে সম্পন্ন হয়েছে।")
        return redirect('index')
        
    return redirect('cart_view')


# ==========================================
# ৫. সেলার ইনভেন্টরি ও অর্ডার ড্যাশবোর্ড
# ==========================================
@staff_member_required
def seller_dashboard(request):
    products = Product.objects.all()
    orders = Order.objects.all().order_by('-created_at')
    
    total_orders = orders.count()
    total_products = products.count()
    low_stock_products = Product.objects.filter(stock__lte=5)
    
    context = {
        'products': products,
        'orders': orders,
        'total_orders': total_orders,
        'total_products': total_products,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'shop/dashboard.html', context)


@staff_member_required
def update_order_status(request, order_id, status):
    order = get_object_or_404(Order, id=order_id)
    
    # ডেলিভারি কনফার্ম করলে স্টক কমে যাবে
    if status == 'Delivered' and order.status != 'Delivered':
        for item in order.items.all():
            product = item.product
            if product.stock >= item.quantity:
                product.stock -= item.quantity
            else:
                product.stock = 0
            product.save()
        
        order.status = 'Delivered'
        order.save()
        messages.success(request, f"অর্ডার #{order.id} ডেলিভার্ড করা হয়েছে এবং স্টক আপডেট হয়েছে।")

    elif status == 'Confirmed':
        order.status = 'Confirmed'
        order.save()
        messages.info(request, f"অর্ডার #{order.id} কনফার্ম করা হয়েছে।")

    elif status == 'Cancelled':
        order.status = 'Cancelled'
        order.save()
        messages.warning(request, f"অর্ডার #{order.id} বাতিল করা হয়েছে।")

    return redirect('seller_dashboard')


# ==========================================
# 📋 ৬. অন্যান্য পেজ এবং কন্টাক্ট ভিউ
# ==========================================
def gallery_view(request):
    return render(request, 'shop/gallery.html')

def about_view(request):
    return render(request, 'shop/about.html')

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        message = request.POST.get('message')

        ContactMessage.objects.create(
            name=name,
            phone=phone,
            email=email,
            message=message
        )

        messages.success(request, 'message sent successfully.Thank You!')
        return redirect('contact')

    return render(request, 'shop/contact.html')