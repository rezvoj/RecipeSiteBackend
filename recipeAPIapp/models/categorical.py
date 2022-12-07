from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MinLengthValidator
from recipeAPIapp.models.user import User



class Category(models.Model):
    favoured_by = models.ManyToManyField(User, related_name='fav_categories')
    photo = models.ImageField(upload_to='category/')
    name = models.CharField(max_length=75, unique=True, validators=[MinLengthValidator(2)])
    about = models.CharField(max_length=200, null=True, blank=True)


class Ingredient(models.Model):
    photo = models.ImageField(upload_to='ingredient/')
    name = models.CharField(max_length=75, unique=True, validators=[MinLengthValidator(2)])
    unit = models.CharField(max_length=10)
    about = models.CharField(max_length=200, null=True, blank=True)


class UserIngredient(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='useringredient')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='useringredient')
    amount = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    class Meta:
        unique_together = ('user', 'ingredient')
