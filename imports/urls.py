from django.urls import path

from imports import views

app_name = "imports"

urlpatterns = [
    path("", views.home, name="home"),
    path("chats/", views.chat_list, name="chat_list"),
    path("chats/<int:chat_id>/", views.chat_detail, name="chat_detail"),
    path("midia/<int:media_id>/", views.media_asset_content, name="media_asset_content"),
    path("contatos/", views.contact_lookup, name="contact_lookup"),
]
