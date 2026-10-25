from rest_framework.pagination import PageNumberPagination


class CommentPagination(PageNumberPagination):
    """
    Постраничный вывод комментариев.
    25 на страницу.
    """

    page_size = 25