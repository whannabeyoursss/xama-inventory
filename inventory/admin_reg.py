from django.contrib import admin
from .models import (Category, Supplier, Product, PurchaseOrder,
                     SalesOrder, StockMovement, UserProfile,
                     PurchaseOrderItem, SalesOrderItem)

admin.site.register(UserProfile)
admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(Product)
admin.site.register(PurchaseOrder)
admin.site.register(PurchaseOrderItem)
admin.site.register(SalesOrder)
admin.site.register(SalesOrderItem)
admin.site.register(StockMovement)