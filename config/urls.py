from django.contrib import admin
from django.urls import include, path
from showroom.views import custom_404

urlpatterns=[path('admin/',admin.site.urls),path('',include('showroom.urls'))]

handler404 = custom_404
