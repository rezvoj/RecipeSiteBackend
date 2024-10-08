from django.urls import path
from django.conf import settings
import recipeAPIapp.views.user as UserViews
import recipeAPIapp.views.auth as AuthViews
import recipeAPIapp.views.categorical as CategoricalViews
import recipeAPIapp.views.recipe as RecipeViews
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
    path('ingredient/inventory/<int:ingredient_id>', CategoricalViews.IngredientInventoryView.as_view()),
    path('ingredient/filter/paged', CategoricalViews.IngredientFilterView.as_view()),

    path('recipe', RecipeViews.RecipeView.as_view()),
    path('recipe/<int:recipe_id>', RecipeViews.RecipeView.as_view()),
    path('recipe/photo/<int:id>', RecipeViews.RecipePhotoView.as_view()),
    path('recipe/instruction/<int:id>', RecipeViews.RecipeInstructionView.as_view()),
    path('recipe/ingredient/<int:recipe_id>/<int:ingredient_id>', RecipeViews.RecipeIngredientView.as_view()),
    path('recipe/submit/<int:recipe_id>', RecipeViews.RecipeSubmitView.as_view()),
    path('recipe/accept/<int:recipe_id>', RecipeViews.RecipeAcceptView.as_view()),
    path('recipe/deny/<int:recipe_id>', RecipeViews.RecipeDenyView.as_view()),
    path('recipe/cook/<int:recipe_id>', RecipeViews.RecipeCookView.as_view()),
    path('recipe/change-favourite/<int:recipe_id>', RecipeViews.RecipeFavourView.as_view()),
    path('recipe/detail/<int:recipe_id>', RecipeViews.RecipeDetailView.as_view()),
    path('recipe/filter/paged', RecipeViews.RecipeFilterView.as_view()),

    path('rating/<int:id>', RecipeViews.RatingView.as_view()),
    path('rating/change-liked/<int:rating_id>', RecipeViews.RatingLikeView.as_view()),
    path('rating/filter/paged', RecipeViews.RatingFilterView.as_view()),

]

if settings.DEFAULT_FILE_STORAGE == 'django.core.files.storage.FileSystemStorage':
    urlpatterns += [path('media/<path:path>', MediaViews.ServeStaticView.as_view())]
