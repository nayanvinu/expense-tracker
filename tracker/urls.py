from django.urls import path
from .import views

urlpatterns = [
    path('',views.dashboard,name='dashboard'),
    path('register/',views.register,name='register'),
    path('login/',views.user_login,name='login'),
    path('logout/',views.user_logout,name='logout'),
    path('categories/',views.categories,name='categories'),
    path('categories/delete/<int:id>',views.delete_category,name="delete_category"),
    path('transaction/add',views.add_transaction,name='add_transaction'),
    path('transactions/', views.transactions, name='transactions'),
    path('transaction/delete/<int:id>',views.delete_transaction,name='delete_transaction'),
    path('transaction/edit/<int:id>',views.edit_transaction,name='edit_transaction'),
    path('about/', views.about, name='about'),
    path('account/', views.account, name='account'),
    path('account/change-password/', views.change_password, name='change_password'),
    path('account/delete/', views.delete_account, name='delete_account'),
    path('calculator/', views.calculator, name='calculator'),
    path('reports/', views.reports, name='reports'),
    path('budget/', views.budget, name='budget'),
    path(
        'savings-goals/',
        views.savings_goals,
        name='savings_goals'
    ),

    path(
        'savings-goals/add/<int:id>/',
        views.add_savings,
        name='add_savings'
    ),

    path(
        'savings-goals/delete/<int:id>/',
        views.delete_savings_goal,
        name='delete_savings_goal'
    ),

    path(
    'loans/',
    views.loans,
    name='loans'
    ),

    path(
        'loans/paid/<int:id>/',
        views.mark_loan_paid,
        name='mark_loan_paid'
    ),

    path(
        'loans/delete/<int:id>/',
        views.delete_loan,
        name='delete_loan'
    ),

    path(
        'loans/payment/<int:id>/',
        views.add_loan_payment,
        name='add_loan_payment'
    ),

    path(
        'loans/edit/<int:id>/',
        views.edit_loan,
        name='edit_loan'
    ),
]