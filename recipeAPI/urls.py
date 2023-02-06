from django.urls import path
from django.conf import settings
import recipeAPIapp.views.user as UserViews
import recipeAPIapp.views.auth as AuthViews
import recipeAPIapp.views.categorical as CategoricalViews
import recipeAPIapp.views.media as MediaViews


urlpatterns = [

    path('user', UserViews.UserView.as_view()),
    path('user/change-moderator/<int:user_id>', UserViews.ChangeModeratorView.as_view()),
    path('user/report/<int:user_id>', UserViews.ReportView.as_view()),
    path('user/ban/<int:user_id>', UserViews.UserBanView.as_view()),
    path('user/dismiss-reports/<int:user_id>', UserViews.DismissReportsView.as_view()),
    path('user/detail/<int:user_id>', UserViews.UserDetailView.as_view()),
    path('user/self-detail', UserViews.UserSelfDetailView.as_view()),
    path('user/filter/paged', UserViews.UserFilterView.as_view()),

    path('auth/token', AuthViews.TokenView.as_view()),
    path('auth/login', AuthViews.LoginView.as_view()),
    path('auth/update', AuthViews.UpdateView.as_view()),
    path('auth/email-verification', AuthViews.VerificationView.as_view()),
    path('auth/email-verification/<str:code>', AuthViews.VerificationView.as_view()),
    path('auth/password-reset', AuthViews.PasswordResetView.as_view()),
    path('auth/password-reset/<int:user_id>/<str:code>', AuthViews.PasswordResetView.as_view()),

    path('category', CategoricalViews.CategoryView.as_view()),
    path('category/<int:category_id>', CategoricalViews.CategoryView.as_view()),
    path('category/change-favourite/<int:category_id>', CategoricalViews.CategoryFavourView.as_view()),
    path('category/filter/paged', CategoricalViews.CategoryFilterView.as_view()),

    path('ingredient', CategoricalViews.IngredientView.as_view()),
    path('ingredient/<int:ingredient_id>', CategoricalViews.IngredientView.as_view()),

]

if settings.DEFAULT_FILE_STORAGE == 'django.core.files.storage.FileSystemStorage':
    urlpatterns += [path('media/<path:path>', MediaViews.ServeStaticView.as_view())]
