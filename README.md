# AGIO NEWS

Portal diário de notícias de Arquitetura, Engenharia e Construção, curado por IA e publicado como Artifact em URL fixa.

## O que é

O AGIO NEWS é um portal multiuso gerado todos os dias a partir de fontes RSS do setor AEC (Brasil e internacional). Cada edição reúne quatro vistas, organizadas como pranchas de projeto:

- **A-01 EDIÇÃO** — boletim do dia: destaque, seções Arquitetura / Engenharia & Construção / BIM & Tecnologia / Nacional-BR e notas do editor.
- **A-02 RADAR** — cartões estratégicos (sinal → leitura → jogada) com horizonte e escalas de impacto/esforço, pensados para profissionais e escritórios AEC no Brasil.
- **A-03 CONTEÚDO** — sementes de conteúdo prontas para copiar e publicar no LinkedIn, Instagram ou Substack.
- **A-04 ARQUIVO** — histórico de todas as edições.

Portal publicado: https://claude.ai/code/artifact/a4dbeb62-d306-4a49-b262-343337bbf0b3

## Como funciona

```
 fontes RSS                curadoria IA              data file
 (feeds diretos +   -->    (12-18 notícias,    -->   portal/data/
  Google News RSS)          resumos pt-BR,           YYYY-MM-DD.json
                            dedup 7 dias)                 |
                                                          v
                           Artifact           <--    build
                           (republicado na           (build_portal.py ->
                            mesma URL fixa)           portal/index.html)
```

As fontes são 100% RSS: feeds diretos (ArchDaily Brasil, Dezeen, The Architect's Newspaper, Archinect, Construction Dive, Global Construction Review, Revista PROJETO) e Google News RSS para sites sem feed próprio (CBIC, AECweb, CAUBR). A memória do sistema é o próprio repositório — uma edição por dia em `portal/data/`, com deduplicação contra os últimos 7 dias. As imagens são embutidas como data URI em base64, porque o Artifact bloqueia requisições a hosts externos.

## Estrutura do repositório

```
aec-news-daily-skill/
├── SKILL.md              # A skill: fontes, fluxo diário, schema, diretrizes
├── scripts/
│   ├── fetch_sources.py  # Coleta dos feeds e busca de imagens (data URI)
│   └── build_portal.py   # Gera portal/index.html a partir do template + data files
└── portal/
    ├── template.html     # Template do portal
    ├── data/             # Uma edição por dia: YYYY-MM-DD.json
    └── index.html        # Portal gerado (publicado como Artifact)
```

## Automação

Uma Routine do Claude Code roda todos os dias às 8h de Brasília (cron `0 11 * * *` UTC), abrindo uma sessão nova que executa o fluxo completo: coleta, curadoria, escrita, build, republicação do Artifact na URL fixa e commit dos dados.

## Execução manual

Para gerar a edição de hoje sem esperar a Routine, cole num agente (Claude Code) com acesso a este repositório:

```
Gere a edição de hoje do AGIO NEWS seguindo o SKILL.md deste repositório:
colete as fontes RSS com scripts/fetch_sources.py, cure 12-18 notícias com
resumos em pt-BR (dedup contra os últimos 7 dias em portal/data/), escreva
radar, sementes de conteúdo e notas do editor, grave portal/data/ de hoje,
rode scripts/build_portal.py, republique o Artifact na URL fixa do portal
e commite os dados.
```

## Licença

MIT
