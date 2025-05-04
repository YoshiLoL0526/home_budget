import calendar
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    ListView,
)
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum, Count, Avg, DateField
from django.db.models.functions import Cast
from datetime import datetime, timedelta
import json
import pytz

from .models import SavedReport
from .forms import ReportFilterForm, SaveReportForm
from .utils import (
    get_date_range,
    get_expenses_by_category,
    get_expense_trend,
    generate_chart_data,
    export_to_excel,
    export_to_pdf,
)
from operations.models import Operation


@login_required
def dashboard(request):
    """Main dashboard view with summary widgets"""
    # Get user's timezone
    user_timezone = request.user.userprofile.timezone or "UTC"
    current_tz = pytz.timezone(user_timezone)

    # Get current date in user's timezone
    today = timezone.now().astimezone(current_tz).date()
    start_of_month = today.replace(day=1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(
        days=1
    )

    # Convert dates to datetime with user's timezone for database queries
    start_of_month = timezone.datetime.combine(
        start_of_month, timezone.datetime.min.time()
    )
    start_of_month = current_tz.localize(start_of_month)

    end_of_month = timezone.datetime.combine(end_of_month, timezone.datetime.max.time())
    end_of_month = current_tz.localize(end_of_month)

    # Monthly totals
    monthly_expenses = (
        Operation.objects.filter(
            user=request.user,
            date__gte=start_of_month,
            date__lte=end_of_month,
            category__type="gasto",
        ).aggregate(Sum("amount"))["amount__sum"]
        or 0
    )

    monthly_income = (
        Operation.objects.filter(
            user=request.user,
            date__gte=start_of_month,
            date__lte=end_of_month,
            category__type="ingreso",
        ).aggregate(Sum("amount"))["amount__sum"]
        or 0
    )

    # Calculate balance
    monthly_balance = monthly_income - monthly_expenses

    # Get last month data for comparison
    last_month_end = timezone.datetime.combine(
        start_of_month.date() - timedelta(days=1), timezone.datetime.max.time()
    )
    last_month_end = current_tz.localize(last_month_end)

    last_month_start = timezone.datetime.combine(
        last_month_end.date().replace(day=1), timezone.datetime.min.time()
    )
    last_month_start = current_tz.localize(last_month_start)

    last_month_expenses = (
        Operation.objects.filter(
            user=request.user,
            date__gte=last_month_start,
            date__lte=last_month_end,
            category__type="gasto",
        ).aggregate(Sum("amount"))["amount__sum"]
        or 0
    )

    last_month_income = (
        Operation.objects.filter(
            user=request.user,
            date__gte=last_month_start,
            date__lte=last_month_end,
            category__type="ingreso",
        ).aggregate(Sum("amount"))["amount__sum"]
        or 0
    )

    # Calculate percentage changes
    expense_change_pct = (
        ((monthly_expenses - last_month_expenses) / last_month_expenses * 100)
        if last_month_expenses > 0
        else 0
    )
    income_change_pct = (
        ((monthly_income - last_month_income) / last_month_income * 100)
        if last_month_income > 0
        else 0
    )

    # Top expense categories
    top_expenses = get_expenses_by_category(request.user, start_of_month, end_of_month)[
        :5
    ]  # Get top 5

    # Monthly income categories
    income_by_category = (
        Operation.objects.filter(
            user=request.user,
            date__gte=start_of_month,
            date__lte=end_of_month,
            category__type="ingreso",
        )
        .values("category__name", "category__color")
        .annotate(total=Sum("amount"), count=Count("id"), avg=Avg("amount"))
        .order_by("-total")
    )

    # Daily expense trend
    daily_expenses = (
        Operation.objects.filter(
            user=request.user,
            date__gte=start_of_month,
            date__lte=end_of_month,
            category__type="gasto",
        )
        .values("date")
        .annotate(total=Sum("amount"))
        .order_by("date")
    )

    daily_income = (
        Operation.objects.filter(
            user=request.user,
            date__gte=start_of_month,
            date__lte=end_of_month,
            category__type="ingreso",
        )
        .values("date")
        .annotate(total=Sum("amount"))
        .order_by("date")
    )

    # Create daily trend data
    daily_trend_data = []
    date_range = [
        (start_of_month + timedelta(days=i))
        for i in range((end_of_month - start_of_month).days + 1)
    ]

    expense_dict = {item["date"]: item["total"] for item in daily_expenses}
    income_dict = {item["date"]: item["total"] for item in daily_income}

    for date in date_range:
        daily_trend_data.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "expenses": expense_dict.get(date.date(), 0),
                "income": income_dict.get(date.date(), 0),
            }
        )

    # Prepare chart data
    pie_chart_data = generate_chart_data(top_expenses, chart_type="pie")
    income_pie_chart_data = generate_chart_data(income_by_category, chart_type="pie")

    # Income vs Expenses
    income_expense_data = [
        {
            "category__name": str(_("Ingresos")),
            "category__color": "#28a745",
            "total": monthly_income,
        },
        {
            "category__name": str(_("Gastos")),
            "category__color": "#dc3545",
            "total": monthly_expenses,
        },
    ]
    income_expense_chart_data = generate_chart_data(
        income_expense_data, chart_type="pie"
    )

    # Prepare daily trend chart data
    trend_labels = [item["date"] for item in daily_trend_data]
    expense_values = [float(item["expenses"]) for item in daily_trend_data]
    income_values = [float(item["income"]) for item in daily_trend_data]

    daily_trend_chart_data = {
        "labels": trend_labels,
        "datasets": [
            {
                "label": "Gastos",
                "data": expense_values,
                "borderColor": "#dc3545",
                "backgroundColor": "rgba(220, 53, 69, 0.1)",
                "fill": True,
                "tension": 0.4,
            },
            {
                "label": "Ingresos",
                "data": income_values,
                "borderColor": "#28a745",
                "backgroundColor": "rgba(40, 167, 69, 0.1)",
                "fill": True,
                "tension": 0.4,
            },
        ],
    }

    # Check if user has a monthly budget
    user_profile = request.user.userprofile
    monthly_budget = user_profile.monthly_budget
    budget_percentage = 0
    days_left = (end_of_month.date() - today).days
    daily_budget_left = 0

    if monthly_budget:
        budget_percentage = (1 - monthly_expenses / monthly_budget) * 100
        if days_left > 0:
            remaining_budget = monthly_budget - monthly_expenses
            daily_budget_left = (
                remaining_budget / days_left if remaining_budget > 0 else 0
            )

    context = {
        "monthly_expenses": monthly_expenses,
        "monthly_income": monthly_income,
        "monthly_balance": monthly_balance,
        "expense_change_pct": expense_change_pct,
        "income_change_pct": income_change_pct,
        "top_expenses": top_expenses,
        "income_by_category": income_by_category,
        "pie_chart_data": json.dumps(pie_chart_data),
        "income_pie_chart_data": json.dumps(income_pie_chart_data),
        "trend_chart_data": json.dumps(daily_trend_chart_data),
        "income_expense_chart_data": json.dumps(income_expense_chart_data),
        "monthly_budget": monthly_budget,
        "budget_percentage": budget_percentage,
        "days_left_in_month": days_left,
        "daily_budget_left": daily_budget_left,
        "currency": user_profile.currency,
        "start_date": start_of_month,
        "end_date": end_of_month,
    }

    return render(request, "dashboard.html", context)


@login_required
def monthly_report(request):
    """Detailed monthly report with analysis and projections"""

    # Get user's timezone
    user_timezone = request.user.userprofile.timezone or "UTC"
    current_tz = pytz.timezone(user_timezone)

    # Get current date in user's timezone
    today = timezone.now().astimezone(current_tz).date()

    # Get requested month/year or default to current
    month = int(request.GET.get("month", today.month))
    year = int(request.GET.get("year", today.year))

    # Get month name
    month_name = calendar.month_name[month]

    # Create datetime objects for start and end of month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)

    # Add timezone info
    start_of_month = timezone.datetime.combine(start_date, timezone.datetime.min.time())
    start_of_month = current_tz.localize(start_of_month)

    end_of_month = timezone.datetime.combine(end_date, timezone.datetime.max.time())
    end_of_month = current_tz.localize(end_of_month)

    # Generate months and years for the selector
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]

    # Get last 5 years and next year
    current_year = today.year
    years = list(range(current_year - 5, current_year + 2))

    # Monthly totals
    monthly_expenses = (
        Operation.objects.filter(
            user=request.user,
            date__gte=start_of_month,
            date__lte=end_of_month,
            category__type="gasto",
        ).aggregate(Sum("amount"))["amount__sum"]
        or 0
    )

    monthly_income = (
        Operation.objects.filter(
            user=request.user,
            date__gte=start_of_month,
            date__lte=end_of_month,
            category__type="ingreso",
        ).aggregate(Sum("amount"))["amount__sum"]
        or 0
    )

    # Calculate balance and savings rate
    monthly_balance = monthly_income - monthly_expenses
    savings_rate = (monthly_balance / monthly_income * 100) if monthly_income > 0 else 0

    # Get last month data for comparison
    if month == 1:
        last_month = 12
        last_year = year - 1
    else:
        last_month = month - 1
        last_year = year

    last_month_start = datetime(last_year, last_month, 1)
    if last_month == 12:
        last_month_end = datetime(last_year + 1, 1, 1) - timedelta(days=1)
    else:
        last_month_end = datetime(last_year, last_month + 1, 1) - timedelta(days=1)

    last_month_start = timezone.datetime.combine(
        last_month_start, timezone.datetime.min.time()
    )
    last_month_start = current_tz.localize(last_month_start)

    last_month_end = timezone.datetime.combine(
        last_month_end, timezone.datetime.max.time()
    )
    last_month_end = current_tz.localize(last_month_end)

    last_month_expenses = (
        Operation.objects.filter(
            user=request.user,
            date__gte=last_month_start,
            date__lte=last_month_end,
            category__type="gasto",
        ).aggregate(Sum("amount"))["amount__sum"]
        or 0
    )

    last_month_income = (
        Operation.objects.filter(
            user=request.user,
            date__gte=last_month_start,
            date__lte=last_month_end,
            category__type="ingreso",
        ).aggregate(Sum("amount"))["amount__sum"]
        or 0
    )

    # Calculate percentage changes
    expense_change_pct = (
        ((monthly_expenses - last_month_expenses) / last_month_expenses * 100)
        if last_month_expenses > 0
        else 0
    )
    income_change_pct = (
        ((monthly_income - last_month_income) / last_month_income * 100)
        if last_month_income > 0
        else 0
    )

    # For progress bars, we need absolute percentage values capped at 100%
    expense_change_abs_pct = min(abs(expense_change_pct), 100)
    income_change_abs_pct = min(abs(income_change_pct), 100)

    # Get expenses by category with percentage of total
    expenses_by_category = get_expenses_by_category(
        request.user, start_of_month, end_of_month
    )

    # Add percentage calculation to each category
    for expense in expenses_by_category:
        expense["percentage"] = (
            (expense["total"] / monthly_expenses * 100) if monthly_expenses > 0 else 0
        )

    # Get top 10 expenses
    top_expenses = expenses_by_category[:10]

    # Get budget information
    user_profile = request.user.userprofile
    monthly_budget = user_profile.monthly_budget
    budget_remaining = monthly_budget - monthly_expenses if monthly_budget else 0
    budget_used_percentage = (
        (monthly_expenses / monthly_budget * 100) if monthly_budget else 0
    )
    days_left = (
        (end_of_month.date() - today).days if end_of_month.date() >= today else 0
    )
    days_left = max(days_left, 1)  # Ensure at least 1 day
    daily_budget_left = (budget_remaining / days_left) if budget_remaining > 0 else 0

    # Get daily expenses and income
    daily_expenses = (
        Operation.objects.filter(
            user=request.user,
            date__gte=start_of_month,
            date__lte=end_of_month,
            category__type="gasto",
        )
        .annotate(day=Cast("date", output_field=DateField()))
        .values("day")
        .annotate(total=Sum("amount"))
        .order_by("day")
    )

    daily_income = (
        Operation.objects.filter(
            user=request.user,
            date__gte=start_of_month,
            date__lte=end_of_month,
            category__type="ingreso",
        )
        .annotate(day=Cast("date", output_field=DateField()))
        .values("day")
        .annotate(total=Sum("amount"))
        .order_by("day")
    )

    # Create daily trend data
    daily_trend_data = []
    date_range = [
        (start_of_month + timedelta(days=i))
        for i in range((end_of_month - start_of_month).days + 1)
    ]

    expense_dict = {item["day"]: item["total"] for item in daily_expenses}
    income_dict = {item["day"]: item["total"] for item in daily_income}

    for date in date_range:
        daily_trend_data.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "expenses": expense_dict.get(date.date(), 0),
                "income": income_dict.get(date.date(), 0),
            }
        )

    # Get top spending days with their main category
    top_spending_days = []
    for day_data in sorted(daily_expenses, key=lambda x: x["total"], reverse=True)[:5]:
        day = day_data["day"]

        # Get top category for this day
        day_top_category = (
            Operation.objects.filter(
                user=request.user,
                date=day,
                category__type="gasto",
            )
            .values("category__name", "category__color")
            .annotate(total=Sum("amount"))
            .order_by("-total")
            .first()
        )

        top_spending_days.append(
            {
                "date": day,
                "total": day_data["total"],
                "percentage": (
                    (day_data["total"] / monthly_expenses * 100)
                    if monthly_expenses > 0
                    else 0
                ),
                "top_category": (
                    day_top_category["category__name"] if day_top_category else None
                ),
                "top_category_color": (
                    day_top_category["category__color"] if day_top_category else None
                ),
            }
        )

    # Get 6-month expense trend (including current month)
    six_month_data = []
    for i in range(5, -1, -1):
        if month - i <= 0:
            trend_month = month - i + 12
            trend_year = year - 1
        else:
            trend_month = month - i
            trend_year = year

        trend_month_name = calendar.month_name[trend_month]

        # First day of month
        trend_start = datetime(trend_year, trend_month, 1)
        # Last day of month
        if trend_month == 12:
            trend_end = datetime(trend_year + 1, 1, 1) - timedelta(days=1)
        else:
            trend_end = datetime(trend_year, trend_month + 1, 1) - timedelta(days=1)

        trend_start = timezone.datetime.combine(
            trend_start, timezone.datetime.min.time()
        )
        trend_start = current_tz.localize(trend_start)

        trend_end = timezone.datetime.combine(trend_end, timezone.datetime.max.time())
        trend_end = current_tz.localize(trend_end)

        trend_expenses = (
            Operation.objects.filter(
                user=request.user,
                date__gte=trend_start,
                date__lte=trend_end,
                category__type="gasto",
            ).aggregate(Sum("amount"))["amount__sum"]
            or 0
        )

        six_month_data.append(
            {
                "month": f"{trend_month_name[:3]} {trend_year}",
                "expenses": trend_expenses,
            }
        )

    # Project next month expenses
    # Simple projection based on average of last 3 months
    recent_months_expenses = []
    for i in range(2, -1, -1):  # Last 3 months including current
        if month - i <= 0:
            proj_month = month - i + 12
            proj_year = year - 1
        else:
            proj_month = month - i
            proj_year = year

        proj_start = datetime(proj_year, proj_month, 1)
        if proj_month == 12:
            proj_end = datetime(proj_year + 1, 1, 1) - timedelta(days=1)
        else:
            proj_end = datetime(proj_year, proj_month + 1, 1) - timedelta(days=1)

        proj_start = timezone.datetime.combine(proj_start, timezone.datetime.min.time())
        proj_start = current_tz.localize(proj_start)

        proj_end = timezone.datetime.combine(proj_end, timezone.datetime.max.time())
        proj_end = current_tz.localize(proj_end)

        proj_expenses = (
            Operation.objects.filter(
                user=request.user,
                date__gte=proj_start,
                date__lte=proj_end,
                category__type="gasto",
            ).aggregate(Sum("amount"))["amount__sum"]
            or 0
        )

        recent_months_expenses.append(proj_expenses)

    # Projected expenses with a slight trend weighting
    if len(recent_months_expenses) >= 3:
        projected_expenses = (
            0.2 * float(recent_months_expenses[0])
            + 0.3 * float(recent_months_expenses[1])
            + 0.5 * float(recent_months_expenses[2])
        )
    else:
        projected_expenses = monthly_expenses

    # Calculate percentage vs income
    projection_vs_income_pct = (
        (projected_expenses / float(monthly_income) * 100) if monthly_income > 0 else 0
    )

    # Generate recommendations based on the data
    recommendations = []

    # Check if expenses exceed income
    if monthly_expenses > monthly_income:
        recommendations.append(
            {
                "title": _("Reducir gastos"),
                "description": _(
                    "Tus gastos superan tus ingresos este mes. Considera recortar gastos no esenciales."
                ),
                "icon": "fa-exclamation-triangle",
                "color": "warning",
            }
        )

    # Check if there's a category that takes up more than 40% of expenses
    for category in top_expenses:
        if category["percentage"] > 40:
            recommendations.append(
                {
                    "title": _("Alta concentración de gastos"),
                    "description": _(
                        f'La categoría {category["category__name"]} representa el {category["percentage"]:.1f}% de tus gastos.'
                    ),
                    "icon": "fa-chart-pie",
                    "color": "info",
                }
            )
            break

    # Check for expense increase
    if expense_change_pct > 15:
        recommendations.append(
            {
                "title": _("Aumento de gastos"),
                "description": _(
                    f"Tus gastos han aumentado un {expense_change_pct:.1f}% respecto al mes anterior."
                ),
                "icon": "fa-arrow-trend-up",
                "color": "danger",
            }
        )

    # Check for savings rate
    if savings_rate < 10 and savings_rate >= 0:
        recommendations.append(
            {
                "title": _("Tasa de ahorro baja"),
                "description": _(
                    "Tu tasa de ahorro es menor al 10%. Intenta aumentarla para mejorar tu situación financiera."
                ),
                "icon": "fa-piggy-bank",
                "color": "warning",
            }
        )
    elif savings_rate >= 20:
        recommendations.append(
            {
                "title": _("¡Buen trabajo ahorrando!"),
                "description": _(
                    f"Estás ahorrando el {savings_rate:.1f}% de tus ingresos. ¡Sigue así!"
                ),
                "icon": "fa-award",
                "color": "success",
            }
        )

    # Prepare chart data
    pie_chart_data = generate_chart_data(top_expenses, chart_type="pie")

    # Prepare daily trend chart data
    trend_labels = [item["date"] for item in daily_trend_data]
    expense_values = [float(item["expenses"]) for item in daily_trend_data]
    income_values = [float(item["income"]) for item in daily_trend_data]

    daily_trend_chart_data = {
        "labels": trend_labels,
        "datasets": [
            {
                "label": "Gastos",
                "data": expense_values,
                "borderColor": "#dc3545",
                "backgroundColor": "rgba(220, 53, 69, 0.1)",
                "fill": True,
                "tension": 0.4,
            },
            {
                "label": "Ingresos",
                "data": income_values,
                "borderColor": "#28a745",
                "backgroundColor": "rgba(40, 167, 69, 0.1)",
                "fill": True,
                "tension": 0.4,
            },
        ],
    }

    # Six month trend data
    six_month_trend_data = {
        "labels": [item["month"] for item in six_month_data],
        "datasets": [
            {
                "label": "Gastos mensuales",
                "data": [float(item["expenses"]) for item in six_month_data],
                "backgroundColor": "rgba(54, 162, 235, 0.7)",
            }
        ],
    }

    context = {
        "month": month,
        "year": year,
        "month_name": month_name,
        "months": months,
        "years": years,
        "monthly_expenses": monthly_expenses,
        "monthly_income": monthly_income,
        "monthly_balance": monthly_balance,
        "savings_rate": savings_rate,
        "expense_change_pct": expense_change_pct,
        "income_change_pct": income_change_pct,
        "expense_change_abs_pct": expense_change_abs_pct,
        "income_change_abs_pct": income_change_abs_pct,
        "top_expenses": top_expenses,
        "top_spending_days": top_spending_days,
        "monthly_budget": monthly_budget,
        "budget_remaining": budget_remaining,
        "budget_used_percentage": budget_used_percentage,
        "days_left_in_month": days_left,
        "daily_budget_left": daily_budget_left,
        "projected_expenses": projected_expenses,
        "projection_vs_income_pct": projection_vs_income_pct,
        "recommendations": recommendations,
        "pie_chart_data": json.dumps(pie_chart_data),
        "daily_trend_chart_data": json.dumps(daily_trend_chart_data),
        "six_month_trend_data": json.dumps(six_month_trend_data),
    }
    return render(request, "monthly_report.html", context)


@login_required
def export_monthly_report(request):
    """Export monthly report data to Excel or PDF"""
    export_format = request.GET.get("format", "excel")
    month = int(request.GET.get("month", timezone.now().month))
    year = int(request.GET.get("year", timezone.now().year))

    # Get user's timezone
    user_timezone = request.user.userprofile.timezone or "UTC"
    current_tz = pytz.timezone(user_timezone)

    # Create datetime objects for start and end of month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)

    # Add timezone info
    start_of_month = timezone.datetime.combine(start_date, timezone.datetime.min.time())
    start_of_month = current_tz.localize(start_of_month)

    end_of_month = timezone.datetime.combine(end_date, timezone.datetime.max.time())
    end_of_month = current_tz.localize(end_of_month)

    # Get month name
    month_name = calendar.month_name[month]

    # Prepare data for export
    expenses_by_category = get_expenses_by_category(
        request.user, start_of_month, end_of_month
    )

    # Monthly totals
    monthly_expenses = (
        Operation.objects.filter(
            user=request.user,
            date__gte=start_of_month,
            date__lte=end_of_month,
            category__type="gasto",
        ).aggregate(Sum("amount"))["amount__sum"]
        or 0
    )

    monthly_income = (
        Operation.objects.filter(
            user=request.user,
            date__gte=start_of_month,
            date__lte=end_of_month,
            category__type="ingreso",
        ).aggregate(Sum("amount"))["amount__sum"]
        or 0
    )

    monthly_balance = monthly_income - monthly_expenses

    # Format data for export
    report_data = []

    # Summary row
    report_data.append(
        {
            "Sección": "Resumen Mensual",
            "Concepto": "Mes y año",
            "Valor": f"{month_name} {year}",
            "Adicional": "",
        }
    )
    report_data.append(
        {
            "Sección": "Resumen Mensual",
            "Concepto": "Ingresos",
            "Valor": monthly_income,
            "Adicional": request.user.userprofile.currency,
        }
    )
    report_data.append(
        {
            "Sección": "Resumen Mensual",
            "Concepto": "Gastos",
            "Valor": monthly_expenses,
            "Adicional": request.user.userprofile.currency,
        }
    )
    report_data.append(
        {
            "Sección": "Resumen Mensual",
            "Concepto": "Balance",
            "Valor": monthly_balance,
            "Adicional": request.user.userprofile.currency,
        }
    )

    # Category breakdown
    for category in expenses_by_category:
        report_data.append(
            {
                "Sección": "Gastos por Categoría",
                "Concepto": category["category__name"],
                "Valor": category["total"],
                "Adicional": (
                    f"{(category['total'] / monthly_expenses * 100):.1f}% del total"
                    if monthly_expenses > 0
                    else "0.0%"
                ),
            }
        )

    # Daily expenses
    daily_expenses = (
        Operation.objects.filter(
            user=request.user,
            date__gte=start_of_month,
            date__lte=end_of_month,
            category__type="gasto",
        )
        .annotate(day=Cast("date", output_field=DateField()))
        .values("day")
        .annotate(total=Sum("amount"))
        .order_by("day")
    )

    for day_data in daily_expenses:
        report_data.append(
            {
                "Sección": "Gastos Diarios",
                "Concepto": day_data["day"].strftime("%d/%m/%Y"),
                "Valor": day_data["total"],
                "Adicional": request.user.userprofile.currency,
            }
        )

    # Set filename
    filename = f"Reporte_Mensual_{month_name}_{year}"

    if export_format == "excel":
        # Export to Excel
        output = export_to_excel(report_data, f"Reporte {month_name} {year}")
        response = HttpResponse(
            output.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
        return response
    else:
        # Export to PDF
        output = export_to_pdf(report_data)
        response = HttpResponse(output.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
        return response


@login_required
def annual_report(request):
    """Detailed monthly report with analysis and projections"""

    return render(request, "Not implemented yet")
