from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    ListView,
)
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum, Count, Avg
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
    """Monthly report view with filtering options"""
    today = timezone.now().date()
    year = request.GET.get("year", today.year)
    month = request.GET.get("month", today.month)

    try:
        year = int(year)
        month = int(month)
    except ValueError:
        year = today.year
        month = today.month

    start_date, end_date = get_date_range("month", request.user, year=year, month=month)

    # Initialize form
    form = ReportFilterForm(request.GET or None, user=request.user)

    # Apply filters if form is valid
    categories = None
    if request.GET and form.is_valid():
        start_date = form.cleaned_data.get("start_date") or start_date
        end_date = form.cleaned_data.get("end_date") or end_date
        categories = form.cleaned_data.get("categories")

    # Get expenses data
    expenses_by_category = get_expenses_by_category(
        request.user, start_date, end_date, categories
    )

    expense_trend = get_expense_trend(
        request.user, start_date, end_date, period="month"
    )

    # Prepare chart data
    pie_chart_data = generate_chart_data(expenses_by_category, chart_type="pie")
    bar_chart_data = generate_chart_data(expenses_by_category, chart_type="bar")
    trend_chart_data = generate_chart_data(expense_trend, chart_type="line")

    # Calculate totals
    total_expenses = sum(float(item["total"]) for item in expenses_by_category)

    context = {
        "form": form,
        "expenses_by_category": expenses_by_category,
        "pie_chart_data": json.dumps(pie_chart_data),
        "bar_chart_data": json.dumps(bar_chart_data),
        "trend_chart_data": json.dumps(trend_chart_data),
        "total_expenses": total_expenses,
        "start_date": start_date,
        "end_date": end_date,
        "year": year,
        "month": month,
        "currency": request.user.userprofile.currency,
        "save_report_form": SaveReportForm(),
    }

    # Handle export requests
    if "export" in request.GET:
        export_format = request.GET.get("export")
        report_data = [
            {
                "category": item["category__name"],
                "amount": float(item["total"]),
                "count": item["count"],
                "average": float(item["avg"]),
            }
            for item in expenses_by_category
        ]

        if export_format == "excel":
            output = export_to_excel(report_data, "monthly_report.xlsx")
            response = HttpResponse(
                output.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = (
                f"attachment; filename=monthly_report_{year}_{month}.xlsx"
            )
            return response

        elif export_format == "pdf":
            output = export_to_pdf(
                report_data, f"Monthly Report {year}-{month}", "monthly_report.pdf"
            )
            response = HttpResponse(output.read(), content_type="application/pdf")
            response["Content-Disposition"] = (
                f"attachment; filename=monthly_report_{year}_{month}.pdf"
            )
            return response

    return render(request, "monthly_report.html", context)


@login_required
def annual_report(request):
    """Annual report view with yearly statistics"""
    today = timezone.now().date()
    year = request.GET.get("year", today.year)

    try:
        year = int(year)
    except ValueError:
        year = today.year

    start_date, end_date = get_date_range("year", request.user, year=year)

    # Initialize form
    form = ReportFilterForm(request.GET or None, user=request.user)

    # Apply filters if form is valid
    categories = None
    if request.GET and form.is_valid():
        start_date = form.cleaned_data.get("start_date") or start_date
        end_date = form.cleaned_data.get("end_date") or end_date
        categories = form.cleaned_data.get("categories")

    # Get expenses data
    expenses_by_category = get_expenses_by_category(
        request.user, start_date, end_date, categories
    )

    # Get monthly breakdown
    expense_trend = get_expense_trend(
        request.user, start_date, end_date, period="month"
    )

    # Prepare chart data
    pie_chart_data = generate_chart_data(expenses_by_category, chart_type="pie")
    bar_chart_data = generate_chart_data(expenses_by_category, chart_type="bar")
    trend_chart_data = generate_chart_data(expense_trend, chart_type="line")

    # Calculate totals
    total_expenses = sum(float(item["total"]) for item in expenses_by_category)

    context = {
        "form": form,
        "expenses_by_category": expenses_by_category,
        "expense_trend": expense_trend,
        "pie_chart_data": json.dumps(pie_chart_data),
        "bar_chart_data": json.dumps(bar_chart_data),
        "trend_chart_data": json.dumps(trend_chart_data),
        "total_expenses": total_expenses,
        "start_date": start_date,
        "end_date": end_date,
        "year": year,
        "currency": request.user.userprofile.currency,
        "save_report_form": SaveReportForm(),
    }

    # Handle export requests
    if "export" in request.GET:
        export_format = request.GET.get("export")
        report_data = [
            {
                "category": item["category__name"],
                "amount": float(item["total"]),
                "count": item["count"],
                "average": float(item["avg"]),
            }
            for item in expenses_by_category
        ]

        if export_format == "excel":
            output = export_to_excel(report_data, "annual_report.xlsx")
            response = HttpResponse(
                output.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = (
                f"attachment; filename=annual_report_{year}.xlsx"
            )
            return response

        elif export_format == "pdf":
            output = export_to_pdf(
                report_data, f"Annual Report {year}", "annual_report.pdf"
            )
            response = HttpResponse(output.read(), content_type="application/pdf")
            response["Content-Disposition"] = (
                f"attachment; filename=annual_report_{year}.pdf"
            )
            return response

    return render(request, "annual_report.html", context)


@login_required
def save_report(request):
    """Save a report configuration for future access"""
    if request.method == "POST":
        form = SaveReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user

            # Get filter parameters
            start_date = request.POST.get("start_date")
            end_date = request.POST.get("end_date")
            categories = request.POST.getlist("categories")

            # Save filter parameters
            report.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            report.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            report.filters = {"categories": categories}

            report.save()
            messages.success(request, _("Report saved successfully!"))

            # Redirect to the appropriate report view
            if report.report_type == "monthly":
                return redirect("reports:monthly_report")
            elif report.report_type == "annual":
                return redirect("reports:annual_report")
            else:
                return redirect("reports:dashboard")
        else:
            messages.error(request, _("Error saving report. Please try again."))

    return redirect("reports:dashboard")


class SavedReportListView(ListView):
    model = SavedReport
    template_name = "saved_reports.html"
    context_object_name = "reports"
