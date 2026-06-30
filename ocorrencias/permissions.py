from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class AdministradorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Restringe o acesso da view apenas a usuários autenticados que pertençam
    ao grupo 'Administrador' (ou que sejam superusuários).
    """

    raise_exception = False
    permission_denied_message = (
        "Você não tem permissão para acessar esta área. "
        "Apenas administradores podem gerenciar este cadastro."
    )

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name="Administrador").exists()

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        from django.contrib import messages
        from django.shortcuts import redirect

        messages.error(self.request, self.permission_denied_message)
        return redirect("ocorrencias:dashboard")


def usuario_e_administrador(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Administrador").exists()
    )
