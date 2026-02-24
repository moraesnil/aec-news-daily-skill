# AEC News Daily Skill

> Boletim diario de noticias AEC (Arquitetura, Engenharia e Construcao) gerado por IA, coletado de fontes nacionais e internacionais e salvo automaticamente no Notion.
>
> ## O Problema
>
> O setor AEC brasileiro e global produz dezenas de noticias relevantes por dia — projetos, normas, tecnologias, mercado, BIM, sustentabilidade. Acompanhar tudo isso exige horas de leitura dispersa em varios sites.
>
> ## A Solucao
>
> Esta skill coleta automaticamente as principais fontes AEC nacionais e internacionais — tanto via RSS quanto via web scraping com Apify — gera um boletim estruturado e salva tudo no seu Notion com um unico comando.
>
> ## Fontes Cobertas
>
> ### Com RSS (fetch direto)
>
> **Internacional — Arquitetura:**
> - ArchDaily Brasil → feeds.feedburner.com/ArchdailyBR
> - - Dezeen → dezeen.com/feed
>   - - Archinect → archinect.com/feed/news
>     - - The Architect's Newspaper → archpaper.com/feed
>       - - buildingSMART International → buildingsmart.org/feed
>        
>         - **Internacional — Engenharia & Construcao:**
>         - - ENR (Engineering News-Record) → enr.com/rss/1
>           - - Construction Dive → constructiondive.com/feeds/news/
>             - - Global Construction Review → globalconstructionreview.com/feed/
>              
>               - **Nacional — Brasil:**
>               - - Revista PROJETO → revistaprojeto.com.br/feed/
>                
>                 - ### Sem RSS (scraping via Apify MCP)
>                
>                 - **Internacional:** Arch Record, BD+C, Autodesk AEC Blog, BIM Community
>                
>                 - **Nacional — Brasil:** AECweb, Construcao Mercado (Pini), CBIC, CAUBR
>
> ## Exemplo de Saida no Notion
>
> **Database: AEC News Feed**
> Cada noticia e salva como uma pagina com: Titulo, URL, Fonte, Categoria, Idioma, Data, Resumo em pt-BR.
>
> **Pagina diaria: "AEC Briefing - YYYY-MM-DD"**
> Boletim completo estruturado por categorias com destaques, resumos e observacoes do editor.
>
> ## Como Usar
>
> ### Instalacao
>
> ```bash
> npx skills i moraesnil/aec-news-daily-skill
> ```
>
> ### Executar manualmente
>
> Cole no seu chat (Claude Code, Cursor, etc.):
>
> ```
> Run the aec-news-daily-skill: Fetch all AEC news sources (RSS feeds and scrape non-RSS sites via Apify MCP), select the top stories from the past 24 hours, generate a structured daily briefing in Portuguese, and save all results to the Notion AEC News Feed database. Create a Daily Overview page with today's full briefing.
> ```
>
> ### Configurar como task (OpenClaw)
>
> ```json
> {
>   "name": "aec-daily-briefing",
>   "schedule": {
>     "kind": "cron",
>     "expr": "0 8 * * *",
>     "tz": "America/Sao_Paulo"
>   },
>   "sessionTarget": "isolated",
>   "payload": {
>     "kind": "agentTurn",
>     "message": "Run the aec-news-daily-skill: Fetch all AEC news sources (RSS feeds and scrape non-RSS sites via Apify MCP), select top stories from past 24 hours, generate structured daily briefing in Portuguese (pt-BR), save all results to Notion AEC News Feed database, and create a Daily Overview page titled 'AEC Briefing - {today}' with the full briefing content.",
>     "timeoutSeconds": 300
>   },
>   "delivery": {
>     "mode": "announce"
>   }
> }
> ```
>
> ## Arquitetura
>
> ```
> User Request / Task Trigger
>         |
>         v
> Fetch RSS Feeds (9 sources)
>         |
>         v
> Scrape non-RSS via Apify MCP (8 sources)
>         |
>         v
> Filter by Time Window (24h / 48h fallback)
>         |
>         v
> Select Top Stories (1-2 per source, 10-20 total)
>         |
>         v
> Generate Structured Briefing (pt-BR)
>         |
>         v
> Save to Notion
>   |              |
>   v              v
> AEC News     Daily Overview
> Feed DB        Page
> (individual    (full briefing
>  articles)      by date)
> ```
>
> ## Requisitos
>
> - Assistente de IA com suporte a skills (Claude Code, Cursor, etc.)
> - - Acesso a internet para fetch dos RSS feeds
>   - - MCP Apify configurado (para fontes sem RSS)
>     - - MCP Notion configurado com acesso ao seu workspace
>       - - Nao sao necessarias chaves de API para as fontes RSS
>        
>         - ## Links Relacionados
>        
>         - - [YouMind-OpenLab](https://github.com/YouMind-OpenLab) — Ferramentas e skills de IA open source
>           - - [karpathy-rss-daily-skill](https://github.com/YouMind-OpenLab/karpathy-rss-daily-skill) — Skill similar para noticias de IA
>             - - [Skills CLI](https://www.npmjs.com/package/skills) — Instalador universal de skills de IA
>              
>               - ## Licenca
>              
>               - MIT
