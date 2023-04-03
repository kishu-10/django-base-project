from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10


class CustomPagination(PageNumberPagination):
    page = DEFAULT_PAGE
    page_size = DEFAULT_PAGE_SIZE
    page_query_param = "page"
    page_size_query_param = "page_size"
    
    def paginate_queryset(self, queryset, request, view=None):
        '''Overrding this method to get full queryset incase escape_page param is True

        Args:
            queryset (_type_): _description_
            request (_type_): _description_
            view (_type_, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        '''
        escape_pg = request.GET.get("escape_pg", False)
        if escape_pg:
            super().paginate_queryset(queryset, request, view)
            return queryset

        return super().paginate_queryset(queryset, request, view)


    def get_paginated_response(self, data):
        escape_pg = self.request.GET.get("escape_pg",False)
        if escape_pg:
            return Response({
                "records": data,
                "totalRecords": self.page.paginator.count
            })
            
        if self.get_next_link():
            has_next = True
        else:
            has_next = False

        return Response(
            {
                "records": data,
                "totalRecords": self.page.paginator.count,
                "totalPages": int(self.page.paginator.num_pages),
                "pageNumber": int(self.request.GET.get("page", DEFAULT_PAGE)),
                "pageSize": int(self.request.GET.get("page_size", self.page_size)),
                "hasNext": has_next
            }
        )
