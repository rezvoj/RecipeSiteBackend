from django.urls import path
from django.conf import settings
import recipeAPIapp.views.auth as AuthViews


urlpatterns = [

    path('auth/token', AuthViews.TokenView.as_view()),

]
