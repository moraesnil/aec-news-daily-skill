# Portal AEC NEWS

Portal diário em HTML único (`index.html`), diagramado como **prancha técnica de arquitetura**:

- **Tema claro** = papel de desenho técnico (nanquim sobre papel)
- **Tema escuro** = cianotipia / blueprint (linhas claras sobre azul da Prússia)
- Divisores de seção como linhas de cota, marcadores de detalhe por notícia (`ARQ/01`),
  legenda de camadas que funciona como filtro de categorias, e rodapé em formato de
  **carimbo** com tabela de revisões — cada edição diária vira uma linha `R01`, `R02`…

## Como o portal é atualizado

O design é fixo; os dados vivem num único bloco JSON embutido:

```html
<script type="application/json" id="aec-data"> { ... } </script>
```

Fluxo diário (executado pela skill / task agendada):

1. Coletar as fontes (RSS + Google News RSS para sites sem feed)
2. Curar as notícias e escrever resumos em pt-BR
3. Substituir **apenas** o JSON do `#aec-data`:
   - `meta` — data, revisão (`R01`, `R02`…), contagens de fontes/notícias
   - `hero` — destaque do dia
   - `sections[].items` — notícias por categoria (arq / eng / tec / bra)
   - `editor_notes` — notas de projeto (tendências, conexões)
   - `revisions` — **acrescentar** a linha da nova revisão (manter o histórico)
4. Republicar o arquivo como Artifact **na mesma URL** (mesmo `file_path` na mesma
   sessão, ou passando a URL do artifact como `url` em outra sessão)

O leitor guarda um único link; a página é sempre a edição mais recente, e o
histórico de edições fica visível na tabela de revisões do carimbo.

## Estrutura do JSON

Ver o próprio `index.html` — o bloco `#aec-data` da edição `R00` serve de exemplo
completo do schema.
