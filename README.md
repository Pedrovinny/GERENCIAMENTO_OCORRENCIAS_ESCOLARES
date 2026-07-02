# Sistema de Gerenciamento de Ocorrências Escolares

Sistema web desenvolvido com **Django 5** para registro, acompanhamento e geração de relatórios de ocorrências disciplinares no **IFAM Campus Humaitá**.

---

## Funcionalidades

### Dashboard
- Métricas em tempo real: total de ocorrências, ocorrências do dia, distribuição por gravidade
- Estatísticas de professores, alunos e cursos cadastrados
- Gráficos interativos: ocorrências por mês, por curso, por professor, por tipo e por turma
- Lista das ocorrências mais recentes

### Ocorrências
- Registro de ocorrências vinculando professor, aluno, horário e tipo
- Níveis de gravidade: **Grave**, **Média** e **Leve**
- Status de acompanhamento: **Aberta**, **Em Análise**, **Resolvida**, **Arquivada**
- Anexo de arquivos (PDF, JPG, PNG)
- Trilha de auditoria automática (criado por / atualizado por / timestamps)

### Cadastros Administrativos
- **Professores**: nome, SIAPE, e-mail, telefone, situação (ativo/inativo)
- **Alunos**: matrícula, nome, turma, curso
- **Cursos**: nome do curso
- **Turmas**: nome, curso, turno (matutino/vespertino/noturno/integral), ano letivo
- **Tipos de Ocorrência**: descrição e nível de gravidade
- **Horários**: dia da semana, horário de início/fim, período de aula
- **Usuários**: autenticação com controle de acesso baseado em perfil

### Relatórios e Exportação
- Filtros avançados: professor, aluno, curso, tipo, status, intervalo de datas
- Exportação para **CSV**, **Excel** e **PDF**
- Versão para impressão

### Busca AJAX
- Busca de alunos por matrícula ou nome com preenchimento automático do formulário
- Busca de professores por nome ou SIAPE com preenchimento automático

---

## Tecnologias

| Categoria | Tecnologia |
|-----------|------------|
| Backend | Python 3 · Django 5.1 |
| Banco de dados | SQLite 3 |
| Frontend | Bootstrap 5.3 · Bootstrap Icons 1.11 |
| Exportação | openpyxl 3.1 (Excel) · ReportLab 5.0 (PDF) |
| Imagens | Pillow 12.2 |

---

## Pré-requisitos

- Python 3.10 ou superior
- pip

---

## Instalação e Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/Pedrovinny/GERENCIAMENTO_OCORRENCIAS_ESCOLARES.git
cd GERENCIAMENTO_OCORRENCIAS_ESCOLARES
```

### 2. Crie e ative o ambiente virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Execute as migrações do banco de dados

```bash
python manage.py migrate
```

### 5. Configure os grupos de permissão

```bash
python manage.py setup_grupos
```

### 6. Crie o superusuário

```bash
python manage.py createsuperuser
```

### 7. Inicie o servidor de desenvolvimento

```bash
python manage.py runserver
```

Acesse em: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Estrutura do Projeto

```
GERENCIAMENTO_OCORRENCIAS_ESCOLARES/
├── manage.py
├── requirements.txt
│
├── dados/                       # Banco SQLite (db.sqlite3)
│
├── teste/                       # Configuração principal do Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── ocorrencias/                 # App principal
│   ├── models.py                # Modelos: Curso, Turma, Professor, Aluno, Ocorrencia...
│   ├── views.py                 # 30+ views com CRUD, dashboard, relatórios e AJAX
│   ├── forms.py                 # Formulários com validação e estilo Bootstrap
│   ├── urls.py                  # 75+ rotas
│   ├── permissions.py           # Mixin de controle de acesso
│   ├── management/commands/
│   │   └── setup_grupos.py      # Comando para criar grupos e permissões
│   ├── templatetags/
│   │   └── ocorrencias_extras.py
│   └── templates/ocorrencias/   # Templates HTML
│
└── static/                      # Arquivos estáticos (logo IFAM)
```

---

## Modelos de Dados

| Modelo | Descrição |
|--------|-----------|
| `Curso` | Cursos/áreas do campus |
| `Turma` | Turmas com curso, turno e ano letivo |
| `Professor` | Dados dos docentes (SIAPE) |
| `Aluno` | Dados dos discentes (matrícula, turma) |
| `TipoOcorrencia` | Tipos de ocorrência com nível de gravidade |
| `Horario` | Horários de aula por dia e período |
| `PerfilUsuario` | Perfil estendido do usuário (one-to-one com User) |
| `Ocorrencia` | Registro principal da ocorrência |
| `AnexoOcorrencia` | Arquivos anexados a cada ocorrência |

---

## Controle de Acesso

O sistema possui dois perfis de usuário:

| Perfil | Permissões |
|--------|------------|
| **Administrador** | Acesso total: CRUD de todos os cadastros, gestão de usuários e configurações |
| **Usuário** | Visualização dos cadastros, criação e consulta de ocorrências |

Os grupos e permissões são criados automaticamente pelo comando `setup_grupos`.

---

## Principais Rotas

| URL | Descrição |
|-----|-----------|
| `/` | Dashboard principal |
| `/login/` | Autenticação |
| `/ocorrencias/` | Lista de ocorrências |
| `/ocorrencias/nova/` | Registrar nova ocorrência |
| `/ocorrencias/<id>/` | Detalhe da ocorrência |
| `/professores/` | Gestão de professores |
| `/alunos/` | Gestão de alunos |
| `/turmas/` | Gestão de turmas |
| `/cursos/` | Gestão de cursos |
| `/tipos/` | Tipos de ocorrência |
| `/horarios/` | Horários de aula |
| `/usuarios/` | Gestão de usuários |
| `/relatorio/` | Relatórios com filtros |
| `/relatorio/excel/` | Exportar para Excel |
| `/relatorio/pdf/` | Exportar para PDF |
| `/relatorio/csv/` | Exportar para CSV |

---

## Configurações de Produção

Antes de implantar em produção, altere as seguintes configurações em `teste/settings.py`:

1. **`DEBUG = False`**
2. **`SECRET_KEY`**: utilize uma variável de ambiente
3. **`ALLOWED_HOSTS`**: adicione o domínio do servidor
4. Substitua o SQLite por um banco de dados mais robusto (PostgreSQL recomendado)
5. Configure o servidor de arquivos estáticos e de mídia

---

## Licença

Este projeto foi desenvolvido para uso interno no **IFAM Campus Humaitá**.
