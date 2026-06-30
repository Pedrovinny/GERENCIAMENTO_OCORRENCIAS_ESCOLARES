from django.contrib import admin

from .models import (
    Aluno, AnexoOcorrencia, Curso, Horario, Ocorrencia,
    PerfilUsuario, Professor, TipoOcorrencia, Turma,
)


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ("nome", "curso", "turno", "ano_letivo")
    list_filter = ("curso", "turno", "ano_letivo")
    search_fields = ("nome",)


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ("nome", "siape", "email", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "siape", "email")


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("nome", "matricula", "turma", "curso")
    list_filter = ("turma", "curso")
    search_fields = ("nome", "matricula")


@admin.register(TipoOcorrencia)
class TipoOcorrenciaAdmin(admin.ModelAdmin):
    list_display = ("descricao", "nivel")
    list_filter = ("nivel",)


@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ("dia_semana", "aula", "horario_inicio", "horario_fim")
    list_filter = ("dia_semana",)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("user", "perfil", "siape", "area")
    list_filter = ("perfil",)


class AnexoInline(admin.TabularInline):
    model = AnexoOcorrencia
    extra = 0


@admin.register(Ocorrencia)
class OcorrenciaAdmin(admin.ModelAdmin):
    list_display = ("id", "aluno", "professor", "tipo", "status", "data", "usuario")
    list_filter = ("status", "tipo", "data")
    search_fields = ("aluno__nome", "aluno__matricula", "professor__nome")
    inlines = [AnexoInline]
    readonly_fields = (
        "usuario", "criado_por", "atualizado_por",
        "criado_em", "atualizado_em", "data", "hora",
    )
