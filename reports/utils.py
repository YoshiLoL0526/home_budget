import calendar
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth, TruncWeek, TruncYear
from django.utils import timezone
from operations.models import Operation
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import xlsxwriter


def get_date_range(period_type, user, year=None, month=None):
    """Generate start and end dates based on period type and user's timezone"""
    # Get user's timezone or default to UTC
    user_timezone = (
        timezone.pytz.timezone(user.profile.timezone)
        if hasattr(user, "profile") and hasattr(user.profile, "timezone")
        else timezone.utc
    )

    # Get current time in user's timezone
    today = timezone.now().astimezone(user_timezone).date()

    if period_type == "week":
        # Get the current week's start (Monday) and end (Sunday)
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period_type == "month":
        # Get the current month's start and end
        if year and month:
            start_date = datetime(year, month, 1, tzinfo=user_timezone).date()
            # Last day of the month
            _, last_day = calendar.monthrange(year, month)
            end_date = datetime(year, month, last_day, tzinfo=user_timezone).date()
        else:
            start_date = today.replace(day=1)
            # Last day of the month
            _, last_day = calendar.monthrange(today.year, today.month)
            end_date = today.replace(day=last_day)
    elif period_type == "year":
        # Get the current year's start and end
        year = year or today.year
        start_date = datetime(year, 1, 1, tzinfo=user_timezone).date()
        end_date = datetime(year, 12, 31, tzinfo=user_timezone).date()
    else:  # Custom or default to current month
        start_date = today.replace(day=1)
        _, last_day = calendar.monthrange(today.year, today.month)
        end_date = today.replace(day=last_day)

    return start_date, end_date


def get_expenses_by_category(user, start_date, end_date, categories=None):
    """Get expenses grouped by category for a given date range"""
    expenses_query = Operation.objects.filter(
        user=user, date__gte=start_date, date__lte=end_date, category__type="gasto"
    )

    if categories:
        expenses_query = expenses_query.filter(category__in=categories)

    expenses_by_category = (
        expenses_query.values("category__name", "category__color")
        .annotate(total=Sum("amount"), count=Count("id"), avg=Avg("amount"))
        .order_by("-total")
    )

    return expenses_by_category


def get_expense_trend(user, start_date, end_date, period="month"):
    """Get expense trend over time (weekly, monthly, or yearly)"""
    expenses_query = Operation.objects.filter(
        user=user, date__gte=start_date, date__lte=end_date, category__type="gasto"
    )

    if period == "week":
        expenses_trend = (
            expenses_query.annotate(period=TruncWeek("date"))
            .values("period")
            .annotate(total=Sum("amount"))
            .order_by("period")
        )
    elif period == "month":
        expenses_trend = (
            expenses_query.annotate(period=TruncMonth("date"))
            .values("period")
            .annotate(total=Sum("amount"))
            .order_by("period")
        )
    else:  # year
        expenses_trend = (
            expenses_query.annotate(period=TruncYear("date"))
            .values("period")
            .annotate(total=Sum("amount"))
            .order_by("period")
        )

    return expenses_trend


def generate_chart_data(data, chart_type="pie"):
    """Generate data formatted for Chart.js"""
    if chart_type == "pie" or chart_type == "doughnut":
        labels = [item["category__name"] for item in data]
        values = [float(item["total"]) for item in data]
        colors = [item["category__color"] for item in data]

        chart_data = {
            "labels": labels,
            "datasets": [{"data": values, "backgroundColor": colors, "borderWidth": 1}],
        }

    elif chart_type == "bar":
        labels = [item["category__name"] for item in data]
        values = [float(item["total"]) for item in data]
        colors = [item["category__color"] for item in data]

        chart_data = {
            "labels": labels,
            "datasets": [
                {
                    "label": "Expenses by Category",
                    "data": values,
                    "backgroundColor": colors,
                    "borderWidth": 1,
                }
            ],
        }

    elif chart_type == "line":
        labels = [item["period"].strftime("%Y-%m-%d") for item in data]
        values = [float(item["total"]) for item in data]

        chart_data = {
            "labels": labels,
            "datasets": [
                {
                    "label": "Expense Trend",
                    "data": values,
                    "fill": False,
                    "borderColor": "#3498db",
                    "tension": 0.1,
                }
            ],
        }

    return chart_data


def export_to_excel(data, sheet_name="Report"):
    """Export data to Excel file"""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet(sheet_name)

    # Add headers
    headers = list(data[0].keys()) if data else []
    for col_num, header in enumerate(headers):
        worksheet.write(0, col_num, header)

    # Add data
    for row_num, row_data in enumerate(data, 1):
        for col_num, (key, value) in enumerate(row_data.items()):
            worksheet.write(row_num, col_num, value)

    workbook.close()
    output.seek(0)

    return output


def export_to_pdf(data):
    """Export data to PDF file"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # Create table data
    if data:
        headers = list(data[0].keys())
        table_data = [headers]
        for item in data:
            table_data.append([str(item[key]) for key in headers])

        # Create table
        table = Table(table_data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return buffer
