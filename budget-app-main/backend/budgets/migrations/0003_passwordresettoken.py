# Generated manually

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid
from datetime import timedelta


def create_password_reset_token_model(apps, schema_editor):
    """Tworzy model PasswordResetToken"""
    # Model jest już zdefiniowany w models.py, więc migracja tylko tworzy tabelę
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('budgets', '0002_emailverificationtoken'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='PasswordResetToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('token', models.CharField(max_length=100, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('is_used', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='password_reset_tokens', to='auth.user')),
            ],
            options={
                'verbose_name': 'Token resetu hasła',
                'verbose_name_plural': 'Tokeny resetu hasła',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='passwordresettoken',
            index=models.Index(fields=['token'], name='budgets_pas_token_idx'),
        ),
        migrations.AddIndex(
            model_name='passwordresettoken',
            index=models.Index(fields=['user', 'is_used'], name='budgets_pas_user_is_u_idx'),
        ),
    ]

