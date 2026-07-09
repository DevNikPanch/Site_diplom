from .models import Menu

def get_common_data(request):
    menu_items = Menu.objects.all()
    return {
        'menu_items': menu_items
    }