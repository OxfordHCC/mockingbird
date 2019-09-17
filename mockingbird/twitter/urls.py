from django.urls import path

from . import views, view_info, view_edit, view_explain

app_name = 'twitter'
urlpatterns = [
    path('', views.index, name='index'),
    path('username/', views.username, name='username'),
    path('<username>/tweets/', views.tweets, name='tweets'),
    path('<username>/profile/', views.profile, name='profile'),
    path('<username>/profile/reset/', views.reset_tweets, name='reset_tweets'),
    path('<username>/ibm/info/', view_info.ibm_info, name='ibm_info'),
    path('<username>/<attr>_m3/info/', view_info.m3_info, name='m3_info'),
    path('<username>/<attr>_blob/info/', view_info.blob_info, name='blob_info'),
    path('<username>/<attr>_clf/info/', view_info.clf_info, name='clf_info'),
    path('<username>/<attr>/info/', view_info.lex_info, name='lex_info'),
    path('<username>/<attr>_lex/edit/<target>/', view_edit.lex_edit, name='lex_edit'),
    path('<username>/<attr>_lime/edit/<target>/', view_edit.lime_edit, name='lime_edit'),
    path('<username>/<attr>_lex/edited/', views.lex_edited, name='lex_edited'),
    path('<username>/<attr>_lime/edited/', views.lime_edited, name='lime_edited'),
    path('<username>/<attr>_lime/explanation/', view_explain.lime_explain, name='lime_explanation'),
    path('<username>/<attr>_lime/explain_all/', view_explain.lime_explain_all, name='lime_explain_all')
]
