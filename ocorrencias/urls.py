from django.urls import path

from . import views

app_name = "ocorrencias"

urlpatterns = [
    # Autenticação
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),

    # Dashboard (home do sistema)
    path("", views.DashboardView.as_view(), name="dashboard"),

    # Ocorrências (funcionalidade principal)
    path("ocorrencias/", views.OcorrenciaListView.as_view(), name="ocorrencia_list"),
    path("ocorrencias/nova/", views.OcorrenciaCreateView.as_view(), name="ocorrencia_create"),
    path("ocorrencias/<int:pk>/", views.OcorrenciaDetailView.as_view(), name="ocorrencia_detail"),
    path("ocorrencias/<int:pk>/editar/", views.OcorrenciaUpdateView.as_view(), name="ocorrencia_update"),
    path("ocorrencias/<int:pk>/excluir/", views.OcorrenciaDeleteView.as_view(), name="ocorrencia_delete"),
    path("anexos/<int:pk>/excluir/", views.AnexoDeleteView.as_view(), name="anexo_delete"),

    # Buscas rápidas (AJAX)
    path("buscar/alunos/", views.BuscarAlunoView.as_view(), name="buscar_aluno"),
    path("buscar/professores/", views.BuscarProfessorView.as_view(), name="buscar_professor"),

    # Relatórios
    path("relatorio/", views.RelatorioView.as_view(), name="relatorio"),
    path("relatorio/csv/", views.RelatorioExportarCSVView.as_view(), name="relatorio_csv"),
    path("relatorio/excel/", views.RelatorioExportarExcelView.as_view(), name="relatorio_excel"),
    path("relatorio/pdf/", views.RelatorioExportarPDFView.as_view(), name="relatorio_pdf"),
    path("relatorio/imprimir/", views.RelatorioImprimirView.as_view(), name="relatorio_imprimir"),

    # Cadastro: Professores
    path("professores/", views.ProfessorListView.as_view(), name="professor_list"),
    path("professores/novo/", views.ProfessorCreateView.as_view(), name="professor_create"),
    path("professores/<int:pk>/editar/", views.ProfessorUpdateView.as_view(), name="professor_update"),
    path("professores/<int:pk>/excluir/", views.ProfessorDeleteView.as_view(), name="professor_delete"),

    # Cadastro: Cursos / Áreas
    path("cursos/", views.CursoListView.as_view(), name="curso_list"),
    path("cursos/novo/", views.CursoCreateView.as_view(), name="curso_create"),
    path("cursos/<int:pk>/editar/", views.CursoUpdateView.as_view(), name="curso_update"),
    path("cursos/<int:pk>/excluir/", views.CursoDeleteView.as_view(), name="curso_delete"),

    # Cadastro: Turmas
    path("turmas/", views.TurmaListView.as_view(), name="turma_list"),
    path("turmas/nova/", views.TurmaCreateView.as_view(), name="turma_create"),
    path("turmas/<int:pk>/editar/", views.TurmaUpdateView.as_view(), name="turma_update"),
    path("turmas/<int:pk>/excluir/", views.TurmaDeleteView.as_view(), name="turma_delete"),

    # Cadastro: Alunos
    path("alunos/", views.AlunoListView.as_view(), name="aluno_list"),
    path("alunos/novo/", views.AlunoCreateView.as_view(), name="aluno_create"),
    path("alunos/<int:pk>/editar/", views.AlunoUpdateView.as_view(), name="aluno_update"),
    path("alunos/<int:pk>/excluir/", views.AlunoDeleteView.as_view(), name="aluno_delete"),

    # Cadastro: Tipos de Ocorrência
    path("tipos/", views.TipoOcorrenciaListView.as_view(), name="tipo_list"),
    path("tipos/novo/", views.TipoOcorrenciaCreateView.as_view(), name="tipo_create"),
    path("tipos/<int:pk>/editar/", views.TipoOcorrenciaUpdateView.as_view(), name="tipo_update"),
    path("tipos/<int:pk>/excluir/", views.TipoOcorrenciaDeleteView.as_view(), name="tipo_delete"),

    # Cadastro: Horários
    path("horarios/", views.HorarioListView.as_view(), name="horario_list"),
    path("horarios/novo/", views.HorarioCreateView.as_view(), name="horario_create"),
    path("horarios/<int:pk>/editar/", views.HorarioUpdateView.as_view(), name="horario_update"),
    path("horarios/<int:pk>/excluir/", views.HorarioDeleteView.as_view(), name="horario_delete"),

    # Gerenciamento de Usuários
    path("usuarios/", views.UsuarioListView.as_view(), name="usuario_list"),
    path("usuarios/novo/", views.UsuarioCreateView.as_view(), name="usuario_create"),
    path("usuarios/<int:pk>/editar/", views.UsuarioUpdateView.as_view(), name="usuario_update"),
    path("usuarios/<int:pk>/excluir/", views.UsuarioDeleteView.as_view(), name="usuario_delete"),
]
