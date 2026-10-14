from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth import login,logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Category, Transaction, Budget, SavingsGoal,Loan
from datetime import date
from decimal import Decimal, InvalidOperation
# Create your views here.

@login_required
def dashboard(request):

    today = date.today()

    # ==========================================
    # ALL TRANSACTIONS
    # ==========================================

    transactions = Transaction.objects.filter(
        user=request.user
    )

    # ==========================================
    # TOTAL CREDIT
    # ==========================================

    total_credit = transactions.filter(
        transaction_type='CREDIT'
    ).aggregate(
        Sum('amount')
    )['amount__sum'] or Decimal('0')

    # ==========================================
    # TOTAL DEBIT
    # ==========================================

    total_debit = transactions.filter(
        transaction_type='DEBIT'
    ).aggregate(
        Sum('amount')
    )['amount__sum'] or Decimal('0')

    # ==========================================
    # BALANCE
    # ==========================================

    balance = total_credit - total_debit

    # ==========================================
    # CURRENT MONTH TRANSACTIONS
    # ==========================================

    current_month_transactions = transactions.filter(
        date__month=today.month,
        date__year=today.year
    )

    # ==========================================
    # CURRENT MONTH INCOME
    # ==========================================

    monthly_income = current_month_transactions.filter(
        transaction_type='CREDIT'
    ).aggregate(
        Sum('amount')
    )['amount__sum'] or Decimal('0')

    # ==========================================
    # CURRENT MONTH EXPENSES
    # ==========================================

    monthly_expenses = current_month_transactions.filter(
        transaction_type='DEBIT'
    ).aggregate(
        Sum('amount')
    )['amount__sum'] or Decimal('0')

    # ==========================================
    # MONTHLY SAVINGS
    # ==========================================

    monthly_savings = monthly_income - monthly_expenses

    # ==========================================
    # CREDIT / DEBIT CHART
    # ==========================================

    chart_data = {
        'labels': [
            'Credit',
            'Debit'
        ],
        'values': [
            float(total_credit),
            float(total_debit)
        ]
    }

    # ==========================================
    # EXPENSE BY CATEGORY
    # ==========================================

    category_data = (
        transactions
        .filter(
            transaction_type='DEBIT'
        )
        .values(
            'category__name'
        )
        .annotate(
            total=Sum('amount')
        )
        .order_by('-total')
    )

    category_labels = [
        item['category__name']
        for item in category_data
    ]

    category_amounts = [
        float(item['total'])
        for item in category_data
    ]

    # ==========================================
    # RECENT TRANSACTIONS
    # ==========================================

    recent_transactions = transactions.order_by(
        '-date',
        '-created_at'
    )[:5]

    # ==========================================
    # CURRENT MONTH BUDGET
    # ==========================================

    current_budget = Budget.objects.filter(
        user=request.user,
        month=today.month,
        year=today.year
    ).first()

    if current_budget:

        budget_amount = current_budget.amount

        budget_remaining = (
            budget_amount - monthly_expenses
        )

        if budget_amount > 0:

            budget_percentage = (
                float(monthly_expenses)
                / float(budget_amount)
            ) * 100

        else:
            budget_percentage = 0

        budget_progress = min(
            budget_percentage,
            100
        )

        budget_over = (
            monthly_expenses > budget_amount
        )

    else:

        budget_amount = Decimal('0')
        budget_remaining = Decimal('0')
        budget_percentage = 0
        budget_progress = 0
        budget_over = False

    # ==========================================
    # SAVINGS GOALS
    # ==========================================

    savings_goals = SavingsGoal.objects.filter(
        user=request.user
    ).order_by(
        '-created_at'
    )[:3]

    savings_goal_data = []

    for goal in savings_goals:

        if goal.target_amount > 0:

            percentage = (
                float(goal.saved_amount)
                / float(goal.target_amount)
            ) * 100

        else:

            percentage = 0

        percentage = min(
            percentage,
            100
        )

        remaining = (
            goal.target_amount
            - goal.saved_amount
        )

        completed = (
            goal.saved_amount
            >= goal.target_amount
        )

        savings_goal_data.append({
            'goal': goal,
            'percentage': round(
                percentage,
                1
            ),
            'remaining': remaining,
            'completed': completed,
        })

    # ==========================================
    # LOANS
    # ==========================================

    all_loans = Loan.objects.filter(
        user=request.user
    )

    # Pending loan amount

    pending_loans = [
        loan
        for loan in all_loans
        if loan.status == 'PENDING'
    ]

    pending_loan_amount = sum(
        (
            loan.remaining_amount
            for loan in pending_loans
        ),
        Decimal('0')
    )

    # ==========================================
    # OVERDUE LOANS
    # ==========================================

    overdue_loans = [
        loan
        for loan in pending_loans
        if loan.due_date
        and loan.due_date < today
    ]

    overdue_loan_amount = sum(
        (
            loan.remaining_amount
            for loan in overdue_loans
        ),
        Decimal('0')
    )

    # ==========================================
    # RECENT LOANS
    # ==========================================

    recent_loans = all_loans.order_by(
        '-created_at'
    )[:3]

    # ==========================================
    # DASHBOARD CONTEXT
    # ==========================================

    context = {

        # Basic financial information

        'message': 'Welcome to SpendWise',

        'credit': total_credit,

        'debit': total_debit,

        'balance': balance,

        # Current month

        'monthly_income': monthly_income,

        'monthly_expenses': monthly_expenses,

        'monthly_savings': monthly_savings,

        # Charts

        'chart_data': chart_data,

        'category_labels': category_labels,

        'category_amounts': category_amounts,

        # Recent transactions

        'recent_transactions': recent_transactions,

        # Budget

        'current_budget': current_budget,

        'budget_amount': budget_amount,

        'budget_remaining': budget_remaining,

        'budget_percentage': round(
            budget_percentage,
            1
        ),

        'budget_progress': budget_progress,

        'budget_over': budget_over,

        # Savings goals

        'savings_goal_data': savings_goal_data,

        # Loans

        'pending_loan_amount': pending_loan_amount,

        'overdue_loan_amount': overdue_loan_amount,

        'pending_loan_count': len(
            pending_loans
        ),

        'overdue_loan_count': len(
            overdue_loans
        ),

        'recent_loans': recent_loans,
    }

    return render(
        request,
        'tracker/dashboard.html',
        context
    )

def register(request):
    context = {}

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not username:
            context["error"] = "Username is required."

        elif password != confirm_password:
            context["error"] = "Passwords do not match."

        elif User.objects.filter(username=username).exists():
            context["error"] = "Username already exists."

        else:
            try:
                validate_password(password)

                User.objects.create_user(
                    username=username,
                    password=password
                )

                return redirect("login")

            except ValidationError as e:
                context["password_errors"] = e.messages

    return render(
        request,
        "tracker/register.html",
        context
    )

def user_login(request):
    context={}

    if request.method=="POST":
        username=request.POST.get("username")
        password=request.POST.get("password")
        user=authenticate(
            request,
            username=username,
            password=password
        )
        if user:
            login(request,user)
            return redirect('dashboard')
        else:
            context={
                "error":"Invalid username or password"
            }

    return render(request,'tracker/login.html',context)

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def categories(request):
    if request.method=="POST":
        name=request.POST.get("name")
        Category.objects.create(
                name=name,
                user=request.user
        )
    categories=Category.objects.filter(user=request.user)
    return render(request,'tracker/categories.html',{"categories":categories})

@login_required
def delete_category(request,id):
    category=Category.objects.get(
        id=id,
        user=request.user
    )

    category.delete()

    return redirect('categories')

@login_required
def add_transaction(request):
    categories = Category.objects.filter(user=request.user)

    if request.method=='POST':
        category_id=request.POST.get('Category')

        category=Category.objects.get(
            id=category_id,
            user=request.user
        )

        amount = request.POST.get('amount')
        transaction_type = request.POST.get('transaction_type')
        date = request.POST.get('date')
        description = request.POST.get('description')

        Transaction.objects.create(
            user=request.user,
            category=category,
            amount=amount,
            transaction_type=transaction_type,
            date=date,
            description=description
        )
    
    return render(request,'tracker/add_transaction.html',{'categories':categories})


@login_required
def transactions(request):

    transactions = Transaction.objects.filter(
        user=request.user
    )

    categories = Category.objects.filter(
        user=request.user
    )

    transaction_type = request.GET.get('type')
    category_id = request.GET.get('category')

    if transaction_type:
        transactions = transactions.filter(
            transaction_type=transaction_type
        )

    if category_id:
        transactions = transactions.filter(
            category_id=category_id
        )

    return render(
        request,
        'tracker/transactions.html',
        {
            'transactions': transactions,
            'categories': categories,
        }
    )
@login_required
def delete_transaction(request, id):

    if request.method == "POST":

        transaction = Transaction.objects.get(
            id=id,
            user=request.user
        )

        transaction.delete()

    return redirect('transactions')

@login_required
def edit_transaction(request, id):
    transaction = Transaction.objects.get(
        id=id,
        user=request.user
    )

    if request.method == 'POST':
        category_id = request.POST.get('category')

        category = Category.objects.get(
            id=category_id,
            user=request.user
        )

        transaction.category = category
        transaction.amount = request.POST.get('amount')
        transaction.transaction_type = request.POST.get('transaction_type')
        transaction.description = request.POST.get('description')
        transaction.date = request.POST.get('date')

        transaction.save()

        return redirect('transactions')

    categories = Category.objects.filter(user=request.user)

    return render(request,'tracker/edit_transaction.html',{'transaction': transaction,'categories': categories}
    )

def about(request):
    return render(request, 'tracker/about.html')

@login_required
def account(request):
    return render(
        request,
        'tracker/account.html'
    )


@login_required
def change_password(request):

    if request.method == "POST":

        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if not request.user.check_password(current_password):
            return render(
                request,
                'tracker/account.html',
                {
                    'password_error': 'Current password is incorrect.'
                }
            )

        if new_password != confirm_password:
            return render(
                request,
                'tracker/account.html',
                {
                    'password_error': 'New passwords do not match.'
                }
            )

        try:
            validate_password(
                new_password,
                request.user
            )

            request.user.set_password(new_password)
            request.user.save()

            logout(request)

            return redirect('login')

        except ValidationError as e:

            return render(
                request,
                'tracker/account.html',
                {
                    'password_errors': e.messages
                }
            )

    return redirect('account')

@login_required
def delete_account(request):

    if request.method == "POST":

        user = request.user

        logout(request)

        user.delete()

        return redirect('login')

    return redirect('account')

@login_required
def calculator(request):
    categories = Category.objects.filter(user=request.user).order_by('name')

    if request.method == "POST":
        entries = request.POST.getlist("amount[]")
        types = request.POST.getlist("transaction_type[]")
        category_ids = request.POST.getlist("category[]")
        descriptions = request.POST.getlist("description[]")
        dates = request.POST.getlist("date[]")

        for i in range(len(entries)):
            try:
                amount = Decimal(entries[i])

                if amount <= 0:
                    continue

                category = Category.objects.get(
                    id=category_ids[i],
                    user=request.user
                )

                transaction_type = types[i]

                if transaction_type not in ["CREDIT", "DEBIT"]:
                    continue

                Transaction.objects.create(
                    user=request.user,
                    category=category,
                    amount=amount,
                    transaction_type=transaction_type,
                    description=descriptions[i].strip(),
                    date=dates[i]
                )

            except (
                ValueError,
                TypeError,
                InvalidOperation,
                Category.DoesNotExist,
                IndexError
            ):
                continue

        return redirect("transactions")

    return render(
        request,
        "tracker/calculator.html",
        {
            "categories": categories
        }
    )

@login_required
def reports(request):

    transactions = Transaction.objects.filter(
        user=request.user
    )

    month = request.GET.get('month')
    year = request.GET.get('year')

    if month:
        transactions = transactions.filter(
            date__month=month
        )

    if year:
        transactions = transactions.filter(
            date__year=year
        )

    total_income = transactions.filter(
        transaction_type='CREDIT'
    ).aggregate(
        Sum('amount')
    )['amount__sum'] or 0

    total_expenses = transactions.filter(
        transaction_type='DEBIT'
    ).aggregate(
        Sum('amount')
    )['amount__sum'] or 0

    savings = total_income - total_expenses

    category_data = (
    transactions
    .filter(transaction_type='DEBIT')
    .values('category__name')
    .annotate(total=Sum('amount'))
    .order_by('-total')
)
    category_labels = [
    item['category__name']
    for item in category_data
    ]

    category_amounts = [
        float(item['total'])
        for item in category_data
    ]
    monthly_data = (
    Transaction.objects
    .filter(user=request.user)
    .values('date__month', 'transaction_type')
    .annotate(total=Sum('amount'))
    .order_by('date__month')
)
    monthly_income = [0] * 12
    monthly_expenses = [0] * 12

    for item in monthly_data:

        month_index = item['date__month'] - 1

        if item['transaction_type'] == 'CREDIT':
            monthly_income[month_index] = float(item['total'])

        elif item['transaction_type'] == 'DEBIT':
            monthly_expenses[month_index] = float(item['total'])

    return render(
    request,
    'tracker/reports.html',
    {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'savings': savings,
        'selected_month': month,
        'selected_year': year,
        'category_data': category_data,
        'category_labels': category_labels,
        'category_amounts': category_amounts,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
    }
)




@login_required
def budget(request):

    # Get selected month and year
    month = request.GET.get('month')
    year = request.GET.get('year')

    today = date.today()

    # Default to current month/year
    if not month:
        month = today.month

    if not year:
        year = today.year

    month = int(month)
    year = int(year)

    # Get user's budget for selected month
    budget = Budget.objects.filter(
        user=request.user,
        month=month,
        year=year
    ).first()

    # Set or update budget
    if request.method == 'POST':

        amount = request.POST.get('amount', '').strip()

        try:
            amount = Decimal(amount)

            if amount <= 0:
                raise InvalidOperation

            Budget.objects.update_or_create(
                user=request.user,
                month=month,
                year=year,
                defaults={
                    'amount': amount
                }
            )

            return redirect(
                f'/budget/?month={month}&year={year}'
            )

        except (InvalidOperation, ValueError):
            pass

    # Get debit transactions for selected month
    expenses = Transaction.objects.filter(
        user=request.user,
        transaction_type='DEBIT',
        date__month=month,
        date__year=year
    )

    # Calculate total expenses
    total_expenses = expenses.aggregate(
        Sum('amount')
    )['amount__sum'] or Decimal('0')

    # Budget amount
    budget_amount = (
        budget.amount
        if budget
        else Decimal('0')
    )

    # Remaining budget
    remaining = budget_amount - total_expenses

    # Calculate percentage used
    if budget_amount > 0:
        percentage_used = (
            float(total_expenses) /
            float(budget_amount)
        ) * 100
    else:
        percentage_used = 0

    # Prevent progress bar from exceeding 100%
    progress_percentage = min(
        percentage_used,
        100
    )

    # Check if over budget
    over_budget = (
        total_expenses > budget_amount
        and budget_amount > 0
    )

    # Amount over budget
    amount_over_budget = abs(remaining)

    context = {
        'budget': budget,
        'budget_amount': budget_amount,
        'total_expenses': total_expenses,
        'remaining': remaining,
        'percentage_used': round(
            percentage_used,
            1
        ),
        'progress_percentage': progress_percentage,
        'over_budget': over_budget,
        'amount_over_budget': amount_over_budget,
        'selected_month': str(month),
        'selected_year': str(year),
    }

    return render(
        request,
        'tracker/budget.html',
        context
    )

@login_required
def savings_goals(request):

    goals = SavingsGoal.objects.filter(
        user=request.user
    ).order_by('-created_at')

    # Create new goal
    if request.method == 'POST':

        name = request.POST.get('name', '').strip()
        target_amount = request.POST.get('target_amount', '').strip()
        saved_amount = request.POST.get('saved_amount', '0').strip()
        target_date = request.POST.get('target_date', '').strip()

        if name and target_amount:

            try:
                from decimal import Decimal

                target_amount = Decimal(target_amount)
                saved_amount = Decimal(saved_amount or '0')

                if target_amount > 0 and saved_amount >= 0:

                    if saved_amount <= target_amount:

                        SavingsGoal.objects.create(
                            user=request.user,
                            name=name,
                            target_amount=target_amount,
                            saved_amount=saved_amount,
                            target_date=target_date or None
                        )

                        return redirect('savings_goals')

            except:
                pass

    # Prepare goal information
    goal_data = []

    for goal in goals:

        remaining = (
            goal.target_amount -
            goal.saved_amount
        )

        if goal.target_amount > 0:

            percentage = (
                float(goal.saved_amount) /
                float(goal.target_amount)
            ) * 100

        else:

            percentage = 0

        percentage = min(
            percentage,
            100
        )

        completed = (
            goal.saved_amount >=
            goal.target_amount
        )

        goal_data.append({
            'goal': goal,
            'remaining': remaining,
            'percentage': round(percentage, 1),
            'completed': completed,
        })

    return render(
        request,
        'tracker/savings_goals.html',
        {
            'goal_data': goal_data,
        }
    )


@login_required
def add_savings(request, id):

    if request.method == 'POST':

        from decimal import Decimal

        goal = SavingsGoal.objects.get(
            id=id,
            user=request.user
        )

        amount = request.POST.get(
            'amount',
            ''
        ).strip()

        try:

            amount = Decimal(amount)

            if amount > 0:

                new_saved_amount = (
                    goal.saved_amount +
                    amount
                )

                # Don't allow saving more than target
                if new_saved_amount <= goal.target_amount:

                    goal.saved_amount = new_saved_amount
                    goal.save()

        except:
            pass

    return redirect('savings_goals')


@login_required
def delete_savings_goal(request, id):

    if request.method == 'POST':

        goal = SavingsGoal.objects.get(
            id=id,
            user=request.user
        )

        goal.delete()

    return redirect('savings_goals')


@login_required
def mark_loan_paid(request, id):

    if request.method == 'POST':

        loan = Loan.objects.get(
            id=id,
            user=request.user
        )

        loan.status = 'PAID'
        loan.save()

    return redirect('loans')

@login_required
def delete_loan(request, id):

    if request.method == 'POST':

        loan = Loan.objects.get(
            id=id,
            user=request.user
        )

        loan.delete()

    return redirect('loans')

@login_required
def loans(request):

    from decimal import Decimal
    from datetime import date

    # =============================
    # ADD NEW LOAN
    # =============================

    if request.method == 'POST':

        person_name = request.POST.get(
            'person_name',
            ''
        ).strip()

        amount = request.POST.get(
            'amount',
            ''
        ).strip()

        loan_type = request.POST.get('loan_type')

        due_date = request.POST.get('due_date')

        description = request.POST.get(
            'description',
            ''
        ).strip()

        try:

            amount = Decimal(amount)

            if (
                person_name
                and amount > 0
                and loan_type in ['BORROWED', 'LENT']
            ):

                Loan.objects.create(
                    user=request.user,
                    person_name=person_name,
                    amount=amount,
                    loan_type=loan_type,
                    due_date=due_date or None,
                    description=description
                )

                return redirect('loans')

        except (ValueError, TypeError, InvalidOperation):

            pass


    # =============================
    # ALL LOANS
    # =============================

    all_loans = Loan.objects.filter(
        user=request.user
    ).order_by('-created_at')


    # =============================
    # SUMMARY
    # =============================

    total_borrowed = sum(
        (
            loan.amount
            for loan in all_loans
            if loan.loan_type == 'BORROWED'
        ),
        Decimal('0')
    )


    total_lent = sum(
        (
            loan.amount
            for loan in all_loans
            if loan.loan_type == 'LENT'
        ),
        Decimal('0')
    )


    total_pending = sum(
        (
            loan.remaining_amount
            for loan in all_loans
            if loan.status == 'PENDING'
        ),
        Decimal('0')
    )


    total_paid = sum(
        (
            loan.paid_amount
            for loan in all_loans
        ),
        Decimal('0')
    )


    # =============================
    # FILTER
    # =============================

    selected_filter = request.GET.get(
        'filter',
        'ALL'
    )


    filtered_loans = all_loans


    if selected_filter == 'BORROWED':

        filtered_loans = filtered_loans.filter(
            loan_type='BORROWED'
        )


    elif selected_filter == 'LENT':

        filtered_loans = filtered_loans.filter(
            loan_type='LENT'
        )


    elif selected_filter == 'PENDING':

        filtered_loans = filtered_loans.filter(
            status='PENDING'
        )


    elif selected_filter == 'PAID':

        filtered_loans = filtered_loans.filter(
            status='PAID'
        )


    elif selected_filter == 'OVERDUE':

        filtered_loans = filtered_loans.filter(
            status='PENDING',
            due_date__lt=date.today()
        )


    # =============================
    # SEARCH
    # =============================

    search_query = request.GET.get(
        'search',
        ''
    ).strip()


    if search_query:

        filtered_loans = filtered_loans.filter(
            Q(person_name__icontains=search_query)
            |
            Q(description__icontains=search_query)
    )


    # =============================
    # DUE DATE INFORMATION
    # =============================

    today = date.today()

    loan_data = []


    for loan in filtered_loans:

        due_status = None
        due_class = None


        if loan.due_date and loan.status == 'PENDING':

            days_remaining = (
                loan.due_date - today
            ).days


            if days_remaining < 0:

                days = abs(days_remaining)

                due_status = (
                    f'Overdue by {days} '
                    f'day{"s" if days != 1 else ""}'
                )

                due_class = 'overdue'


            elif days_remaining == 0:

                due_status = 'Due today'

                due_class = 'due-today'


            elif days_remaining == 1:

                due_status = 'Due tomorrow'

                due_class = 'due-soon'


            elif days_remaining <= 7:

                due_status = (
                    f'Due in {days_remaining} days'
                )

                due_class = 'due-soon'


            else:

                due_status = (
                    f'Due in {days_remaining} days'
                )

                due_class = 'due-normal'


        loan_data.append({
            'loan': loan,
            'due_status': due_status,
            'due_class': due_class,
        })


    return render(
        request,
        'tracker/loans.html',
        {
            'loans': filtered_loans,
            'loan_data': loan_data,

            'total_borrowed': total_borrowed,
            'total_lent': total_lent,
            'total_pending': total_pending,
            'total_paid': total_paid,

            'selected_filter': selected_filter,

            'search_query': search_query,
        }
    )


@login_required
def add_loan_payment(request, id):

    if request.method == 'POST':

        from decimal import Decimal

        loan = Loan.objects.get(
            id=id,
            user=request.user
        )

        amount = request.POST.get(
            'amount',
            ''
        ).strip()

        try:

            amount = Decimal(amount)

            if amount <= 0:
                return redirect('loans')

            remaining = (
                loan.amount -
                loan.paid_amount
            )

            if amount > remaining:
                amount = remaining

            loan.paid_amount += amount

            if loan.paid_amount >= loan.amount:
                loan.paid_amount = loan.amount
                loan.status = 'PAID'

            loan.save()

        except (ValueError, TypeError, InvalidOperation):
            pass

    return redirect('loans')


@login_required
def edit_loan(request, id):

    loan = Loan.objects.get(
        id=id,
        user=request.user
    )

    if request.method == 'POST':

        person_name = request.POST.get(
            'person_name',
            ''
        ).strip()

        amount = request.POST.get(
            'amount',
            ''
        ).strip()

        loan_type = request.POST.get(
            'loan_type'
        )

        due_date = request.POST.get(
            'due_date'
        )

        description = request.POST.get(
            'description',
            ''
        ).strip()

        try:

            amount = Decimal(amount)

            if (
                person_name
                and amount > 0
                and loan_type in ['BORROWED', 'LENT']
            ):

                # Don't allow the new total
                # to be less than what was already paid.
                if amount < loan.paid_amount:
                    return render(
                        request,
                        'tracker/edit_loan.html',
                        {
                            'loan': loan,
                            'error': (
                                'Loan amount cannot be less '
                                'than the amount already paid.'
                            )
                        }
                    )

                loan.person_name = person_name
                loan.amount = amount
                loan.loan_type = loan_type
                loan.due_date = due_date or None
                loan.description = description

                if loan.paid_amount >= loan.amount:
                    loan.paid_amount = loan.amount
                    loan.status = 'PAID'
                else:
                    loan.status = 'PENDING'

                loan.save()

                return redirect('loans')

        except (ValueError, TypeError, InvalidOperation):
            pass

    return render(
        request,
        'tracker/edit_loan.html',
        {
            'loan': loan
        }
    )