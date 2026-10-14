from django.contrib import admin
from .models import Category, Transaction, Budget, SavingsGoal, Loan


admin.site.register(Category)
admin.site.register(Transaction)
admin.site.register(Budget)
admin.site.register(SavingsGoal)
admin.site.register(Loan)