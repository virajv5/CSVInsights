# project/urls.py
from django.urls import path
from .views import UploadCSV,  Upload_Customer_CSV,  Upload_Sales_CSV,  GenerateSQLSalesTable, GenerateSQLPurchaseTable, GenerateSQLCustomerTable, GenerateSQLQueryView
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [

#uploading CSV
path('upload-Purchase-csv/', UploadCSV.as_view(), name='upload_csv'),
path('upload-Customer-csv/', Upload_Customer_CSV.as_view(), name='upload-csv'),
path('upload-Sales-csv/', Upload_Sales_CSV.as_view(), name='upload-sales-csv'),


# sql queries
    path('generate-related-query/', GenerateSQLQueryView.as_view(), name='generate-sql-query'),
    path('generate-sales-query/', GenerateSQLSalesTable.as_view(), name='generate-sales-query'),
    path('generate-purchase-query/', GenerateSQLPurchaseTable.as_view(), name='generate-purchase-query'),
    path('generate-customer-query/', GenerateSQLCustomerTable.as_view(), name='generate-purchase-query'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)