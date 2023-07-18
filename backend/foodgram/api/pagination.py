from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    '''Пагинатор, который выводит запрашиваемое
    количество объектов на странице.
    '''
    page_size_query_param = 'limit'
