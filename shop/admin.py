from django.contrib import admin
from .models import Category, SubCategory, Product, Cart, Order, ContactMessage

# প্রোডাক্ট টেবিলটি এডমিন প্যানেলে সুন্দর করে দেখানোর জন্য
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'subcategory', 'brand', 'price', 'stock')
    list_filter = ('subcategory', 'brand')
    search_fields = ('name',)

# কন্টাক্ট মেসেজগুলো অ্যাডমিনে সুন্দর করে দেখানোর জন্য
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'phone')

# নতুন ও পুরোনো সব টেবিল এডমিন প্যানেলে রেজিস্টার করা হলো
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(Product, ProductAdmin)