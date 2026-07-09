"""Monta e envia o e-mail do panorama diário (HTML + PDF anexado) via Mailtrap Send API.

Só pode ser importado depois de `django.setup()` (usa `render_to_string`).
"""
import base64

import requests
from django.template.loader import render_to_string

from .config import ConfiguracaoEmail


class EnvioEmailError(Exception):
    """Levantada quando a Mailtrap Send API recusa ou falha ao enviar o e-mail."""


def montar_corpo_html(destinatario, panorama: dict) -> str:
    return render_to_string(
        "automacao/email_panorama.html",
        {"destinatario": destinatario, "panorama": panorama},
    )


def montar_payload(cfg: ConfiguracaoEmail, destinatario, panorama: dict, pdf_bytes: bytes) -> dict:
    texto_simples = (
        f"Panorama de ocorrências de {panorama['data'].strftime('%d/%m/%Y')}. "
        f"Total: {panorama['total']} ocorrência(s). Veja o PDF em anexo para o detalhamento completo."
    )
    return {
        "from": {"email": cfg.from_email, "name": cfg.from_name},
        "to": [{"email": destinatario.email_efetivo}],
        "subject": f"Panorama de Ocorrências — {panorama['data'].strftime('%d/%m/%Y')}",
        "text": texto_simples,
        "html": montar_corpo_html(destinatario, panorama),
        "attachments": [
            {
                "content": base64.b64encode(pdf_bytes).decode("ascii"),
                "filename": f"panorama_{panorama['data'].isoformat()}.pdf",
                "type": "application/pdf",
                "disposition": "attachment",
            }
        ],
        "category": "Panorama Diário de Ocorrências",
    }


def _enviar_via_api(cfg: ConfiguracaoEmail, destinatario, payload: dict) -> None:
    resposta = requests.post(
        cfg.api_url,
        json=payload,
        headers={
            "Authorization": f"Bearer {cfg.api_token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )

    if not resposta.ok:
        raise EnvioEmailError(
            f"Mailtrap API retornou {resposta.status_code} para {destinatario.email_efetivo}: "
            f"{resposta.text}"
        )


def enviar_panorama(cfg: ConfiguracaoEmail, destinatario, panorama: dict, pdf_bytes: bytes) -> None:
    payload = montar_payload(cfg, destinatario, panorama, pdf_bytes)
    _enviar_via_api(cfg, destinatario, payload)


def montar_corpo_html_alerta(destinatario, ocorrencias) -> str:
    return render_to_string(
        "automacao/email_alerta_grave.html",
        {"destinatario": destinatario, "ocorrencias": ocorrencias},
    )


def montar_payload_alerta(cfg: ConfiguracaoEmail, destinatario, ocorrencias) -> dict:
    total = len(ocorrencias)
    plural = "s" if total != 1 else ""
    texto_simples = (
        f"{total} ocorrência{plural} grave{plural} em aberto exige{'m' if plural else ''} atenção imediata. "
        "Veja os detalhes no e-mail em HTML ou acesse o sistema."
    )
    return {
        "from": {"email": cfg.from_email, "name": cfg.from_name},
        "to": [{"email": destinatario.email_efetivo}],
        "subject": f"[Alerta] {total} ocorrência(s) grave(s) em aberto",
        "text": texto_simples,
        "html": montar_corpo_html_alerta(destinatario, ocorrencias),
        "category": "Alerta de Ocorrência Grave",
    }


def enviar_alerta_grave(cfg: ConfiguracaoEmail, destinatario, ocorrencias) -> None:
    payload = montar_payload_alerta(cfg, destinatario, ocorrencias)
    _enviar_via_api(cfg, destinatario, payload)
