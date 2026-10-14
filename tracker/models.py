from django.db import models


# Category
class Category(models.Model):

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE
    )

    name = models.CharField(
        max_length=100
    )

    def __str__(self):
        return self.name


# Transaction
class Transaction(models.Model):

    TRANSACTION_TYPES = [
        ('CREDIT', 'credit'),
        ('DEBIT', 'debit'),
    ]

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES
    )

    description = models.TextField(
        blank=True
    )

    date = models.DateField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"


# Budget
class Budget(models.Model):

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    month = models.IntegerField()

    year = models.IntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f'{self.user.username} - {self.month}/{self.year}'


# Savings Goal
class SavingsGoal(models.Model):

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE
    )

    name = models.CharField(
        max_length=100
    )

    target_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    saved_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    target_date = models.DateField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


class Loan(models.Model):

    LOAN_TYPES = [
        ('BORROWED', 'Borrowed'),
        ('LENT', 'Lent'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
    ]

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE
    )

    person_name = models.CharField(
        max_length=100
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    loan_type = models.CharField(
        max_length=10,
        choices=LOAN_TYPES
    )

    due_date = models.DateField(
        null=True,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    @property
    def remaining_amount(self):
        return self.amount - self.paid_amount

    def __str__(self):
        return f'{self.person_name} - {self.amount}'