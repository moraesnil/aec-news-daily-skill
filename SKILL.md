---
name: aec-news-daily-skill
description: |
  Gera a edição diária do portal AEC NEWS — boletim curado de notícias de
  Arquitetura, Engenharia e Construção (Brasil e internacional), publicado
  como Artifact HTML em URL fixa. Use esta skill quando o usuário pedir para
  gerar, atualizar ou republicar a edição do dia do AEC NEWS, ou quando a
  Routine diária agendada disparar a produção da edição.
---

# AEC NEWS — Edição Diária

Esta skill produz a edição diária do portal AEC NEWS: coleta notícias de fontes RSS do setor AEC (Arquitetura, Engenharia e Construção), cura 12–18 matérias com resumos em pt-BR, escreve radar estratégico e sementes de conteúdo, grava o data file do dia em `portal/data/`, regenera o `portal/index.html` e republica o Artifact na URL fixa do portal. A memória do sistema é o próprio repositório: cada edição vive em `portal/data/YYYY-MM-DD.json`, e a deduplicação é feita contra os data files dos últimos 7 dias. A v1 usava Notion e Apify; a v2 eliminou ambos — o fluxo é 100% RSS e git.

Portal publicado: https://claude.ai/code/artifact/a4dbeb62-d306-4a49-b262-343337bbf0b3

## Fontes

Todas as fontes são RSS. Sites sem feed próprio entram via Google News RSS, no padrão `https://news.google.com/rss/search?q=site:DOMINIO&hl=pt-BR&gl=BR&ceid=BR:pt-419`.

| Fonte | Feed | Tipo |
|-------|------|------|
| ArchDaily Brasil | https://feeds.feedburner.com/ArchdailyBR | RSS direto |
| Dezeen | https://dezeen.com/feed | RSS direto |
| The Architect's Newspaper | https://archpaper.com/feed | RSS direto |
| Archinect | https://archinect.com/feed/news | RSS direto |
| Construction Dive | https://constructiondive.com/feeds/news/ | RSS direto |
| Global Construction Review | https://globalconstructionreview.com/feed/ | RSS direto |
| Revista PROJETO | https://revistaprojeto.com.br/feed/ | RSS direto |
| CBIC | https://news.google.com/rss/search?q=site:cbic.org.br&hl=pt-BR&gl=BR&ceid=BR:pt-419 | Google News RSS |
| AECweb | https://news.google.com/rss/search?q=site:aecweb.com.br&hl=pt-BR&gl=BR&ceid=BR:pt-419 | Google News RSS |
| CAUBR | https://news.google.com/rss/search?q=site:caubr.gov.br&hl=pt-BR&gl=BR&ceid=BR:pt-419 | Google News RSS |

## As quatro pranchas do portal

O portal tem quatro vistas, nomeadas como pranchas de projeto:

- **A-01 EDIÇÃO** — o boletim do dia: destaque + seções Arquitetura (ARQ), Engenharia & Construção (ENG), BIM & Tecnologia (TEC) e Nacional-BR (BRA), mais notas do editor.
- **A-02 RADAR** — 3 a 5 cartões estratégicos no formato sinal → leitura → jogada, com horizonte (AGORA / 6M / 24M) e escalas de impacto e esforço de 1 a 3.
- **A-03 CONTEÚDO** — 2 a 3 sementes de conteúdo prontas para copiar (LinkedIn, Instagram, Substack), cada uma com hook, draft em pt-BR e hashtags.
- **A-04 ARQUIVO** — histórico de edições, montado automaticamente pelo build a partir de `portal/data/`.

## Fluxo diário

1. **Coletar candidatos** de todas as fontes:

   ```bash
   python3 scripts/fetch_sources.py feeds
   ```

2. **Curar** 12–18 notícias: resumos em pt-BR (2–3 frases cada), distribuídas entre as seções ARQ / ENG / TEC / BRA. Antes de curar, ler os data files de `portal/data/` dos últimos 7 dias e descartar qualquer URL já publicada (dedup).

3. **Buscar imagens** para o destaque e para matérias selecionadas:

   ```bash
   python3 scripts/fetch_sources.py image --url <url-da-matéria> [--hero]
   ```

   O comando retorna a imagem como data URI (base64) para embutir no data file. O Artifact tem CSP que bloqueia requisições a hosts externos — por isso as fotos precisam ser embutidas, nunca referenciadas por URL.

4. **Escrever** o radar (jogadas acionáveis para profissionais e escritórios AEC no Brasil), as sementes de conteúdo e as notas do editor.

5. **Gravar** o data file do dia em `portal/data/YYYY-MM-DD.json`, seguindo o schema abaixo.

6. **Regenerar o portal**:

   ```bash
   python3 scripts/build_portal.py
   ```

   Gera `portal/index.html` a partir de `portal/template.html` e dos data files.

7. **Republicar o Artifact na mesma URL**: usar a ferramenta Artifact com o parâmetro `url` apontando para a URL fixa do portal (https://claude.ai/code/artifact/a4dbeb62-d306-4a49-b262-343337bbf0b3). Nunca publicar sem `url` — isso criaria um Artifact novo em outra URL.

8. **Commitar** `portal/data/*.json` e `portal/index.html`.

## Schema do data file

Um arquivo por dia em `portal/data/YYYY-MM-DD.json`:

```json
{
  "meta": {
    "sheet": "A-01",
    "revision": "R00",
    "date": "DD.MM.AAAA",
    "date_long": "quarta-feira, 12 de agosto de 2026",
    "scale": "1:DIA",
    "sources_polled": 10,
    "sources_active": 9,
    "story_count": 15
  },
  "hero": {
    "marker": ["D", "01"],
    "kicker": "Destaque do dia",
    "title": "Título da matéria em destaque",
    "paragraphs": ["Parágrafo 1.", "Parágrafo 2."],
    "points": ["Ponto 1", "Ponto 2", "Ponto 3"],
    "source": "Nome da fonte",
    "date": "DD.MM",
    "url": "https://...",
    "image": "data:image/jpeg;base64,... (opcional)"
  },
  "sections": [
    {
      "id": "arq",
      "code": "ARQ",
      "name": "Arquitetura",
      "items": [
        {
          "title": "Título",
          "source": "Fonte",
          "date": "DD.MM",
          "url": "https://...",
          "summary": "Resumo em 2-3 frases, pt-BR.",
          "image": "data:image/jpeg;base64,... (opcional)"
        }
      ]
    }
  ],
  "editor_notes": [
    "<strong>Título da nota.</strong> Texto da nota do editor..."
  ],
  "radar": {
    "intro": "Parágrafo de abertura do radar.",
    "cards": [
      {
        "signal": "O sinal observado",
        "refs": ["fonte1", "fonte2"],
        "reading": "O que isso significa",
        "play": "A jogada recomendada",
        "horizon": "AGORA",
        "impact": 3,
        "effort": 2
      }
    ]
  },
  "studio": {
    "intro": "Parágrafo de abertura do estúdio.",
    "seeds": [
      {
        "platform": "LinkedIn",
        "format": "Post de opinião",
        "hook": "Primeira linha que segura o leitor",
        "draft": "Texto completo pronto para publicar, em pt-BR.",
        "hashtags": ["#AEC", "#BIM"]
      }
    ]
  },
  "revisions": [
    { "rev": "R00", "date": "DD.MM.AAAA", "desc": "Emissão da edição" }
  ]
}
```

Notas sobre o schema:

- `sections[].id` é um de `arq | eng | tec | bra`; `code` é o correspondente `ARQ | ENG | TEC | BRA`.
- `hero.paragraphs` tem 2 parágrafos; `hero.points` tem 3 pontos.
- `radar.cards[].horizon` é `AGORA | 6M | 24M`; `impact` e `effort` vão de 1 a 3.
- `studio.seeds[].platform` é `LinkedIn | Instagram | Substack`.
- O campo `archive` (histórico da prancha A-04) é injetado automaticamente pelo `build_portal.py` — não escrever à mão.

## Diretrizes editoriais

- **pt-BR primeiro.** Todos os resumos, notas, radar e sementes em português do Brasil, mesmo quando a matéria original é em inglês.
- **Resumos de 2–3 frases.** Densos e informativos: o que aconteceu, por que importa, com números e valores quando disponíveis.
- **Priorizar o Brasil.** Notícias do mercado nacional ganham peso na curadoria e no destaque; matérias internacionais entram quando há impacto ou lição para o contexto brasileiro.
- **Conectar notícias entre si.** As notas do editor e o radar devem apontar relações entre matérias do dia (e de dias anteriores), não repetir os resumos.
- **Radar acionável, nunca genérico.** Cada cartão do radar termina numa jogada concreta para profissionais, escritórios de arquitetura ou construtoras no Brasil — algo que dá para começar a fazer, não conselho vago de tendência.
- **Studio pronto para publicar.** As sementes de conteúdo são texto final, com voz direta e pessoal, sem clichê de IA ("no mundo acelerado de hoje", "revolucionário", "game changer" e afins estão proibidos). Quem copia deve poder colar e publicar.

## Casos de borda

- **Fonte fora do ar:** seguir com as demais fontes e registrar a diferença em `meta.sources_active` (menor que `sources_polled`).
- **Menos de 8 notícias nas últimas 24h:** ampliar a janela para 48h e avisar nas notas do editor que a edição cobre um período estendido.
- **Falha ao republicar o Artifact:** ainda assim commitar `portal/data/*.json` e `portal/index.html` — os dados do dia não podem se perder; a republicação pode ser refeita depois.

## Automação

A edição roda via Routine agendada do Claude Code: cron `0 11 * * *` UTC (8h de Brasília), disparando uma sessão nova a cada dia. A sessão executa o fluxo diário completo descrito acima, do fetch ao commit.

Enquanto o portal não estiver na branch `main`, a sessão da Routine deve trabalhar na branch `claude/onde-paramos-ld5c9n` (checkout dela antes de qualquer passo e commit nela ao final).
