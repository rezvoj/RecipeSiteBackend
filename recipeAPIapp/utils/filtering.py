import re
from datetime import timedelta
from django.db.models import Q, Manager
from recipeAPIapp.models.timestamp import utc_now
from recipeAPIapp.models.recipe import SubmitStatuses



def search(qryset: Manager, field_names: list[str], search_string: str):
    """ Applies string search filtration on queryset """
    words = [re.sub(r"('s|s|s's)$", "", word.lower()) for word in search_string.split(" ")]
    words = [word for word in words if len(word) > 0]
    qry_filter = Q()
    for word in words:
        qry_filter_part = Q()
        for fn in field_names:
            qry_filter_part |= Q(**{f'{fn}__icontains': word})
        qry_filter &= qry_filter_part
    return qryset.filter(qry_filter)


def order_by(qryset: Manager, vdata, **recent_replace):
    """ Replaces time windowed parameters and applies order by on queryset """
    if 'order_by' in vdata:
        order_by = vdata['order_by']
        if 'order_time_window' in vdata:
            start_dtm = utc_now() - timedelta(days=vdata['order_time_window'])
            for order_param, replace_data in recent_replace.items():
                if order_param in order_by or f'-{order_param}' in order_by:
                    rec_param =  f'rec_{order_param}'
                    function = replace_data[0]
                    function_param: str = replace_data[1]
                    filter_param: str = replace_data[2]
                    filter = Q(**{f'{filter_param}__created_at__gte': start_dtm})
                    if filter_param.endswith('recipe') or filter_param.endswith('recipes'):
                        filter &= Q(**{f'{filter_param}__submit_status': SubmitStatuses.ACCEPTED})
                    qryset = qryset.annotate(**{rec_param: function(function_param, filter=filter, distinct=True)})
                    order_by = [rec_param if param == order_param else param for param in order_by]
                    order_by = [f'-{rec_param}' if param == f'-{order_param}' else param for param in order_by]
        qryset = qryset.order_by(*order_by)
    return qryset


def paginate(qryset: Manager, vdata, serialization_function):
    """ Paginates and serializes queryset """
    result = {'count': qryset.count(), 'page': vdata['page'], 'page_size': vdata['page_size']}
    offset = (vdata['page'] - 1) * vdata['page_size']
    qryset = qryset[offset:offset + vdata['page_size']]
    result['results'] = serialization_function(qryset)
    return result
