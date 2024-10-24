from django.urls import path
from .views import UploadCSVView, GenerateSQlQuery, MultipleCSVUploadView, GenerateSQLJoinQuery

urlpatterns = [
    path('upload-csv/', UploadCSVView.as_view(), name='upload_csv'),
    path('upload-Multiple-csv/', MultipleCSVUploadView.as_view(), name='get_data'),
    path('get-data/', GenerateSQlQuery.as_view(), name='get_data'),
    path('get-Multiple-data/', GenerateSQLJoinQuery.as_view(), name='get_data'),
]