import csv
import json

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView, View,
)

from .forms import (
    AlunoForm, CursoForm, DestinatarioRelatorioForm, FiltroRelatorioForm,
    HorarioForm, OcorrenciaForm, ProfessorForm, TipoOcorrenciaForm,
    TurmaForm, UsuarioEdicaoForm, UsuarioForm,
)
from .models import (
    Aluno, AnexoOcorrencia, Curso, DestinatarioRelatorio, Horario, Ocorrencia,
    Professor, TipoOcorrencia, Turma,
)
from .permissions import AdministradorRequiredMixin
from .relatorios_service import gerar_pdf_relatorio, linhas_ocorrencias


# ======================================================
# AUTENTICAÇÃO
# ======================================================

class LoginView(auth_views.LoginView):
    template_name = "ocorrencias/login.html"
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy("ocorrencias:login")


# ======================================================
# MIXIN GENÉRICO DE CRUD (pesquisa + paginação + mensagens)
# ======================================================

class CrudListMixin(LoginRequiredMixin):
    """Lista com pesquisa simples (campo 'q') e paginação."""

    paginate_by = 15
    campos_busca = []

    def get_queryset(self):
        qs = super().get_queryset()
        termo = self.request.GET.get("q", "").strip()
        if termo and self.campos_busca:
            filtro = Q()
            for campo in self.campos_busca:
                filtro |= Q(**{f"{campo}__icontains": termo})
            qs = qs.filter(filtro)
        return qs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["termo_busca"] = self.request.GET.get("q", "")
        return contexto


class CrudMensagemMixin:
    mensagem_sucesso = "Registro salvo com sucesso."

    def form_valid(self, form):
        resposta = super().form_valid(form)
        messages.success(self.request, self.mensagem_sucesso)
        return resposta


class CrudDeleteMixin(AdministradorRequiredMixin):
    def post(self, request, *args, **kwargs):
        resposta = super().post(request, *args, **kwargs)
        messages.success(request, "Registro excluído com sucesso.")
        return resposta


# ======================================================
# DASHBOARD
# ======================================================

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "ocorrencias/dashboard.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        hoje = timezone.localdate()

        ocorrencias = Ocorrencia.objects.all()

        contexto["total_ocorrencias"] = ocorrencias.count()
        contexto["ocorrencias_hoje"] = ocorrencias.filter(data=hoje).count()
        contexto["ocorrencias_graves"] = ocorrencias.filter(
            tipo__nivel=TipoOcorrencia.Nivel.GRAVE
        ).count()
        contexto["ocorrencias_medias"] = ocorrencias.filter(
            tipo__nivel=TipoOcorrencia.Nivel.MEDIA
        ).count()
        contexto["ocorrencias_leves"] = ocorrencias.filter(
            tipo__nivel=TipoOcorrencia.Nivel.LEVE
        ).count()
        contexto["total_professores"] = Professor.objects.count()
        contexto["total_alunos"] = Aluno.objects.count()
        contexto["total_cursos"] = Curso.objects.count()

        # --- Gráfico: ocorrências por mês (últimos 12 meses) ---
        por_mes = (
            ocorrencias
            .annotate(mes=TruncMonth("data"))
            .values("mes")
            .annotate(total=Count("id"))
            .order_by("mes")[:12]
        )
        contexto["grafico_mes_labels"] = json.dumps(
            [m["mes"].strftime("%m/%Y") for m in por_mes if m["mes"]]
        )
        contexto["grafico_mes_valores"] = json.dumps(
            [m["total"] for m in por_mes if m["mes"]]
        )

        # --- Gráfico: ocorrências por curso ---
        por_curso = (
            ocorrencias.values("aluno__curso__nome")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )
        contexto["grafico_curso_labels"] = json.dumps(
            [c["aluno__curso__nome"] or "Sem curso" for c in por_curso]
        )
        contexto["grafico_curso_valores"] = json.dumps(
            [c["total"] for c in por_curso]
        )

        # --- Gráfico: ocorrências por professor ---
        por_professor = (
            ocorrencias.values("professor__nome")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )
        contexto["grafico_professor_labels"] = json.dumps(
            [p["professor__nome"] for p in por_professor]
        )
        contexto["grafico_professor_valores"] = json.dumps(
            [p["total"] for p in por_professor]
        )

        # --- Gráfico: ocorrências por tipo ---
        por_tipo = (
            ocorrencias.values("tipo__descricao")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        contexto["grafico_tipo_labels"] = json.dumps(
            [t["tipo__descricao"] for t in por_tipo]
        )
        contexto["grafico_tipo_valores"] = json.dumps(
            [t["total"] for t in por_tipo]
        )

        # --- Gráfico: ocorrências por turma ---
        por_turma = (
            ocorrencias.values("aluno__turma__nome")
            .annotate(total=Count("id"))
            .order_by("-total")[:10]
        )
        contexto["grafico_turma_labels"] = json.dumps(
            [t["aluno__turma__nome"] or "Sem turma" for t in por_turma]
        )
        contexto["grafico_turma_valores"] = json.dumps(
            [t["total"] for t in por_turma]
        )

        contexto["ultimas_ocorrencias"] = ocorrencias.select_related(
            "aluno", "professor", "tipo"
        )[:8]

        return contexto


# ======================================================
# CADASTRO: PROFESSORES
# ======================================================

class ProfessorListView(AdministradorRequiredMixin, CrudListMixin, ListView):
    model = Professor
    template_name = "ocorrencias/cadastros/professor_list.html"
    context_object_name = "objetos"
    campos_busca = ["nome", "siape", "email"]


class ProfessorCreateView(AdministradorRequiredMixin, CrudMensagemMixin, CreateView):
    model = Professor
    form_class = ProfessorForm
    template_name = "ocorrencias/cadastros/form_generico.html"
    success_url = reverse_lazy("ocorrencias:professor_list")
    mensagem_sucesso = "Professor cadastrado com sucesso."
    extra_context = {"titulo": "Novo Professor", "voltar_url": "ocorrencias:professor_list"}


class ProfessorUpdateView(AdministradorRequiredMixin, CrudMensagemMixin, UpdateView):
    model = Professor
    form_class = ProfessorForm
    template_name = "ocorrencias/cadastros/form_generico.html"
    success_url = reverse_lazy("ocorrencias:professor_list")
    mensagem_sucesso = "Professor atualizado com sucesso."
    extra_context = {"titulo": "Editar Professor", "voltar_url": "ocorrencias:professor_list"}


class ProfessorDeleteView(CrudDeleteMixin, DeleteView):
    model = Professor
    template_name = "ocorrencias/cadastros/confirmar_exclusao.html"
    success_url = reverse_lazy("ocorrencias:professor_list")


# ======================================================
# CADASTRO: CURSOS / ÁREAS
# ======================================================

class CursoListView(AdministradorRequiredMixin, CrudListMixin, ListView):
    model = Curso
    template_name = "ocorrencias/cadastros/curso_list.html"
    context_object_name = "objetos"
    campos_busca = ["nome"]


class CursoCreateView(AdministradorRequiredMixin, CrudMensagemMixin, CreateView):
    model = Curso
    form_class = CursoForm
    template_name = "ocorrencias/cadastros/form_generico.html"
    success_url = reverse_lazy("ocorrencias:curso_list")
    mensagem_sucesso = "Curso cadastrado com sucesso."
    extra_context = {"titulo": "Novo Curso", "voltar_url": "ocorrencias:curso_list"}


class CursoUpdateView(AdministradorRequiredMixin, CrudMensagemMixin, UpdateView):
    model = Curso
    form_class = CursoForm
    template_name = "ocorrencias/cadastros/form_generico.html"
    success_url = reverse_lazy("ocorrencias:curso_list")
    mensagem_sucesso = "Curso atualizado com sucesso."
    extra_context = {"titulo": "Editar Curso", "voltar_url": "ocorrencias:curso_list"}


class CursoDeleteView(CrudDeleteMixin, DeleteView):
    model = Curso
    template_name = "ocorrencias/cadastros/confirmar_exclusao.html"
    success_url = reverse_lazy("ocorrencias:curso_list")


# ======================================================
# CADASTRO: TURMAS
# ======================================================

class TurmaListView(AdministradorRequiredMixin, CrudListMixin, ListView):
    model = Turma
    template_name = "ocorrencias/cadastros/turma_list.html"
    context_object_name = "objetos"
    campos_busca = ["nome", "curso__nome"]

    def get_queryset(self):
        return super().get_queryset().select_related("curso")


class TurmaCreateView(AdministradorRequiredMixin, CrudMensagemMixin, CreateView):
    model = Turma
    form_class = TurmaForm
    template_name = "ocorrencias/cadastros/form_generico.html"
    success_url = reverse_lazy("ocorrencias:turma_list")
    mensagem_sucesso = "Turma cadastrada com sucesso."
    extra_context = {"titulo": "Nova Turma", "voltar_url": "ocorrencias:turma_list"}


class TurmaUpdateView(AdministradorRequiredMixin, CrudMensagemMixin, UpdateView):
    model = Turma
    form_class = TurmaForm
    template_name = "ocorrencias/cadastros/form_generico.html"
    success_url = reverse_lazy("ocorrencias:turma_list")
    mensagem_sucesso = "Turma atualizada com sucesso."
    extra_context = {"titulo": "Editar Turma", "voltar_url": "ocorrencias:turma_list"}


class TurmaDeleteView(CrudDeleteMixin, DeleteView):
    model = Turma
    template_name = "ocorrencias/cadastros/confirmar_exclusao.html"
    success_url = reverse_lazy("ocorrencias:turma_list")


# ======================================================
# CADASTRO: ALUNOS
# ======================================================

class AlunoListView(AdministradorRequiredMixin, CrudListMixin, ListView):
    model = Aluno
    template_name = "ocorrencias/cadastros/aluno_list.html"
    context_object_name = "objetos"
    campos_busca = ["nome", "matricula"]

    def get_queryset(self):
        return super().get_queryset().select_related("turma", "curso")


class AlunoCreateView(AdministradorRequiredMixin, CrudMensagemMixin, CreateView):
    model = Aluno
    form_class = AlunoForm
    template_name = "ocorrencias/cadastros/form_generico.html"
    success_url = reverse_lazy("ocorrencias:aluno_list")
    mensagem_sucesso = "Aluno cadastrado com sucesso."
    extra_context = {"titulo": "Novo Aluno", "voltar_url": "ocorrencias:aluno_list"}


class AlunoUpdateView(AdministradorRequiredMixin, CrudMensagemMixin, UpdateView):
    model = Aluno
    form_class = AlunoForm
    template_name = "ocorrencias/cadastros/form_generico.html"
    success_url = reverse_lazy("ocorrencias:aluno_list")
    mensagem_sucesso = "Aluno atualizado com sucesso."
    extra_context = {"titulo": "Editar Aluno", "voltar_url": "ocorrencias:aluno_list"}


class AlunoDeleteView(CrudDeleteMixin, DeleteView):
    model = Aluno
    template_name = "ocorrencias/cadastros/confirmar_exclusao.html"
    success_url = reverse_lazy("ocorrencias:aluno_list")


# ======================================================
# CADASTRO: TIPOS DE OCORRÊNCIA
# ======================================================

class TipoOcorrenciaListView(AdministradorRequiredMixin, CrudListMixin, ListView):
    model = TipoOcorrencia
    template_name = "ocorrencias/cadastros/tipo_list.html"
    context_object_name = "objetos"
    campos_busca = ["descricao"]


class TipoOcorrenciaCreateView(AdministradorRequiredMixin, CrudMensagemMixin, CreateView):
    model = TipoOcorrencia
    form_class = TipoOcorrenciaForm
    template_name = "ocorrencias/cadastros/form_generico.html"
    success_url = reverse_lazy("ocorrencias:tipo_list")
    mensagem_sucesso = "Tipo de ocorrência cadastrado com sucesso."
    extra_context = {"titulo": "Novo Tipo de Ocorrência", "voltar_url": "ocorrencias:tipo_list"}


class TipoOcorrenciaUpdateView(AdministradorRequiredMixin, CrudMensagemMixin, UpdateView):
    model = TipoOcorrencia
    form_class = TipoOcorrenciaForm
    template_name = "ocorrencias/cadastros/form_generico.html"
    success_url = reverse_lazy("ocorrencias:tipo_list")
    mensagem_sucesso = "Tipo de ocorrência atualizado com sucesso."
    extra_context = {"titulo": "Editar Tipo de Ocorrência", "voltar_url": "ocorrencias:tipo_list"}


class TipoOcorrenciaDeleteView(CrudDeleteMixin, DeleteView):
    model = TipoOcorrencia
    template_name = "ocorrencias/cadastros/confirmar_exclusao.html"
    success_url = reverse_lazy("ocorrencias:tipo_list")


# ======================================================
# CADASTRO: HORÁRIOS
# ======================================================

class HorarioListView(AdministradorRequiredMixin, CrudListMixin, ListView):
    model = Horario
    template_name = "ocorrencias/cadastros/horario_list.html"
    context_object_name = "objetos"
    campos_busca = ["aula"]


class HorarioCreateView(AdministradorRequiredMixin, CrudMensagemMixin, CreateView):
    model = Horario
    form_class = HorarioForm
    template_name = "ocorrencias/cadastros/form_generico.html"
    success_url = reverse_lazy("ocorrencias:horario_list")
    mensagem_sucesso = "Horário cadastrado com sucesso."
    extra_context = {"titulo": "Novo Horário", "voltar_url": "ocorrencias:horario_list"}


class HorarioUpdateView(AdministradorRequiredMixin, CrudMensagemMixin, UpdateView):
    model = Horario
    form_class = HorarioForm
    template_name = "ocorrencias/cadastros/form_generico.html"
    success_url = reverse_lazy("ocorrencias:horario_list")
    mensagem_sucesso = "Horário atualizado com sucesso."
    extra_context = {"titulo": "Editar Horário", "voltar_url": "ocorrencias:horario_list"}


class HorarioDeleteView(CrudDeleteMixin, DeleteView):
    model = Horario
    template_name = "ocorrencias/cadastros/confirmar_exclusao.html"
    success_url = reverse_lazy("ocorrencias:horario_list")


# ======================================================
# GERENCIAMENTO DE USUÁRIOS
# ======================================================

class UsuarioListView(AdministradorRequiredMixin, CrudListMixin, ListView):
    model = User
    template_name = "ocorrencias/cadastros/usuario_list.html"
    context_object_name = "objetos"
    campos_busca = ["username", "first_name", "last_name", "email"]

    def get_queryset(self):
        return super().get_queryset().select_related("perfil_ocorrencias").order_by("username")


class UsuarioCreateView(AdministradorRequiredMixin, CrudMensagemMixin, CreateView):
    model = User
    form_class = UsuarioForm
    template_name = "ocorrencias/cadastros/form_generico.html"
    success_url = reverse_lazy("ocorrencias:usuario_list")
    mensagem_sucesso = "Usuário cadastrado com sucesso."
    extra_context = {"titulo": "Novo Usuário", "voltar_url": "ocorrencias:usuario_list"}


class UsuarioUpdateView(AdministradorRequiredMixin, CrudMensagemMixin, UpdateView):
    model = User
    form_class = UsuarioEdicaoForm
    template_name = "ocorrencias/cadastros/form_generico.html"
    success_url = reverse_lazy("ocorrencias:usuario_list")
    mensagem_sucesso = "Usuário atualizado com sucesso."
    extra_context = {"titulo": "Editar Usuário", "voltar_url": "ocorrencias:usuario_list"}


class UsuarioDeleteView(CrudDeleteMixin, DeleteView):
    model = User
    template_name = "ocorrencias/cadastros/confirmar_exclusao.html"
    success_url = reverse_lazy("ocorrencias:usuario_list")


# ======================================================
# OCORRÊNCIAS (funcionalidade principal)
# ======================================================

class OcorrenciaListView(CrudListMixin, ListView):
    model = Ocorrencia
    template_name = "ocorrencias/ocorrencia_list.html"
    context_object_name = "objetos"
    campos_busca = ["aluno__nome", "aluno__matricula", "professor__nome"]
    paginate_by = 10

    def get_queryset(self):
        return super().get_queryset().select_related(
            "aluno", "professor", "tipo", "usuario"
        )


class OcorrenciaDetailView(LoginRequiredMixin, DetailView):
    model = Ocorrencia
    template_name = "ocorrencias/ocorrencia_detail.html"
    context_object_name = "ocorrencia"

    def get_queryset(self):
        return super().get_queryset().select_related(
            "aluno", "professor", "tipo", "horario", "usuario"
        ).prefetch_related("anexos")


class OcorrenciaCreateView(LoginRequiredMixin, CreateView):
    model = Ocorrencia
    form_class = OcorrenciaForm
    template_name = "ocorrencias/ocorrencia_form.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["titulo"] = "Registrar Ocorrência"
        return contexto

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        form.instance.criado_por = self.request.user
        form.instance.atualizado_por = self.request.user
        resposta = super().form_valid(form)

        for arquivo in self.request.FILES.getlist("anexos"):
            AnexoOcorrencia.objects.create(ocorrencia=self.object, arquivo=arquivo)

        messages.success(self.request, "Ocorrência registrada com sucesso.")
        return resposta

    def get_success_url(self):
        return reverse_lazy("ocorrencias:ocorrencia_detail", args=[self.object.pk])


class OcorrenciaUpdateView(LoginRequiredMixin, UpdateView):
    model = Ocorrencia
    form_class = OcorrenciaForm
    template_name = "ocorrencias/ocorrencia_form.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["titulo"] = "Editar Ocorrência"
        return contexto

    def form_valid(self, form):
        form.instance.atualizado_por = self.request.user
        resposta = super().form_valid(form)

        for arquivo in self.request.FILES.getlist("anexos"):
            AnexoOcorrencia.objects.create(ocorrencia=self.object, arquivo=arquivo)

        messages.success(self.request, "Ocorrência atualizada com sucesso.")
        return resposta

    def get_success_url(self):
        return reverse_lazy("ocorrencias:ocorrencia_detail", args=[self.object.pk])


class OcorrenciaDeleteView(CrudDeleteMixin, DeleteView):
    model = Ocorrencia
    template_name = "ocorrencias/cadastros/confirmar_exclusao.html"
    success_url = reverse_lazy("ocorrencias:ocorrencia_list")


class AnexoDeleteView(LoginRequiredMixin, DeleteView):
    model = AnexoOcorrencia
    template_name = "ocorrencias/cadastros/confirmar_exclusao.html"

    def get_success_url(self):
        messages.success(self.request, "Anexo removido com sucesso.")
        return reverse_lazy("ocorrencias:ocorrencia_detail", args=[self.object.ocorrencia_id])


# ======================================================
# BUSCAS RÁPIDAS (AJAX) — preenchimento automático no form de ocorrência
# ======================================================

class BuscarAlunoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        termo = request.GET.get("q", "").strip()
        resultados = []
        if termo:
            alunos = Aluno.objects.select_related("turma", "curso").filter(
                Q(matricula__icontains=termo) | Q(nome__icontains=termo)
            )[:10]
            resultados = [
                {
                    "id": a.id,
                    "nome": a.nome,
                    "matricula": a.matricula,
                    "turma": str(a.turma),
                    "curso": str(a.curso),
                }
                for a in alunos
            ]
        return HttpResponse(
            json.dumps(resultados), content_type="application/json"
        )


class BuscarProfessorView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        termo = request.GET.get("q", "").strip()
        resultados = []
        if termo:
            professores = Professor.objects.filter(
                Q(nome__icontains=termo) | Q(siape__icontains=termo), ativo=True
            )[:10]
            resultados = [
                {
                    "id": p.id,
                    "nome": p.nome,
                    "siape": p.siape,
                    "email": p.email,
                }
                for p in professores
            ]
        return HttpResponse(
            json.dumps(resultados), content_type="application/json"
        )


# ======================================================
# RELATÓRIOS
# ======================================================

def _aplicar_filtros_relatorio(querystring):
    """Recebe um QueryDict (GET) e devolve o queryset de Ocorrencia filtrado."""
    form = FiltroRelatorioForm(querystring or None)
    qs = Ocorrencia.objects.select_related(
        "aluno", "aluno__turma", "aluno__curso", "professor", "tipo", "usuario"
    )

    if form.is_valid():
        dados = form.cleaned_data
        if dados.get("professor"):
            qs = qs.filter(professor=dados["professor"])
        if dados.get("aluno"):
            qs = qs.filter(aluno=dados["aluno"])
        if dados.get("matricula"):
            qs = qs.filter(aluno__matricula__icontains=dados["matricula"])
        if dados.get("curso"):
            qs = qs.filter(aluno__curso=dados["curso"])
        if dados.get("turma"):
            qs = qs.filter(aluno__turma=dados["turma"])
        if dados.get("tipo"):
            qs = qs.filter(tipo=dados["tipo"])
        if dados.get("status"):
            qs = qs.filter(status=dados["status"])
        if dados.get("usuario"):
            qs = qs.filter(usuario=dados["usuario"])
        if dados.get("data_inicial"):
            qs = qs.filter(data__gte=dados["data_inicial"])
        if dados.get("data_final"):
            qs = qs.filter(data__lte=dados["data_final"])

    return form, qs


def _ordenar(request, qs):
    ordenacao_valida = {
        "data": "data", "-data": "-data",
        "aluno": "aluno__nome", "-aluno": "-aluno__nome",
        "professor": "professor__nome", "-professor": "-professor__nome",
        "status": "status", "-status": "-status",
    }
    campo = request.GET.get("ordenar", "-data")
    return qs.order_by(ordenacao_valida.get(campo, "-data"), "-hora")


class RelatorioView(LoginRequiredMixin, ListView):
    template_name = "ocorrencias/relatorio.html"
    context_object_name = "objetos"
    paginate_by = 20

    def get_queryset(self):
        self.form, qs = _aplicar_filtros_relatorio(self.request.GET)
        return _ordenar(self.request, qs)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["form"] = self.form
        contexto["ordenar_atual"] = self.request.GET.get("ordenar", "-data")
        # mantém os filtros aplicados ao trocar de página / ordenação
        parametros = self.request.GET.copy()
        parametros.pop("page", None)
        contexto["query_sem_page"] = parametros.urlencode()
        return contexto


class RelatorioExportarCSVView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        _, qs = _aplicar_filtros_relatorio(request.GET)
        qs = _ordenar(request, qs)
        _, linhas = linhas_ocorrencias(qs)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="relatorio_ocorrencias.csv"'
        writer = csv.writer(response)
        for linha in linhas:
            writer.writerow(linha)
        return response


class RelatorioExportarExcelView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        from openpyxl import Workbook
        from openpyxl.styles import Font

        _, qs = _aplicar_filtros_relatorio(request.GET)
        qs = _ordenar(request, qs)
        cabecalho, linhas = linhas_ocorrencias(qs)

        wb = Workbook()
        ws = wb.active
        ws.title = "Ocorrências"

        for linha in linhas:
            ws.append(linha)
        for celula in ws[1]:
            celula.font = Font(bold=True)
        for coluna in ws.columns:
            largura = max(len(str(c.value or "")) for c in coluna) + 2
            ws.column_dimensions[coluna[0].column_letter].width = min(largura, 40)

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="relatorio_ocorrencias.xlsx"'
        wb.save(response)
        return response


class RelatorioExportarPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        _, qs = _aplicar_filtros_relatorio(request.GET)
        qs = _ordenar(request, qs)
        _, linhas = linhas_ocorrencias(qs)

        pdf_bytes = gerar_pdf_relatorio(linhas, "Relatório de Ocorrências Escolares")

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="relatorio_ocorrencias.pdf"'
        return response


class RelatorioImprimirView(LoginRequiredMixin, ListView):
    template_name = "ocorrencias/relatorio_imprimir.html"
    context_object_name = "objetos"

    def get_queryset(self):
        self.form, qs = _aplicar_filtros_relatorio(self.request.GET)
        return _ordenar(self.request, qs)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["gerado_em"] = timezone.localtime()
        return contexto


# ======================================================
# AUTOMAÇÃO: DESTINATÁRIOS DO RELATÓRIO DIÁRIO
# ======================================================

class DestinatarioListView(AdministradorRequiredMixin, CrudListMixin, ListView):
    model = DestinatarioRelatorio
    template_name = "ocorrencias/cadastros/destinatario_list.html"
    context_object_name = "objetos"
    campos_busca = ["nome", "email", "usuario__first_name", "usuario__last_name", "usuario__email"]

    def get_queryset(self):
        return super().get_queryset().select_related("usuario")


class DestinatarioCreateView(AdministradorRequiredMixin, CrudMensagemMixin, CreateView):
    model = DestinatarioRelatorio
    form_class = DestinatarioRelatorioForm
    template_name = "ocorrencias/cadastros/form_generico.html"
    success_url = reverse_lazy("ocorrencias:destinatario_list")
    mensagem_sucesso = "Destinatário cadastrado com sucesso."
    extra_context = {"titulo": "Novo Destinatário de Relatório", "voltar_url": "ocorrencias:destinatario_list"}


class DestinatarioUpdateView(AdministradorRequiredMixin, CrudMensagemMixin, UpdateView):
    model = DestinatarioRelatorio
    form_class = DestinatarioRelatorioForm
    template_name = "ocorrencias/cadastros/form_generico.html"
    success_url = reverse_lazy("ocorrencias:destinatario_list")
    mensagem_sucesso = "Destinatário atualizado com sucesso."
    extra_context = {"titulo": "Editar Destinatário de Relatório", "voltar_url": "ocorrencias:destinatario_list"}


class DestinatarioDeleteView(CrudDeleteMixin, DeleteView):
    model = DestinatarioRelatorio
    template_name = "ocorrencias/cadastros/confirmar_exclusao.html"
    success_url = reverse_lazy("ocorrencias:destinatario_list")
