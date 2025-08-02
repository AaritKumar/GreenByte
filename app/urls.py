from django.urls import path
from . import views

urlpatterns = [
    path("", views.identify_view, name="identify"),
    path("tracker/", views.tracker_view, name="tracker"),
    path("finder/", views.finder_view, name="finder"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path('logout/', views.logout_view, name='logout'),
    path('identify/predict/', views.identify_predict, name='identify_predict'),
    path('update-tracker/', views.update_tracker, name='update_tracker'),
]