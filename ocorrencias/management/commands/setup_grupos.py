from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from ocorrencias import models as m

MODELOS_ADMIN = [
    m.Professor, m.Curso, m.Turma, m.Aluno, m.TipoOcorrencia,
    m.Horario, m.PerfilUsuario, m.Ocorrencia, m.AnexoOcorrencia,
]

MODELOS_USUARIO_RESTRITO = [m.Ocorrencia, m.AnexoOcorrencia]


class Command(BaseCommand):
    help = (
        "Cria (ou atualiza) os grupos 'Administrador' e 'Usuario' com as "
        "permissões adequadas para o sistema de Ocorrências Escolares."
    )

    def handle(self, *args, **options):
        grupo_admin, _ = Group.objects.get_or_create(name="Administrador")
        grupo_usuario, _ = Group.objects.get_or_create(name="Usuario")

        # Administrador: acesso total a todos os cadastros do app.
        permissoes_admin = Permission.objects.filter(
            content_type__app_label="ocorrencias"
        )
        grupo_admin.permissions.set(permissoes_admin)

        # Usuário comum: pode ver os cadastros de apoio (para usar nos
        # formulários/relatórios) e criar/visualizar ocorrências e anexos,
        # mas não pode editar/excluir cadastros administrativos.
        permissoes_usuario = []
        for modelo in MODELOS_ADMIN:
            codename_view = f"view_{modelo._meta.model_name}"
            permissoes_usuario += list(
                Permission.objects.filter(
                    content_type__app_label="ocorrencias",
                    codename=codename_view,
                )
            )

        for modelo in MODELOS_USUARIO_RESTRITO:
            for acao in ("add", "view"):
                codename = f"{acao}_{modelo._meta.model_name}"
                permissoes_usuario += list(
                    Permission.objects.filter(
                        content_type__app_label="ocorrencias",
                        codename=codename,
                    )
                )

        grupo_usuario.permissions.set(permissoes_usuario)

        self.stdout.write(self.style.SUCCESS(
            "Grupos 'Administrador' e 'Usuario' configurados com sucesso."
        ))
