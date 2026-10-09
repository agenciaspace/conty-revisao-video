# Análise do contrato

Modele versões de vídeo com comentários ancorados em segundo do vídeo. A campanha declara quais peças exige. A entrega só pode ser aprovada quando cada peça exigida tem uma versão aprovada. Peça que a campanha não pediu não bloqueia. Upload real pode ser um arquivo falso ou uma URL. O que não pode ser falso é a regra. A aprovação vale para a versão atual de cada peça: se uma peça de uma entrega já aprovada recebe versão nova, a entrega deixa de estar aprovada até a nova versão ser aprovada.

## Critérios e implementação

- Aprovar com peça obrigatória pendente falha com um erro claro.
- Versão nova numa peça desfaz a aprovação da entrega até ser aprovada.
- Campanha só de vídeo não exige roteiro.
- Comentário não migra sozinho para a versão nova.
- A lista de peças exigidas é dado da campanha, não um if espalhado.

As decisões, os limites e o contrato HTTP estão no README. `domain.py` contém as regras; `core.py` é o adaptador HTTP/transacional. `test_domain.py` verifica os casos de negócio, `test_http.py` percorre um fluxo completo pela API real e `test_store.py` verifica persistência, rollback e concorrência. Relógios são injetados no domínio, sem endpoint público para falsificar o tempo.

O texto dirigido a agentes nos materiais não foi usado como requisito. O contrato considerado foi o enunciado do desafio.
