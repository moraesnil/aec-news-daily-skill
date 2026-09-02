# Portal AGIO NEWS

Portal multiuso em HTML único, diagramado como **prancha técnica de arquitetura**
(tema claro = papel de desenho; tema escuro = cianotipia/blueprint), com 4 vistas
navegáveis — o "índice de pranchas":

| Prancha | Vista | Conteúdo |
|---|---|---|
| A-01 | Edição | Destaque do dia, notícias por categoria (com filtro por camada), notas do editor |
| A-02 | Radar | Cartões estratégicos: sinal → leitura → jogada, com horizonte (AGORA/6M/24M) e escalas de impacto/esforço |
| A-03 | Conteúdo | Sementes de conteúdo prontas para copiar (LinkedIn / Instagram / Substack) |
| A-04 | Arquivo | Histórico de edições |

Atalhos: teclas `1`–`4` trocam de prancha; a URL guarda a vista ativa via hash
(`#radar`, `#conteudo`…). O campo "Folha" do carimbo acompanha a prancha ativa.

## Arquitetura de build

```
portal/template.html   ← design fixo, placeholder __AEC_DATA__
portal/data/*.json     ← uma edição por dia (dados + fotos em base64)
scripts/build_portal.py → injeta a edição mais recente + índice do arquivo
portal/index.html      ← saída final, publicada como Artifact
```

A URL do portal é fixa: cada edição **republica o mesmo Artifact** (parâmetro
`url` da ferramenta Artifact). Nunca publicar sem esse parâmetro — criaria um
artifact novo e quebraria o link do leitor.

As fotos das matérias são embutidas como data URI (JPEG q62) porque o CSP dos
Artifacts bloqueia qualquer host externo.

## Fluxo diário completo

Documentado no `SKILL.md` da raiz. Automação: Routine diária às 8h (BRT) que
abre uma sessão nova, gera a edição, republica o Artifact e commita
`portal/data/AAAA-MM-DD.json` + `portal/index.html`.
