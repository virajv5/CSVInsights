from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path('project/', include('project.urls')),  # Including project app's URLs
    path('exp/', include('exp.urls')),  # Including project app's URLs

]
