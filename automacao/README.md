# Automação — Panorama Diário de Ocorrências por E-mail

Robô que roda **uma vez por dia** e envia, por e-mail, o panorama completo das
ocorrências registradas no dia para os destinatários cadastrados no painel
"Destinatários de Relatório" (admin do sistema, menu Configurações).

> **Atenção:** a configuração atual usa um Sending Domain de **produção** no
> Mailtrap — os e-mails enviados por este robô são reais e chegam de fato na
> caixa de entrada dos destinatários cadastrados (não é uma sandbox de teste).
> Só cadastre destinatários em `/destinatarios/` que devem mesmo receber o
> relatório.

## O que este robô faz e o que ele não faz

Ele usa **BotCity Framework** (edição local/gratuita, biblioteca
`botcity-framework-core`), **sem** BotCity Maestro/nuvem. O `DesktopBot` do
BotCity é usado aqui apenas pelo seu ciclo de vida de execução (`action()`) —
não há nenhuma automação de tela/clique/OCR neste robô, porque a tarefa é
puramente de backend: consultar o banco de dados (via Django ORM), gerar um
PDF (`reportlab`) e enviar um e-mail via **Mailtrap Send API** (HTTP,
autenticada por token — não SMTP), reaproveitando exatamente a mesma lógica
de relatório usada nas telas web do sistema (`ocorrencias/relatorios_service.py`).

## Estrutura

```
automacao/
├── bot.py             # ponto de entrada do robô
├── config.py           # carrega automacao/.env
├── email_service.py    # monta e envia o e-mail (HTML + PDF anexado)
├── logger_config.py    # log com rotação diária em automacao/logs/
├── run_diario.bat      # wrapper para o Windows Task Scheduler
├── .env.example         # modelo de configuração (copiar para .env)
└── logs/                # gerado automaticamente na primeira execução
```

## Configuração

1. Instale as dependências (no ambiente virtual do projeto):
   ```
   venv\Scripts\pip install -r requirements.txt
   ```
2. Copie `automacao\.env.example` para `automacao\.env` e preencha com as
   credenciais da **Mailtrap Send API** (Sending Domains → seu domínio →
   Integration → API, no painel do Mailtrap):
   - `MAILTRAP_API_TOKEN`: o API Token do Mailtrap (usado como Bearer token).
   - `MAILTRAP_API_URL`: normalmente não precisa mudar
     (`https://send.api.mailtrap.io/api/send`, endpoint de produção).
   - `MAILTRAP_FROM_EMAIL`: precisa ser um e-mail do **Sending Domain já
     verificado** no painel do Mailtrap — se não estiver verificado, a API
     recusa o envio.
   - `MAILTRAP_FROM_NAME`: nome do remetente exibido no e-mail.
   - **`automacao\.env` nunca deve ser commitado** (já está no `.gitignore`).
3. Cadastre ao menos um destinatário em `/destinatarios/` no sistema, marcando
   os dias da semana em que ele deve receber o relatório.

## Execução manual

```
venv\Scripts\python.exe automacao\bot.py
```

Acompanhe o resultado em `automacao\logs\panorama_diario.log` (também é
exibido no console). Se não houver destinatários configurados para o dia
atual, o robô registra um aviso e encerra normalmente — isso não é uma falha.

## Agendamento (Windows Task Scheduler)

1. Abra o **Agendador de Tarefas** → **Criar Tarefa Básica**.
2. Gatilho: **Diariamente**, no horário desejado (ex.: 18:00, após o horário
   normal de registro de ocorrências).
3. Ação: **Iniciar um programa** → selecione `automacao\run_diario.bat`.
4. Em "Iniciar em (opcional)", aponte para a raiz do projeto (a pasta que
   contém `manage.py`).
5. Nas opções da tarefa, marque **"Executar mesmo que o usuário não esteja
   conectado"** apenas se a máquina permanecer ligada; caso contrário, use
   **"Executar somente quando o usuário estiver conectado"**.
6. Após criar, clique com o botão direito na tarefa → **Executar**, para
   validar manualmente que o caminho relativo do `.bat` resolve corretamente
   fora de um terminal aberto manualmente. Confira o log gerado.

## Solução de problemas

- **`RuntimeError: Variáveis de ambiente ausentes...`** — falta preencher
  `automacao\.env` (copie de `.env.example`).
- **`EnvioEmailError` com status 401/403** — token inválido/expirado; gere um
  novo API Token no painel do Mailtrap.
- **`EnvioEmailError` com status 400 mencionando o domínio remetente** —
  `MAILTRAP_FROM_EMAIL` não pertence a um Sending Domain verificado no
  Mailtrap; verifique o domínio no painel ou use um e-mail de um domínio já
  aprovado.
- **"Nenhum destinatário ativo configurado"** — não é erro; verifique se
  algum destinatário tem o dia da semana atual marcado e está "Ativo".
