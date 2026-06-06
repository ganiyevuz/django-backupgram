from __future__ import annotations

from django.forms import CharField, ModelForm, PasswordInput

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
