from rest_framework import viewsets


class CustomModelViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet that overrides get_serializer_class, perform_create, perform_update
    and perform_destroy
    """

    response_serializer_class = None

    def get_serializer_class(self):
        """
        If the method is GET return the alternate or response serializer class
        """
        if self.response_serializer_class and self.request.method == "GET":
            return self.response_serializer_class
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()
