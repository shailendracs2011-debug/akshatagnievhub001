from django.urls import path
from .views import *
urlpatterns=[
  path('',home,name='home'), path('language/<str:code>/',language,name='language'), path('gallery/',gallery,name='gallery'),
  path('category/<slug:slug>/',category_page,name='category'), path('product/<slug:slug>/',product_detail,name='product_detail'),
  path('enquiry/',enquire,name='enquiry'), path('product/<slug:slug>/enquiry/',enquire,name='product_enquiry'),
  path('product/<slug:slug>/book/',book_order,name='book_order'), path('order/<int:pk>/success/',order_success,name='order_success'),
  path('service/',service_enquiry,name='service'), path('support/',support_query,name='support'), path('ticket/<str:ticket>/success/',ticket_success,name='ticket_success'),
  path('erp/login/',ERPLoginView.as_view(),name='erp_login'), path('erp/logout/',ERPLogoutView.as_view(),name='erp_logout'), path('erp/',erp_dashboard,name='erp_dashboard'),
  path('erp/settings/',erp_settings,name='erp_settings'),
  path('erp/sales/',erp_sales,name='erp_sales'), path('erp/sales/export/',export_sales_excel,name='export_sales'),
  path('erp/purchases/',erp_purchases,name='erp_purchases'), path('erp/purchases/export/',export_purchases_excel,name='export_purchases'),
  path('erp/inventory/',erp_inventory,name='erp_inventory'), path('erp/inventory/export/',export_inventory_excel,name='export_inventory'),
  path('erp/orders/',erp_orders,name='erp_orders'), path('erp/orders/export/',export_orders_excel,name='export_orders'),
  path('erp/enquiries/',erp_enquiries,name='erp_enquiries'), path('erp/enquiries/export/',export_enquiries_excel,name='export_enquiries'),
  path('erp/activities/',erp_activities,name='erp_activities'), path('erp/activities/export/',export_activities_excel,name='export_activities'),
  path('erp/service/',erp_service,name='erp_service'), path('erp/service/export/',export_service_excel,name='export_service'),
  path('erp/support/',erp_support,name='erp_support'), path('erp/support/export/',export_support_excel,name='export_support'),
  path('erp/ledger/',erp_ledger,name='erp_ledger'), path('erp/ledger/export/',export_ledger_excel,name='export_ledger'),
  path('erp/reports/',erp_reports,name='erp_reports'), path('erp/reports/export/',export_reports_excel,name='export_reports'),
  path('erp/sale/<int:pk>/invoice/',invoice_pdf,name='invoice_pdf'),
]
