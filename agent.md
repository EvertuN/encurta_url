# URL Shortener

Um serviço moderno e simples de **encurtamento de URLs**, desenvolvido para demonstrar conceitos de backend, cache, persistência de dados, concorrência e coleta de métricas.

O projeto recebe uma URL longa, gera um código curto e único, permite o redirecionamento para a URL original e registra informações sobre cada acesso.

---

## 1. Objetivo

Criar uma API de encurtamento de URLs com uma interface web minimalista.

O sistema deve permitir:

* Criar URLs curtas.
* Redirecionar usuários para a URL original.
* Registrar acessos.
* Consultar estatísticas.
* Utilizar cache para reduzir consultas ao banco.
* Garantir unicidade dos códigos gerados.
* Ser executável localmente através de Docker.
* Possuir documentação clara da API.

O projeto deve priorizar **simplicidade, desempenho e organização**, evitando complexidade desnecessária.

---

# 2. Conceito

O fluxo principal do sistema é:

```text
Usuário
   │
   │ URL longa
   ▼
Frontend
   │
   │ POST /urls
   ▼
FastAPI
   │
   ├──────────────► PostgreSQL
   │                    │
   │                    ▼
   │              URL + código
   │
   ▼
URL curta
```

Quando alguém acessa o código curto:

```text
GET /a8Kx91
      │
      ▼
    Redis
      │
   ┌──┴──┐
   │     │
  HIT   MISS
   │     │
   │     ▼
   │ PostgreSQL
   │     │
   │     ▼
   │   Redis
   │
   ▼
HTTP 302
   │
   ▼
URL original
```

Ao mesmo tempo, o acesso deve gerar um evento de métrica.

---

# 3. Stack

## Backend

### Python

Linguagem principal do projeto.

### FastAPI

Framework utilizado para construção da API REST.

Responsabilidades:

* Receber URLs.
* Gerar códigos.
* Realizar redirecionamentos.
* Consultar estatísticas.
* Validar requisições.
* Documentar a API através de OpenAPI/Swagger.

### Uvicorn

Servidor ASGI utilizado para executar a aplicação FastAPI.

---

# 4. Banco de dados

## PostgreSQL

Banco relacional principal.

Responsável por armazenar:

* URLs cadastradas.
* Códigos curtos.
* Datas de criação.
* Expiração opcional.
* Eventos de acesso.
* Informações analíticas.

### Modelo conceitual

#### URLs

```text
urls
├── id
├── short_code
├── original_url
├── created_at
└── expires_at
```

#### Eventos de acesso

```text
click_events
├── id
├── url_id
├── ip
├── user_agent
├── referer
└── clicked_at
```

Relacionamento:

```text
URL
 │
 ├── Click Event
 ├── Click Event
 ├── Click Event
 └── Click Event
```

O campo `short_code` deve possuir uma restrição de unicidade no banco.

---

# 5. Cache

## Redis

Redis será utilizado como camada de cache para URLs frequentemente acessadas.

Estrutura conceitual:

```text
short_code → original_url
```

Exemplo:

```text
a8Kx91 → https://exemplo.com/produto/123
```

O objetivo é evitar consultas desnecessárias ao PostgreSQL durante os redirecionamentos.

### Estratégia

Utilizar o padrão **Cache-Aside**:

```text
Request
   │
   ▼
Redis
   │
   ├── HIT ──────► Redirect
   │
   └── MISS
          │
          ▼
     PostgreSQL
          │
          ▼
        Redis
          │
          ▼
       Redirect
```

O Redis não será considerado a fonte principal dos dados.

O PostgreSQL continuará sendo a fonte de verdade.

---

# 6. Geração dos códigos

Cada URL deve receber um código curto e único.

Exemplo:

```text
a8Kx91
K72mQa
x91Lp2
```

O sistema deve considerar concorrência.

Não deve depender somente de:

```text
verificar se existe
        ↓
se não existe
        ↓
criar
```

porque duas requisições simultâneas podem gerar o mesmo código.

A unicidade deve ser garantida principalmente pelo banco de dados através de uma constraint `UNIQUE`.

Em caso de colisão, a aplicação deve gerar outro código.

---

# 7. Redirecionamento

O endpoint de redirecionamento será responsável por localizar a URL original e retornar um redirecionamento HTTP.

Exemplo:

```text
GET /a8Kx91
```

Resposta:

```text
HTTP 302 Found

Location: https://exemplo.com/produto/123
```

O projeto deve utilizar inicialmente **302 Temporary Redirect**.

A possibilidade de utilização de `301 Permanent Redirect` pode ser avaliada posteriormente.

### Motivo

O `302` permite maior flexibilidade durante o desenvolvimento do serviço e evita tratar o redirecionamento como permanentemente armazenável por clientes e intermediários.

---

# 8. Coleta de métricas

Cada acesso a uma URL curta deve gerar um evento.

Informações coletadas:

```text
IP
User-Agent
Referer
Timestamp
URL acessada
```

Exemplo conceitual:

```json
{
  "short_code": "a8Kx91",
  "ip": "189.xxx.xxx.xxx",
  "user_agent": "Mozilla/5.0",
  "referer": "https://google.com/",
  "clicked_at": "2026-09-09T12:15:32Z"
}
```

Esses eventos poderão posteriormente ser utilizados para gerar estatísticas.

---

# 9. Estatísticas

O sistema deve permitir consultar informações básicas de uma URL.

Exemplo:

```http
GET /urls/a8Kx91/stats
```

Resposta esperada:

```json
{
  "short_code": "a8Kx91",
  "total_clicks": 1532,
  "last_click": "2026-09-09T12:15:32Z"
}
```

Possíveis métricas futuras:

* Total de acessos.
* Acessos por dia.
* Acessos por hora.
* Principais referenciadores.
* User-Agent.
* País/região, caso posteriormente seja adicionada uma solução de geolocalização.
* Visitantes únicos, utilizando uma estratégia apropriada de identificação.

---

# 10. API

A API deve inicialmente possuir poucos endpoints.

### Criar URL

```http
POST /urls
```

Entrada:

```json
{
  "url": "https://exemplo.com/produto/123"
}
```

Resposta:

```json
{
  "short_code": "a8Kx91",
  "short_url": "https://dominio.com/a8Kx91"
}
```

---

### Redirecionar

```http
GET /{short_code}
```

Responsável pelo redirecionamento para a URL original.

---

### Consultar informações

```http
GET /urls/{short_code}
```

Retorna informações básicas da URL.

---

### Estatísticas

```http
GET /urls/{short_code}/stats
```

Retorna as métricas de acesso.

---

### Excluir URL

```http
DELETE /urls/{short_code}
```

Remove ou desativa uma URL encurtada.

---

# 11. Frontend

O frontend deve ser propositalmente simples.

A primeira versão será composta por **um único HTML**, utilizando:

* HTML5
* CSS3
* JavaScript vanilla

Não existe necessidade de React, Vue ou outro framework para a interface inicial.

## Interface

A página principal deve possuir:

```text
Shortly

Links longos.
Agora, simples.

[ Cole sua URL aqui... ] [ Encurtar ]

Seu link curto
shortly.com/a8Kx91
```

Características visuais:

* Minimalista.
* Responsivo.
* Fundo claro.
* Tipografia limpa.
* Poucos elementos.
* Interface semelhante a produtos SaaS modernos.
* Boa experiência em desktop e mobile.

---

# 12. Estrutura do projeto

Estrutura sugerida:

```text
url-shortener/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── database/
│   │
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   └── index.html
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

A separação entre `routes`, `services` e `repositories` deve manter a lógica de negócio organizada e facilitar testes e manutenção.

---

# 13. Docker

O ambiente de desenvolvimento deve ser executável através de Docker Compose.

Serviços principais:

```text
docker-compose
│
├── api
├── postgres
└── redis
```

Conceitualmente:

```text
             Docker Compose
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
    FastAPI   PostgreSQL   Redis
```

Isso permite que o projeto seja executado de maneira consistente em diferentes ambientes.

---

# 14. Configuração

Informações sensíveis não devem ser armazenadas diretamente no código.

Utilizar variáveis de ambiente:

```text
DATABASE_URL
REDIS_URL
BASE_URL
APP_ENV
```

Exemplo:

```text
.env
```

O arquivo `.env` real não deve ser enviado ao GitHub.

Um `.env.example` deve ser disponibilizado.

---

# 15. Testes

O backend deve possuir testes automatizados utilizando **pytest**.

Áreas importantes:

* Criação de URL.
* Validação de URL.
* Geração de códigos.
* Colisão de códigos.
* Redirecionamento.
* URL inexistente.
* Registro de eventos.
* Consulta de estatísticas.
* Integração com Redis.
* Integração com PostgreSQL.

O objetivo não é possuir centenas de testes, mas cobrir as partes importantes da lógica.

---

# 16. Qualidade de código

Ferramentas recomendadas:

* **Ruff** — lint e formatação.
* **pytest** — testes.
* **Alembic** — migrations.
* **Pydantic** — validação.
* **SQLAlchemy** — ORM.
* **OpenAPI/Swagger** — documentação.

O código deve priorizar:

* Simplicidade.
* Separação de responsabilidades.
* Tipagem.
* Funções pequenas.
* Nomes claros.
* Tratamento adequado de erros.

---

# 17. Segurança e privacidade

Como o sistema registra informações de acesso, deve existir preocupação com privacidade.

O IP deve ser tratado como dado potencialmente sensível e não deve ser exposto nas estatísticas públicas.

O sistema deve evitar:

* Exposição desnecessária de IP.
* SQL injection.
* URLs inválidas.
* Dados arbitrariamente grandes.
* Abuso da API.
* Criação automatizada excessiva de URLs.

Recursos futuros:

* Rate limiting.
* CAPTCHA em cenários de abuso.
* Limite de tamanho da URL.
* Bloqueio de domínios maliciosos.
* Autenticação para gerenciamento de URLs.

---

# 18. Domínio

O sistema pode funcionar inicialmente sem domínio:

```text
localhost:8000
```

Para produção, poderá utilizar um domínio próprio.

Exemplo:

```text
encurta.dev
```

Então os links poderiam ser:

```text
https://encurta.dev/a8Kx91
```

O domínio deve apontar para a infraestrutura responsável por executar a API.

HTTPS deve ser utilizado em produção.

---

# 19. Infraestrutura

Arquitetura inicial:

```text
                  Internet
                     │
                     ▼
              ┌─────────────┐
              │   Domínio   │
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │   FastAPI   │
              └──────┬──────┘
                     │
             ┌───────┴───────┐
             ▼               ▼
        PostgreSQL          Redis
             │
             ▼
       Click Events
```

A arquitetura deve permanecer simples enquanto o volume do projeto for pequeno.

---

# 20. Possíveis evoluções

Depois do MVP, o projeto pode evoluir para:

### Autenticação

Usuários poderiam criar e administrar seus próprios links.

### Expiração

URLs poderiam possuir data de validade.

```json
{
  "url": "https://exemplo.com",
  "expires_at": "2026-12-31T23:59:59Z"
}
```

### Dashboard

Interface para visualizar:

* Links criados.
* Total de cliques.
* Gráficos.
* Referenciadores.
* Histórico.

### Rate limiting

Limitação de requisições por IP ou usuário.

### Processamento assíncrono

Caso o volume de eventos cresça, a coleta de métricas poderá ser desacoplada do redirecionamento através de uma fila ou sistema de eventos.

Exemplo futuro:

```text
Request
   │
   ├──────────────► Redirect
   │
   └──► Event Queue
             │
             ▼
           Worker
             │
             ▼
        PostgreSQL
```

Tecnologias como Redis Streams, RabbitMQ ou Kafka poderiam ser avaliadas somente quando houver necessidade real.

---

# 21. Escopo do MVP

O MVP deve conter somente:

* [x] Criação de URL curta.
* [x] Código único.
* [x] Redirecionamento HTTP.
* [x] PostgreSQL.
* [x] Redis.
* [x] Registro de cliques.
* [x] Estatísticas básicas.
* [x] Frontend HTML/CSS/JS.
* [x] Docker Compose.
* [x] Testes automatizados.
* [x] Documentação da API.

Não faz parte do MVP:

* Autenticação.
* Dashboard complexo.
* Aplicativo mobile.
* Microsserviços.
* Kubernetes.
* Kafka.
* Sistema avançado de geolocalização.
* Arquitetura distribuída.

---

# 22. Objetivo técnico do projeto

O projeto não deve ser tratado apenas como um CRUD.

O principal objetivo é demonstrar conhecimentos de:

```text
REST API
   +
Banco relacional
   +
Cache
   +
Concorrência
   +
HTTP
   +
Métricas
   +
Testes
   +
Docker
   +
Deploy
```

O diferencial está em entender **por que cada componente existe**, e não simplesmente adicionar tecnologias ao projeto.

---

# 23. Resultado esperado

Ao final, o projeto deverá permitir que alguém:

1. Acesse a página.
2. Cole uma URL.
3. Clique em "Encurtar".
4. Receba um link curto.
5. Acesse o link curto.
6. Seja redirecionado para a URL original.
7. Tenha o acesso registrado.
8. Consulte as estatísticas daquele link.

Exemplo completo:

```text
https://meusite.com/artigo/muito-grande/123
                    │
                    ▼
              Encurtar
                    │
                    ▼
          https://encurta.dev/a8Kx91
                    │
                    ▼
                 Acesso
                    │
             ┌──────┴──────┐
             ▼             ▼
           Redis       Click Event
             │             │
             ▼             ▼
          Redirect      PostgreSQL
```

O resultado deve ser um projeto pequeno, funcional e tecnicamente bem estruturado, capaz de demonstrar fundamentos reais de desenvolvimento backend e preparação para ambientes de produção.
