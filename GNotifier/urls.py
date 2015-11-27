from django.conf.urls import include, url
from django.contrib import admin
from NotifierApp import views
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^settings/', views.settings, name='settings'),
	url(r'^login/', views.login, name='login'),
	url(r'^logout/', views.logout, name='logout'),
    url(r'^ajax_validator/', views.ajax_validator, name='ajax_validator'),
    url(r'^admin/', include(admin.site.urls)),
]