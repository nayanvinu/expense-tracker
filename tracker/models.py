from django.db import models

# Create your models here.


class Category(models.Model):
    name=models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPES=[
        ('CREDIT','credit'),
        ('DEBIT','debit'),
    ]
    user=models.ForeignKey('auth.User',on_delete=models.CASCADE)
    category=models.ForeignKey(Category,on_delete=models.CASCADE)
    amount=models.DecimalField(max_digits=10,decimal_places=2)
    transaction_type=models.CharField(max_length=10,choices=TRANSACTION_TYPES)
    description=models.TextField(blank=True)
    date=models.DateField()
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"


