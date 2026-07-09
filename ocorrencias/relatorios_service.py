"""Funções puras de geração de relatório/panorama (sem dependência de request/HttpResponse).

Reaproveitadas tanto pelas views web (`views.py`) quanto pelo robô de automação
em `automacao/bot.py`, que faz `django.setup()` e importa este módulo normalmente.
"""
import io

from django.db.models import Count
from django.utils import timezone

from .models import Ocorrencia, TipoOcorrencia


def linhas_ocorrencias(qs):
    """Monta cabeçalho + linhas tabulares a partir de um queryset de Ocorrencia."""
    cabecalho = [
        "Data", "Hora", "Professor", "Aluno", "Matrícula",
        "Turma", "Curso", "Tipo", "Usuário", "Status",
    ]
    linhas = [cabecalho]
    for o in qs:
        linhas.append([
            o.data.strftime("%d/%m/%Y"),
            o.hora.strftime("%H:%M"),
            o.professor.nome,
            o.aluno.nome,
            o.aluno.matricula,
            o.aluno.turma.nome,
            o.aluno.curso.nome,
            o.tipo.descricao,
            o.usuario.get_full_name() or o.usuario.username,
            o.get_status_display(),
        ])
    return cabecalho, linhas


def gerar_pdf_relatorio(linhas, titulo, subtitulo=None) -> bytes:
    """Gera o PDF do relatório (mesmo layout usado no download web) e devolve os bytes prontos
    para uma `HttpResponse` ou para um anexo de e-mail. `linhas` já inclui o cabeçalho na 1ª posição
    (formato retornado por `linhas_ocorrencias`)."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    if subtitulo is None:
        subtitulo = (
            f"Gerado em {timezone.localtime().strftime('%d/%m/%Y %H:%M')} "
            f"— {len(linhas) - 1} registro(s)"
        )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=1 * cm, rightMargin=1 * cm,
        topMargin=1 * cm, bottomMargin=1 * cm,
    )
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph(titulo, estilos["Title"]),
        Paragraph(subtitulo, estilos["Normal"]),
    ]

    tabela = Table(linhas, repeatRows=1)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elementos.append(tabela)

    doc.build(elementos)
    return buffer.getvalue()


def montar_panorama_do_dia(data) -> dict:
    """Agregações de ocorrências de uma data específica, no mesmo estilo do DashboardView."""
    qs = (
        Ocorrencia.objects
        .select_related("aluno", "aluno__turma", "aluno__curso", "professor", "tipo", "usuario")
        .filter(data=data)
        .order_by("professor__nome", "hora")
    )
    cabecalho, linhas = linhas_ocorrencias(qs)

    return {
        "data": data,
        "total": qs.count(),
        "graves": qs.filter(tipo__nivel=TipoOcorrencia.Nivel.GRAVE).count(),
        "medias": qs.filter(tipo__nivel=TipoOcorrencia.Nivel.MEDIA).count(),
        "leves": qs.filter(tipo__nivel=TipoOcorrencia.Nivel.LEVE).count(),
        "por_curso": list(
            qs.values("aluno__curso__nome").annotate(total=Count("id")).order_by("-total")
        ),
        "por_professor": list(
            qs.values("professor__nome").annotate(total=Count("id")).order_by("-total")
        ),
        "por_tipo": list(
            qs.values("tipo__descricao").annotate(total=Count("id")).order_by("-total")
        ),
        "por_turma": list(
            qs.values("aluno__turma__nome").annotate(total=Count("id")).order_by("-total")
        ),
        "cabecalho": cabecalho,
        "linhas": linhas,
    }


def ocorrencias_graves_pendentes_de_alerta():
    """Ocorrências abertas, de gravidade GRAVE, que ainda não geraram e-mail de alerta.

    Usado pelo robô de alerta em tempo real (`automacao/alerta_grave.py`); o campo
    `alerta_grave_enviado_em` evita reenviar o alerta a cada execução periódica.
    """
    return (
        Ocorrencia.objects
        .select_related("aluno", "aluno__turma", "aluno__curso", "professor", "tipo", "usuario")
        .filter(
            status=Ocorrencia.Status.ABERTA,
            tipo__nivel=TipoOcorrencia.Nivel.GRAVE,
            alerta_grave_enviado_em__isnull=True,
        )
        .order_by("data", "hora")
    )


def gerar_pdf_panorama_do_dia(panorama: dict) -> bytes:
    titulo = "Panorama Diário de Ocorrências Escolares"
    subtitulo = (
        f"Referente a {panorama['data'].strftime('%d/%m/%Y')} "
        f"— {panorama['total']} ocorrência(s) "
        f"(Graves: {panorama['graves']}, Médias: {panorama['medias']}, Leves: {panorama['leves']})"
    )
    return gerar_pdf_relatorio(panorama["linhas"], titulo, subtitulo)
