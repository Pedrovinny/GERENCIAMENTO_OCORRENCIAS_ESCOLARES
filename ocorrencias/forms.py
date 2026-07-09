from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User

from .models import (
    Aluno,
    AnexoOcorrencia,
    Curso,
    DestinatarioRelatorio,
    Horario,
    Ocorrencia,
    PerfilUsuario,
    Professor,
    TipoOcorrencia,
    Turma,
)


class BootstrapFormMixin:
    """Aplica automaticamente as classes do Bootstrap 5 nos widgets do form."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput,)):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault("class", "form-select")
            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs.setdefault("class", "form-control")
            else:
                widget.attrs.setdefault("class", "form-control")


# ======================================================
# CADASTROS BÁSICOS
# ======================================================

class CursoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Curso
        fields = ["nome"]


class TurmaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Turma
        fields = ["nome", "curso", "turno", "ano_letivo"]


class ProfessorForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Professor
        fields = ["nome", "siape", "email", "telefone", "ativo"]


class AlunoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ["matricula", "nome", "email", "turma", "curso"]


class TipoOcorrenciaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = TipoOcorrencia
        fields = ["descricao", "nivel"]


class HorarioForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Horario
        fields = ["dia_semana", "horario_inicio", "horario_fim", "aula"]
        widgets = {
            "horario_inicio": forms.TimeInput(attrs={"type": "time"}),
            "horario_fim": forms.TimeInput(attrs={"type": "time"}),
        }


# ======================================================
# USUÁRIOS
# ======================================================

class UsuarioForm(BootstrapFormMixin, UserCreationForm):
    nome_completo = forms.CharField(label="Nome", max_length=150)
    email = forms.EmailField(label="E-mail")
    siape = forms.CharField(label="SIAPE", max_length=20, required=False)
    area = forms.ModelChoiceField(
        label="Área", queryset=Curso.objects.all(), required=False
    )
    perfil = forms.ChoiceField(
        label="Perfil", choices=PerfilUsuario.Perfil.choices
    )

    class Meta:
        model = User
        fields = [
            "username", "nome_completo", "email",
            "siape", "area", "perfil", "password1", "password2",
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        nome_completo = self.cleaned_data["nome_completo"].strip()
        partes = nome_completo.split(" ", 1)
        user.first_name = partes[0]
        user.last_name = partes[1] if len(partes) > 1 else ""
        user.email = self.cleaned_data["email"]
        user.is_staff = self.cleaned_data["perfil"] == PerfilUsuario.Perfil.ADMINISTRADOR

        if commit:
            user.save()
            perfil_obj, _ = PerfilUsuario.objects.update_or_create(
                user=user,
                defaults={
                    "siape": self.cleaned_data["siape"],
                    "area": self.cleaned_data["area"],
                    "perfil": self.cleaned_data["perfil"],
                },
            )
            _sincronizar_grupo(user, self.cleaned_data["perfil"])
        return user


class UsuarioEdicaoForm(BootstrapFormMixin, forms.ModelForm):
    nome_completo = forms.CharField(label="Nome", max_length=150)
    siape = forms.CharField(label="SIAPE", max_length=20, required=False)
    area = forms.ModelChoiceField(
        label="Área", queryset=Curso.objects.all(), required=False
    )
    perfil = forms.ChoiceField(
        label="Perfil", choices=PerfilUsuario.Perfil.choices
    )
    is_active = forms.BooleanField(label="Ativo", required=False)

    class Meta:
        model = User
        fields = ["username", "nome_completo", "email", "siape", "area", "perfil", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["nome_completo"].initial = self.instance.get_full_name()
            perfil_obj = getattr(self.instance, "perfil_ocorrencias", None)
            if perfil_obj:
                self.fields["siape"].initial = perfil_obj.siape
                self.fields["area"].initial = perfil_obj.area
                self.fields["perfil"].initial = perfil_obj.perfil

    def save(self, commit=True):
        user = super().save(commit=False)
        nome_completo = self.cleaned_data["nome_completo"].strip()
        partes = nome_completo.split(" ", 1)
        user.first_name = partes[0]
        user.last_name = partes[1] if len(partes) > 1 else ""
        user.is_staff = self.cleaned_data["perfil"] == PerfilUsuario.Perfil.ADMINISTRADOR

        if commit:
            user.save()
            PerfilUsuario.objects.update_or_create(
                user=user,
                defaults={
                    "siape": self.cleaned_data["siape"],
                    "area": self.cleaned_data["area"],
                    "perfil": self.cleaned_data["perfil"],
                },
            )
            _sincronizar_grupo(user, self.cleaned_data["perfil"])
        return user


def _sincronizar_grupo(user, perfil):
    """Garante que o usuário pertença apenas ao grupo correspondente ao perfil escolhido."""
    nomes_grupos = list(PerfilUsuario.GRUPO_POR_PERFIL.values())
    user.groups.remove(*Group.objects.filter(name__in=nomes_grupos))
    nome_grupo = PerfilUsuario.GRUPO_POR_PERFIL.get(perfil)
    if nome_grupo:
        grupo, _ = Group.objects.get_or_create(name=nome_grupo)
        user.groups.add(grupo)


# ======================================================
# OCORRÊNCIAS
# ======================================================

class OcorrenciaForm(BootstrapFormMixin, forms.ModelForm):
    aluno_busca = forms.CharField(
        label="Pesquisar aluno (matrícula ou nome)", required=False,
    )
    professor_busca = forms.CharField(
        label="Pesquisar professor (nome ou SIAPE)", required=False,
    )

    class Meta:
        model = Ocorrencia
        fields = [
            "professor", "aluno", "horario", "tipo",
            "descricao", "status", "observacoes",
        ]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 5}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["professor"].queryset = Professor.objects.filter(ativo=True)
        self.fields["horario"].required = False
        # Esses campos auxiliam a busca via JS e não são persistidos diretamente.
        self.fields["aluno_busca"].widget.attrs["placeholder"] = "Digite a matrícula ou nome..."
        self.fields["professor_busca"].widget.attrs["placeholder"] = "Digite o nome ou SIAPE..."


class AnexoOcorrenciaForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = AnexoOcorrencia
        fields = ["arquivo"]


AnexoFormSet = forms.modelformset_factory(
    AnexoOcorrencia, form=AnexoOcorrenciaForm, extra=3, can_delete=True
)


# ======================================================
# RELATÓRIO (FILTROS)
# ======================================================

class FiltroRelatorioForm(BootstrapFormMixin, forms.Form):
    professor = forms.ModelChoiceField(
        label="Professor", queryset=Professor.objects.all(), required=False
    )
    aluno = forms.ModelChoiceField(
        label="Aluno", queryset=Aluno.objects.all(), required=False
    )
    matricula = forms.CharField(label="Matrícula", required=False)
    curso = forms.ModelChoiceField(
        label="Curso", queryset=Curso.objects.all(), required=False
    )
    turma = forms.ModelChoiceField(
        label="Turma", queryset=Turma.objects.all(), required=False
    )
    tipo = forms.ModelChoiceField(
        label="Tipo", queryset=TipoOcorrencia.objects.all(), required=False
    )
    status = forms.ChoiceField(
        label="Status",
        choices=[("", "Todos")] + list(Ocorrencia.Status.choices),
        required=False,
    )
    usuario = forms.ModelChoiceField(
        label="Usuário responsável", queryset=User.objects.all(), required=False
    )
    data_inicial = forms.DateField(
        label="Data inicial", required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    data_final = forms.DateField(
        label="Data final", required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )


# ======================================================
# AUTOMAÇÃO: DESTINATÁRIOS DO RELATÓRIO DIÁRIO
# ======================================================

class DestinatarioRelatorioForm(BootstrapFormMixin, forms.ModelForm):
    DIAS_SEMANA = [
        "recebe_segunda", "recebe_terca", "recebe_quarta", "recebe_quinta",
        "recebe_sexta", "recebe_sabado", "recebe_domingo",
    ]

    class Meta:
        model = DestinatarioRelatorio
        fields = [
            "usuario", "nome", "email", "ativo",
            "recebe_segunda", "recebe_terca", "recebe_quarta", "recebe_quinta",
            "recebe_sexta", "recebe_sabado", "recebe_domingo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["usuario"].required = False
        self.fields["usuario"].empty_label = "— Destinatário externo (preencher nome/e-mail) —"
        self.fields["usuario"].queryset = User.objects.filter(is_active=True).order_by("first_name")

    def clean(self):
        cleaned = super().clean()
        usuario = cleaned.get("usuario")
        nome = cleaned.get("nome")
        email = cleaned.get("email")

        if not usuario and not email:
            self.add_error("email", "Informe um e-mail ou selecione um usuário do sistema.")
        if usuario and (nome or email):
            self.add_error("usuario", "Não combine usuário do sistema com nome/e-mail externos.")

        if not any(cleaned.get(dia) for dia in self.DIAS_SEMANA):
            raise forms.ValidationError(
                "Selecione ao menos um dia da semana para o envio do relatório."
            )
        return cleaned
