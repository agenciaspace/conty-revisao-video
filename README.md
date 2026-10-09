# Revisão de vídeo e peças da campanha

Cada campanha declara `required_pieces`: subconjunto não vazio de `script`,
`video`, `cover`, `caption`. A entrega mantém versões independentes por peça.
Apenas a versão **atual** aprovada satisfaz um requisito. Peças opcionais não
bloqueiam; campanha só de vídeo não exige roteiro.

Estados: `in_production` enquanto faltam peças; `ready_for_approval` quando
todas estão aprovadas; `approved` após aprovação explícita da entrega. Nova
versão de peça obrigatória revoga a aprovação; aprovar a nova versão restaura
quando todos os requisitos voltam a valer. Histórico de versões/aprovações
permanece intacto. `previous_version` impede sobrescrita por cliente desatualizado.
Aprovação de versão antiga retorna 409.

Comentários de vídeo apontam para **versão + segundo** e ficam entre zero e a
duração informada. Não migram para outra versão. URLs não são baixadas e o vídeo
não é decodificado: upload e duração são simulados. `actor` simula a identidade
na fronteira de negócio; um sistema real deve obter esse papel da sessão.

## Exemplo

```bash
curl -s "$BASE/campaigns" -H 'Content-Type: application/json' -d '{"id":"c1","actor":"brand","required_pieces":["video"]}'
curl -s "$BASE/deliveries" -H 'Content-Type: application/json' -d '{"id":"d1","campaign_id":"c1","actor":"creator"}'
curl -s "$BASE/deliveries/d1/pieces/video/versions" -H 'Content-Type: application/json' -d '{"actor":"creator","previous_version":0,"url":"https://example.org/video.mp4","duration_seconds":60}'
curl -s "$BASE/deliveries/d1/pieces/video/versions/1/comments" -H 'Content-Type: application/json' -d '{"actor":"brand","second":12.5,"text":"Encurtar esta pausa"}'
curl -s "$BASE/deliveries/d1/pieces/video/versions/1/approve" -H 'Content-Type: application/json' -d '{"actor":"brand"}'
curl -s "$BASE/deliveries/d1/approve" -H 'Content-Type: application/json' -d '{"actor":"brand"}'
curl -s "$BASE/deliveries/d1"
```

A entrega retorna `state: "approved"`, `pending_pieces: []` e o comentário na
versão 1 em `second: 12.5`. Enviar versão 2 (`previous_version: 1`) muda para
`in_production`, mantém o comentário na versão 1 e deixa os comentários da
versão 2 vazios. Aprovar com pendência retorna 409 e nomes das peças pendentes.
Peça opcional nova não revoga o que a campanha exigiu.

Com mais tempo: autenticação/participantes, upload assinado, duração extraída do
vídeo, política de moderação e confirmação concorrente em tabelas normalizadas.

## Rodar e verificar

Python 3.12 com base de fusos IANA (incluída no Ubuntu); sem `pip install`.

```bash
python3 -m unittest -v
python3 app.py
```

API na porta 8080. `PORT`, `HOST` (padrão 127.0.0.1), `DATABASE_PATH` (padrão
`data.sqlite3`) e `API_TOKEN` configuram o processo. Com `API_TOKEN`, envie
`Authorization: Bearer ...`; `/health` fica público. Os exemplos abaixo usam
`BASE` como a URL do processo ou de um proxy HTTPS. `test_http.py` executa o
fluxo pela rede HTTP real, além dos testes de domínio com relógio controlado.

Respostas são JSON; sucesso 200, entrada inválida 422, conflito 409, ausente
404. JSON malformado retorna 400. SQLite persiste estado em transações
`BEGIN IMMEDIATE`; uma operação inválida faz rollback, inclusive de alterações
parciais. Reiniciar preserva dados. Cada execução de testes usa banco isolado.

## Limites desta entrega

O adaptador HTTP é uma demonstração síncrona, não um servidor de produção.
SQLite guarda um documento de estado por aplicação: simples para verificar as
invariantes e a persistência, mas inadequado para grande volume. Com mais tempo,
normalizaria tabelas e índices, adicionaria autenticação por usuário/tenant,
limites operacionais, observabilidade e migrações. O token compartilhado não
substitui autorização por recurso. Não exponha dados reais neste demo.

## Uso de IA

Codex implementou, testou e fez revisão automatizada das regras, exemplos e
resultados a pedido de Leon Hatori. Não declaramos revisão humana que ainda
não ocorreu. Detalhes em [AI_USAGE.md](AI_USAGE.md).
