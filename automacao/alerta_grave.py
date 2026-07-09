"""Robô BotCity Framework (edição local, sem Maestro/nuvem) responsável por alertar por
e-mail, em tempo real, sobre ocorrências GRAVES que permanecem com status ABERTA.

Assim como `automacao/bot.py`, usa apenas `botcity-framework-core` (botcity.core.DesktopBot)
para o ciclo de vida da execução (`action()`); a lógica de negócio é Django ORM (consulta)
e Mailtrap Send API (envio via HTTP). Pensado para rodar periodicamente (a cada 15-30 min),
não uma vez por dia — ver automacao/README.md.

O campo `Ocorrencia.alerta_grave_enviado_em` evita alertar duas vezes pela mesma ocorrência:
só é marcado depois que pelo menos um destinatário recebeu o e-mail com sucesso.

Uso manual:
    venv\\Scripts\\python.exe automacao\\alerta_grave.py
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
from ocorrencias.models import DestinatarioRelatorio, Ocorrencia  # noqa: E402
from ocorrencias.relatorios_service import ocorrencias_graves_pendentes_de_alerta  # noqa: E402


class AlertaGraveBot(DesktopBot):
    def action(self, execution=None):
        log = logger_config.configurar_logger("automacao.alerta_grave", "alerta_grave.log")
        log.info("=== Início da execução ===")

        try:
            pendentes = list(ocorrencias_graves_pendentes_de_alerta())
            if not pendentes:
                log.info("Nenhuma ocorrência grave pendente de alerta. Nada a enviar.")
                return

            log.info("%s ocorrência(s) grave(s) pendente(s) de alerta.", len(pendentes))
            cfg = carregar_configuracao_email()

            # Alertas são urgentes: valem em qualquer dia, ao contrário do panorama
            # diário (que respeita recebe_segunda/terca/...). Ajuste aqui se quiser
            # restringir por dia da semana também.
            destinatarios = DestinatarioRelatorio.objects.filter(ativo=True)
            if not destinatarios.exists():
                log.warning("Nenhum destinatário ativo cadastrado. Nada a enviar.")
                return

            enviados, falhas = 0, 0
            for destinatario in destinatarios:
                try:
                    email_service.enviar_alerta_grave(cfg, destinatario, pendentes)
                    enviados += 1
                    log.info(
                        "Alerta enviado para %s (%s ocorrência(s))",
                        destinatario.email_efetivo, len(pendentes),
                    )
                except Exception:
                    falhas += 1
                    log.exception("Falha ao enviar alerta para %s", destinatario.email_efetivo)

            if enviados > 0:
                agora = timezone.now()
                ids = [o.pk for o in pendentes]
                Ocorrencia.objects.filter(pk__in=ids).update(alerta_grave_enviado_em=agora)
                log.info("Marcada(s) %s ocorrência(s) como alertada(s).", len(ids))
            else:
                log.warning("Nenhum e-mail enviado com sucesso; ocorrências continuam pendentes.")

            log.info("=== Fim da execução — enviados=%s falhas=%s ===", enviados, falhas)
        except Exception:
            log.exception("Erro fatal na execução do robô de alerta.")
            raise


if __name__ == "__main__":
    AlertaGraveBot.main()
