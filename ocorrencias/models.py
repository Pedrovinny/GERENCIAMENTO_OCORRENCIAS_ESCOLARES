from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse


# ======================================================
# CURSOS / ÁREAS
# ======================================================

class Curso(models.Model):
    nome = models.CharField("Nome", max_length=120, unique=True)

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse("ocorrencias:curso_list")


# ======================================================
# TURMAS
# ======================================================

class Turma(models.Model):
    class Turno(models.TextChoices):
        MATUTINO = "MATUTINO", "Matutino"
        VESPERTINO = "VESPERTINO", "Vespertino"
        NOTURNO = "NOTURNO", "Noturno"
        INTEGRAL = "INTEGRAL", "Integral"

    nome = models.CharField("Nome da turma", max_length=120)
    curso = models.ForeignKey(
        Curso, on_delete=models.PROTECT, related_name="turmas",
        verbose_name="Curso",
    )
    turno = models.CharField(
        "Turno", max_length=20, choices=Turno.choices, default=Turno.MATUTINO
    )
    ano_letivo = models.PositiveIntegerField("Ano letivo")

    class Meta:
        verbose_name = "Turma"
        verbose_name_plural = "Turmas"
        ordering = ["-ano_letivo", "nome"]
        unique_together = ("nome", "ano_letivo")

    def __str__(self):
        return f"{self.nome} ({self.ano_letivo})"

    def get_absolute_url(self):
        return reverse("ocorrencias:turma_list")


# ======================================================
# PROFESSORES
# ======================================================

class Professor(models.Model):
    nome = models.CharField("Nome", max_length=150)
    siape = models.CharField("SIAPE", max_length=20, unique=True)
    email = models.EmailField("E-mail")
    telefone = models.CharField("Telefone", max_length=20, blank=True)
    ativo = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Professor"
        verbose_name_plural = "Professores"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse("ocorrencias:professor_list")


# ======================================================
# ALUNOS
# ======================================================

class Aluno(models.Model):
    matricula = models.CharField("Matrícula", max_length=30, unique=True)
    nome = models.CharField("Nome", max_length=150)
    email = models.EmailField("E-mail", blank=True)
    turma = models.ForeignKey(
        Turma, on_delete=models.PROTECT, related_name="alunos",
        verbose_name="Turma",
    )
    curso = models.ForeignKey(
        Curso, on_delete=models.PROTECT, related_name="alunos",
        verbose_name="Curso",
    )

    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.matricula})"

    def get_absolute_url(self):
        return reverse("ocorrencias:aluno_list")


# ======================================================
# TIPOS DE OCORRÊNCIA
# ======================================================

class TipoOcorrencia(models.Model):
    class Nivel(models.TextChoices):
        GRAVE = "GRAVE", "Grave"
        MEDIA = "MEDIA", "Média"
        LEVE = "LEVE", "Leve"

    descricao = models.CharField("Descrição", max_length=120, unique=True)
    nivel = models.CharField(
        "Nível", max_length=10, choices=Nivel.choices, default=Nivel.LEVE,
        help_text="Usado para classificar a ocorrência nos indicadores do dashboard.",
    )

    class Meta:
        verbose_name = "Tipo de Ocorrência"
        verbose_name_plural = "Tipos de Ocorrência"
        ordering = ["descricao"]

    def __str__(self):
        return self.descricao

    def get_absolute_url(self):
        return reverse("ocorrencias:tipo_list")

    @property
    def cor_nivel(self):
        return {
            self.Nivel.GRAVE: "danger",
            self.Nivel.MEDIA: "warning",
            self.Nivel.LEVE: "info",
        }.get(self.nivel, "secondary")


# ======================================================
# HORÁRIOS
# ======================================================

class Horario(models.Model):
    class DiaSemana(models.IntegerChoices):
        SEGUNDA = 1, "Segunda-feira"
        TERCA = 2, "Terça-feira"
        QUARTA = 3, "Quarta-feira"
        QUINTA = 4, "Quinta-feira"
        SEXTA = 5, "Sexta-feira"
        SABADO = 6, "Sábado"

    dia_semana = models.PositiveSmallIntegerField(
        "Dia da semana", choices=DiaSemana.choices
    )
    horario_inicio = models.TimeField("Horário inicial")
    horario_fim = models.TimeField("Horário final")
    aula = models.CharField("Aula", max_length=40, help_text='Ex: "1ª Aula"')

    class Meta:
        verbose_name = "Horário"
        verbose_name_plural = "Horários"
        ordering = ["dia_semana", "horario_inicio"]
        unique_together = ("dia_semana", "aula")

    def __str__(self):
        return f"{self.get_dia_semana_display()} - {self.aula}"

    def get_absolute_url(self):
        return reverse("ocorrencias:horario_list")


# ======================================================
# PERFIL DO USUÁRIO (dados extras além do User padrão)
# ======================================================

class PerfilUsuario(models.Model):
    class Perfil(models.TextChoices):
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
        USUARIO = "USUARIO", "Usuário"

    GRUPO_POR_PERFIL = {
        Perfil.ADMINISTRADOR: "Administrador",
        Perfil.USUARIO: "Usuario",
    }

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="perfil_ocorrencias",
    )
    siape = models.CharField("SIAPE", max_length=20, blank=True)
    area = models.ForeignKey(
        Curso, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="usuarios", verbose_name="Área",
    )
    perfil = models.CharField(
        "Perfil", max_length=20, choices=Perfil.choices, default=Perfil.USUARIO
    )

    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuário"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_perfil_display()})"

    def get_absolute_url(self):
        return reverse("ocorrencias:usuario_list")


# ======================================================
# OCORRÊNCIAS
# ======================================================

class Ocorrencia(models.Model):
    class Status(models.TextChoices):
        ABERTA = "ABERTA", "Aberta"
        EM_ANALISE = "EM_ANALISE", "Em análise"
        RESOLVIDA = "RESOLVIDA", "Resolvida"
        ARQUIVADA = "ARQUIVADA", "Arquivada"

    professor = models.ForeignKey(
        Professor, on_delete=models.PROTECT, related_name="ocorrencias",
        verbose_name="Professor",
    )
    aluno = models.ForeignKey(
        Aluno, on_delete=models.PROTECT, related_name="ocorrencias",
        verbose_name="Aluno",
    )
    horario = models.ForeignKey(
        Horario, on_delete=models.PROTECT, related_name="ocorrencias",
        verbose_name="Horário", null=True, blank=True,
    )
    tipo = models.ForeignKey(
        TipoOcorrencia, on_delete=models.PROTECT, related_name="ocorrencias",
        verbose_name="Tipo da Ocorrência",
    )
    descricao = models.TextField("Descrição")
    status = models.CharField(
        "Status", max_length=20, choices=Status.choices, default=Status.ABERTA
    )
    observacoes = models.TextField("Observações", blank=True)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="ocorrencias_registradas", verbose_name="Usuário responsável",
        editable=False,
    )

    data = models.DateField("Data", auto_now_add=True)
    hora = models.TimeField("Hora", auto_now_add=True)

    # Auditoria
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="ocorrencias_criadas", editable=False,
    )
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="ocorrencias_atualizadas", editable=False,
    )
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Ocorrência"
        verbose_name_plural = "Ocorrências"
        ordering = ["-data", "-hora"]

    def __str__(self):
        return f"Ocorrência #{self.pk} - {self.aluno} ({self.get_status_display()})"

    def get_absolute_url(self):
        return reverse("ocorrencias:ocorrencia_detail", args=[self.pk])

    @property
    def cor_status(self):
        return {
            self.Status.ABERTA: "danger",
            self.Status.EM_ANALISE: "warning",
            self.Status.RESOLVIDA: "success",
            self.Status.ARQUIVADA: "secondary",
        }.get(self.status, "secondary")

    @property
    def cor_nivel(self):
        return self.tipo.cor_nivel


def caminho_anexo(instance, filename):
    return f"ocorrencias/{instance.ocorrencia_id}/{filename}"


class AnexoOcorrencia(models.Model):
    ocorrencia = models.ForeignKey(
        Ocorrencia, on_delete=models.CASCADE, related_name="anexos",
        verbose_name="Ocorrência",
    )
    arquivo = models.FileField(
        "Arquivo", upload_to=caminho_anexo,
        validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png"])],
    )
    enviado_em = models.DateTimeField("Enviado em", auto_now_add=True)

    class Meta:
        verbose_name = "Anexo da Ocorrência"
        verbose_name_plural = "Anexos da Ocorrência"
        ordering = ["-enviado_em"]

    def __str__(self):
        return self.arquivo.name.rsplit("/", 1)[-1]

    @property
    def is_imagem(self):
        return self.arquivo.name.lower().endswith((".jpg", ".jpeg", ".png"))


# ======================================================
# AUTOMAÇÃO: DESTINATÁRIOS DO RELATÓRIO DIÁRIO POR E-MAIL
# ======================================================

class DestinatarioRelatorio(models.Model):
    """Cadastro de quem recebe o panorama diário de ocorrências por e-mail, e em quais dias."""

    WEEKDAY_FIELD_MAP = {
        0: "recebe_segunda",
        1: "recebe_terca",
        2: "recebe_quarta",
        3: "recebe_quinta",
        4: "recebe_sexta",
        5: "recebe_sabado",
        6: "recebe_domingo",
    }  # date.weekday(): Segunda=0 ... Domingo=6

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,
        related_name="destinatarios_relatorio", verbose_name="Usuário do sistema",
        help_text="Selecione um usuário já cadastrado, ou deixe em branco e informe nome/e-mail abaixo.",
    )
    nome = models.CharField("Nome", max_length=150, blank=True)
    email = models.EmailField("E-mail", blank=True)
    ativo = models.BooleanField("Ativo", default=True)

    recebe_segunda = models.BooleanField("Segunda-feira", default=False)
    recebe_terca = models.BooleanField("Terça-feira", default=False)
    recebe_quarta = models.BooleanField("Quarta-feira", default=False)
    recebe_quinta = models.BooleanField("Quinta-feira", default=False)
    recebe_sexta = models.BooleanField("Sexta-feira", default=False)
    recebe_sabado = models.BooleanField("Sábado", default=False)
    recebe_domingo = models.BooleanField("Domingo", default=False)

    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Destinatário de Relatório"
        verbose_name_plural = "Destinatários de Relatório"
        ordering = ["nome", "email"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario"], condition=models.Q(usuario__isnull=False),
                name="unico_destinatario_por_usuario",
            ),
            models.UniqueConstraint(
                fields=["email"], condition=models.Q(usuario__isnull=True),
                name="unico_destinatario_por_email",
            ),
            models.CheckConstraint(
                condition=models.Q(usuario__isnull=False) | ~models.Q(email=""),
                name="destinatario_requer_usuario_ou_email",
            ),
        ]

    def __str__(self):
        return f"{self.nome_efetivo} <{self.email_efetivo}>"

    def get_absolute_url(self):
        return reverse("ocorrencias:destinatario_list")

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.usuario_id and not self.email:
            raise ValidationError("Informe um usuário do sistema OU um e-mail externo.")
        if self.usuario_id and (self.nome or self.email):
            raise ValidationError(
                "Preencha nome/e-mail OU vincule um usuário do sistema — não os dois."
            )

    @property
    def nome_efetivo(self):
        if self.usuario_id:
            return self.usuario.get_full_name() or self.usuario.username
        return self.nome or self.email

    @property
    def email_efetivo(self):
        return self.usuario.email if self.usuario_id else self.email

    @property
    def dias_selecionados(self):
        rotulos = {
            "recebe_segunda": "Seg", "recebe_terca": "Ter", "recebe_quarta": "Qua",
            "recebe_quinta": "Qui", "recebe_sexta": "Sex", "recebe_sabado": "Sáb",
            "recebe_domingo": "Dom",
        }
        return [rotulo for campo, rotulo in rotulos.items() if getattr(self, campo)]

    @classmethod
    def destinatarios_do_dia(cls, data):
        """QuerySet de destinatários ativos que devem receber o relatório na `data` informada."""
        campo = cls.WEEKDAY_FIELD_MAP[data.weekday()]
        return cls.objects.filter(ativo=True, **{campo: True}).select_related("usuario")
