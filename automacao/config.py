"""Carrega e valida as configurações da Mailtrap Send API (produção) usadas pelo robô,
a partir de `automacao/.env` (nunca commitado — ver `.env.example`).

Usa a API HTTP de envio do Mailtrap (send.api.mailtrap.io), autenticada por
Bearer token, e não SMTP — o domínio remetente precisa estar verificado no
painel do Mailtrap (Sending Domains).
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

AUTOMACAO_DIR = Path(__file__).resolve().parent
load_dotenv(AUTOMACAO_DIR / ".env")

_VARIAVEIS_OBRIGATORIAS = [
    "MAILTRAP_API_TOKEN",
    "MAILTRAP_FROM_EMAIL",
]


@dataclass(frozen=True)
class ConfiguracaoEmail:
    api_token: str
    api_url: str
    from_email: str
    from_name: str


def carregar_configuracao_email() -> ConfiguracaoEmail:
    faltando = [nome for nome in _VARIAVEIS_OBRIGATORIAS if not os.environ.get(nome)]
    if faltando:
        raise RuntimeError(
            f"Variáveis de ambiente ausentes em automacao/.env: {', '.join(faltando)}. "
            "Copie automacao/.env.example para automacao/.env e preencha com as credenciais do Mailtrap."
        )

    return ConfiguracaoEmail(
        api_token=os.environ["MAILTRAP_API_TOKEN"],
        api_url=os.environ.get("MAILTRAP_API_URL", "https://send.api.mailtrap.io/api/send"),
        from_email=os.environ["MAILTRAP_FROM_EMAIL"],
        from_name=os.environ.get("MAILTRAP_FROM_NAME", "Ocorrências Escolares"),
    )
