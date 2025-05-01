from django import template
from django.forms.boundfield import BoundField

register = template.Library()


@register.filter(name="add_class")
def filter_add_class(value, arg):
    """
    Añade una clase CSS a un widget de formulario
    Uso: {{ form.field|add_class:"form-control" }}
    """
    css_classes = value.field.widget.attrs.get("class", "")
    # Evita añadir la clase si ya existe
    if arg not in css_classes:
        if css_classes:
            css_classes = f"{css_classes} {arg}"
        else:
            css_classes = arg
    return value.as_widget(attrs={"class": css_classes})


@register.filter(name="attr")
def set_attr(field, attr_string):
    """
    Añade o modifica atributos HTML a un campo de formulario Django

    Uso: {{ field|attr:"class:form-control,placeholder:Ingresa tu nombre" }}
    """
    if not isinstance(field, BoundField):
        return field

    attrs = {}
    # Dividir la cadena de atributos por comas
    attr_pairs = attr_string.split(",")

    # Procesar cada par de atributo-valor
    for pair in attr_pairs:
        if ":" in pair:
            key, value = pair.split(":", 1)
            key = key.strip()
            value = value.strip()

            # Si el campo ya tiene este atributo, combinar los valores
            if key == "class" and "class" in field.field.widget.attrs:
                value = f"{field.field.widget.attrs['class']} {value}"

            attrs[key] = value

    # Crear una copia del widget para no modificar el original
    widget = field.field.widget

    # Actualizar los atributos del widget con los nuevos
    field.field.widget.attrs.update(attrs)

    return field
