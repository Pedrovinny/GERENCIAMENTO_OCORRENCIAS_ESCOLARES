"""Logger com rotação diária para as execuções do robô, gravado em automacao/logs/.

Necessário porque a automação roda localmente via Task Scheduler, sem um
orquestrador central (Maestro) para consultar histórico de execuções.
"""
import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"


def configurar_logger(
    nome: str = "automacao.panorama_diario",
    arquivo_log: str = "panorama_diario.log",
) -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger(nome)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formato = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    arquivo = logging.handlers.TimedRotatingFileHandler(
        LOG_DIR / arquivo_log, when="midnight", backupCount=30, encoding="utf-8"
    )
    arquivo.setFormatter(formato)
    logger.addHandler(arquivo)

    console = logging.StreamHandler()
    console.setFormatter(formato)
    logger.addHandler(console)

    return logger
