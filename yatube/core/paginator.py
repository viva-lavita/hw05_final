from django.core.paginator import Paginator
from django.conf import settings


def paginator(records, request):
    paginator = Paginator(records, settings.LIMIT_VIEWS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
