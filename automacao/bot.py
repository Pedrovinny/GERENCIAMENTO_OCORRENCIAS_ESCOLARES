"""
Robô BotCity Framework (edição local, sem Maestro/nuvem) responsável por montar
e enviar por e-mail o panorama diário de ocorrências escolares.

Este robô usa apenas `botcity-framework-core` (botcity.core.DesktopBot) para o
ciclo de vida da execução (`action()`); não há automação de tela/UI aqui — a
lógica de negócio é Django ORM (consulta) + reportlab (PDF, via
ocorrencias.relatorios_service) + Mailtrap Send API (envio via HTTP),
reaproveitando o mesmo código usado pelas views web do sistema.

Uso manual:
    venv\\Scripts\\python.exe automacao\\bot.py

Agendamento: ver automacao/README.md (Windows Task Scheduler + run_diario.bat).
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teste.settings")

import django  # noqa: E402
django.setup()

from django.utils import timezone  # noqa: E402

from botcity.core import DesktopBot  # noqa: E402

from automacao import email_service, logger_config  # noqa: E402
from automacao.config import carregar_configuracao_email  # noqa: E402
from ocorrencias.models import DestinatarioRelatorio  # noqa: E402
from ocorrencias.relatorios_service import (  # noqa: E402
    gerar_pdf_panorama_do_dia,
    montar_panorama_do_dia,
)


class RelatorioDiarioBot(DesktopBot):
    def action(self, execution=None):
        log = logger_config.configurar_logger()
        hoje = timezone.localdate()
        log.info("=== Início da execução — %s ===", hoje.isoformat())

        try:
            cfg = carregar_configuracao_email()

            panorama = montar_panorama_do_dia(hoje)
            pdf_bytes = gerar_pdf_panorama_do_dia(panorama)

            destinatarios = DestinatarioRelatorio.destinatarios_do_dia(hoje)
            if not destinatarios.exists():
                log.warning(
                    "Nenhum destinatário ativo configurado para %s (%s). Nada a enviar.",
                    hoje.strftime("%A"), hoje.isoformat(),
                )
                return

            enviados, falhas = 0, 0
            for destinatario in destinatarios:
                try:
                    email_service.enviar_panorama(cfg, destinatario, panorama, pdf_bytes)
                    enviados += 1
                    log.info("E-mail enviado com sucesso para %s", destinatario.email_efetivo)
                except Exception:
                    falhas += 1
                    log.exception("Falha ao enviar e-mail para %s", destinatario.email_efetivo)

            log.info("=== Fim da execução — enviados=%s falhas=%s ===", enviados, falhas)
        except Exception:
            log.exception("Erro fatal na execução do robô.")
            raise


if __name__ == "__main__":
    RelatorioDiarioBot.main()
