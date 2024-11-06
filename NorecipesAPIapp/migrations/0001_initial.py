import NorecipesAPIapp.models.timestamp
from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.ImageField(upload_to='category/')),
                ('name', models.CharField(max_length=75, unique=True, validators=[django.core.validators.MinLengthValidator(2)])),
                ('about', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.ImageField(upload_to='ingredient/')),
                ('name', models.CharField(max_length=75, unique=True, validators=[django.core.validators.MinLengthValidator(2)])),
                ('unit', models.CharField(choices=[('g', 'Gram'), ('kg', 'Kilogram'), ('ml', 'Milliliter'), ('l', 'Liter'), ('tsp', 'Teaspoon'), ('tbsp', 'Tablespoon'), ('cup', 'Cup'), ('pcs', 'Piece'), ('pinch', 'Pinch')], max_length=10)),
                ('about', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=NorecipesAPIapp.models.timestamp.utc_now)),
                ('submit_status', models.CharField(choices=[('UNSUBMITTED', 'Unsubmitted'), ('SUBMITTED', 'Submitted'), ('DENIED', 'Denied'), ('ACCEPTED', 'Accepted')], default='UNSUBMITTED', max_length=20)),
                ('deny_message', models.CharField(blank=True, max_length=300, null=True)),
                ('name', models.CharField(max_length=75, validators=[django.core.validators.MinLengthValidator(2)])),
                ('title', models.CharField(max_length=200, validators=[django.core.validators.MinLengthValidator(10)])),
                ('prep_time', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('calories', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('categories', models.ManyToManyField(related_name='recipes', to='NorecipesAPIapp.category')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=NorecipesAPIapp.models.timestamp.utc_now)),
                ('password_hash', models.CharField(blank=True, max_length=150, null=True)),
                ('details_iteration', models.IntegerField(default=1)),
                ('banned', models.BooleanField(default=False)),
                ('moderator', models.BooleanField(default=False)),
                ('vcode', models.CharField(blank=True, max_length=40, null=True)),
                ('vcode_expiry', models.DateTimeField(blank=True, null=True)),
                ('pcode', models.CharField(blank=True, max_length=40, null=True)),
                ('pcode_expiry', models.DateTimeField(blank=True, null=True)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='user/')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('name', models.CharField(max_length=75, validators=[django.core.validators.MinLengthValidator(3)])),
                ('about', models.CharField(blank=True, max_length=500, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RecipePhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.ImageField(upload_to='recipe/')),
                ('number', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipephoto', to='NorecipesAPIapp.recipe')),
            ],
        ),
        migrations.CreateModel(
            name='RecipeInstruction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.ImageField(blank=True, null=True, upload_to='instruction/')),
                ('number', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ('title', models.CharField(max_length=100, validators=[django.core.validators.MinLengthValidator(5)])),
                ('content', models.CharField(max_length=2000, validators=[django.core.validators.MinLengthValidator(25)])),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipeinstruction', to='NorecipesAPIapp.recipe')),
            ],
        ),
        migrations.AddField(
            model_name='recipe',
            name='favoured_by',
            field=models.ManyToManyField(related_name='fav_recipes', to='NorecipesAPIapp.user'),
        ),
        migrations.AddField(
            model_name='recipe',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipe', to='NorecipesAPIapp.user'),
        ),
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=NorecipesAPIapp.models.timestamp.utc_now)),
                ('edited_at', models.DateTimeField(blank=True, null=True)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='rating/')),
                ('stars', models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)])),
                ('content', models.CharField(blank=True, max_length=500, null=True, validators=[django.core.validators.MinLengthValidator(10)])),
                ('liked_by', models.ManyToManyField(related_name='liked_ratings', to='NorecipesAPIapp.user')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rating', to='NorecipesAPIapp.recipe')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rating', to='NorecipesAPIapp.user')),
            ],
        ),
        migrations.CreateModel(
            name='EmailRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=NorecipesAPIapp.models.timestamp.utc_now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emailrecord', to='NorecipesAPIapp.user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='category',
            name='favoured_by',
            field=models.ManyToManyField(related_name='fav_categories', to='NorecipesAPIapp.user'),
        ),
        migrations.CreateModel(
            name='UserReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=NorecipesAPIapp.models.timestamp.utc_now)),
                ('reported', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reported', to='NorecipesAPIapp.user')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report', to='NorecipesAPIapp.user')),
            ],
            options={
                'unique_together': {('user', 'reported')},
            },
        ),
        migrations.CreateModel(
            name='UserIngredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('ingredient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='useringredient', to='NorecipesAPIapp.ingredient')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='useringredient', to='NorecipesAPIapp.user')),
            ],
            options={
                'unique_together': {('user', 'ingredient')},
            },
        ),
        migrations.CreateModel(
            name='RecipeIngredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('ingredient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipeingredient', to='NorecipesAPIapp.ingredient')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipeingredient', to='NorecipesAPIapp.recipe')),
            ],
            options={
                'unique_together': {('recipe', 'ingredient')},
            },
        ),
        migrations.AddIndex(
            model_name='recipe',
            index=models.Index(fields=['submit_status', '-created_at'], name='NorecipesAP_submit__1235fb_idx'),
        ),
        migrations.AddIndex(
            model_name='recipe',
            index=models.Index(fields=['user', '-created_at'], name='NorecipesAP_user_id_85f0df_idx'),
        ),
        migrations.AddIndex(
            model_name='rating',
            index=models.Index(fields=['recipe', '-created_at'], name='NorecipesAP_recipe__f6a76e_idx'),
        ),
        migrations.AddIndex(
            model_name='rating',
            index=models.Index(fields=['user', '-created_at'], name='NorecipesAP_user_id_7db3c8_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='rating',
            unique_together={('user', 'recipe')},
        ),
    ]
