from django import template
from calendar import month_name

register = template.Library()


@register.filter(name="get_range")
def filter_get_range(value, arg):
    """Generate a range of numbers from value to arg"""
    start = int(value)
    end = int(arg)
    return range(start, end + 1)


@register.filter(name="split")
def filter_split(value, arg):
    """Split a list of values"""
    return value.split(arg)


@register.filter(name="month_name")
def filter_month_name(value):
    """Convert month number to month name"""
    return month_name[int(value)]


@register.filter(name="dividedby")
def filter_divided_by(value, arg):
    """Divide value by arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0


@register.filter(name="mul")
def filter_mul(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0


@register.filter(name="abs")
def filter_abs(value):
    """Return absolute value"""
    try:
        return abs(float(value))
    except ValueError:
        return 0


@register.filter(name="div")
def filter_div(value, arg):
    """Integer division of value by arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0
