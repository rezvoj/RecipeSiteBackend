from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from recipeAPIapp.models.timestamp import Timestamped, EditTimestamped
from recipeAPIapp.models.user import User
from recipeAPIapp.models.categorical import Category, Ingredient



class SubmitStatuses:
    UNSUBMITTED = 'UNSUBMITTED'
    SUBMITTED = 'SUBMITTED'
    DENIED = 'DENIED'
    ACCEPTED = 'ACCEPTED'


class Recipe(Timestamped):
    favoured_by = models.ManyToManyField(User, related_name='fav_recipes')
    categories = models.ManyToManyField(Category, related_name='recipes')
    submit_status = models.CharField(default=SubmitStatuses.UNSUBMITTED, max_length=20)
    deny_message = models.CharField(max_length=300, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipe')
    name = models.CharField(max_length=75, validators=[MinLengthValidator(2)])
    title = models.CharField(max_length=200, validators=[MinLengthValidator(10)])
    prep_time = models.IntegerField(validators=[MinValueValidator(0)])
    calories = models.IntegerField(validators=[MinValueValidator(0)])


class RecipePhoto(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipephoto')
    photo = models.ImageField(upload_to='recipe/')
    number = models.IntegerField(default=1, validators=[MinValueValidator(1)])


class RecipeInstruction(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipeinstruction')
    photo = models.ImageField(upload_to='instruction/', null=True, blank=True)
    number = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    title = models.CharField(max_length=100, validators=[MinLengthValidator(5)])
    content = models.CharField(max_length=2000, validators=[MinLengthValidator(25)])


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipeingredient')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='recipeingredient')
    amount = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    class Meta:
        unique_together = ('recipe', 'ingredient')


class Rating(EditTimestamped):
    liked_by = models.ManyToManyField(User, related_name='liked_ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rating')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='rating')
    photo = models.ImageField(upload_to='rating/', null=True, blank=True)
    stars = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
    content = models.CharField(max_length=500, null=True, blank=True, validators=[MinLengthValidator(10)])
    class Meta:
        unique_together = ('user', 'recipe')
