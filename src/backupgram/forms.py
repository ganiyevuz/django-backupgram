from __future__ import annotations

from django.core.exceptions import ValidationError
from django.forms import (
    BooleanField,
    CharField,
    Form,
    IntegerField,
    ModelForm,
    PasswordInput,
)

from backupgram.models import BackupServer


class BackupServerForm(ModelForm):
    token = CharField(
        widget=PasswordInput(render_value=False),
        required=False,
        help_text="Leave blank to keep the existing token.",
    )

    class Meta:
        model = BackupServer
        fields = ["name", "base_url", "token", "verify_tls", "timeout", "enabled"]

    def clean_token(self):
        token = self.cleaned_data.get("token")
        if not token and self.instance.pk:
            return self.instance.token
        return token


class RestoreForm(Form):
    file = CharField(required=False)
    telegram_message_id = IntegerField(required=False, min_value=1)
    target_db = CharField(max_length=63)
    confirm = BooleanField(
        required=True, error_messages={"required": "You must confirm the restore."}
    )

    def clean(self):
        cleaned = super().clean()
        has_file = bool(cleaned.get("file"))
        has_tg = bool(cleaned.get("telegram_message_id"))
        if has_file and has_tg:
            raise ValidationError(
                "Choose one source — a backup file or a Telegram message ID, not both."
            )
        if not has_file and not has_tg:
            raise ValidationError(
                "Choose a source — pick a backup file or enter a Telegram message ID."
            )
        return cleaned
