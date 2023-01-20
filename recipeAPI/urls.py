from django.urls import path
from django.conf import settings
import recipeAPIapp.views.user as UserViews
import recipeAPIapp.views.auth as AuthViews
import recipeAPIapp.views.media as MediaViews


urlpatterns = [

    path('user', UserViews.UserView.as_view()),
    path('user/change-moderator/<int:user_id>', UserViews.ChangeModeratorView.as_view()),
    path('user/report/<int:user_id>', UserViews.ReportView.as_view()),

    path('auth/token', AuthViews.TokenView.as_view()),
    path('auth/login', AuthViews.LoginView.as_view()),
    path('auth/update', AuthViews.UpdateView.as_view()),
    path('auth/email-verification', AuthViews.VerificationView.as_view()),
    path('auth/email-verification/<str:code>', AuthViews.VerificationView.as_view()),
    path('auth/password-reset', AuthViews.PasswordResetView.as_view()),
    path('auth/password-reset/<int:user_id>/<str:code>', AuthViews.PasswordResetView.as_view()),

]

if settings.DEFAULT_FILE_STORAGE == 'django.core.files.storage.FileSystemStorage':
    urlpatterns += [path('media/<path:path>', MediaViews.ServeStaticView.as_view())]
