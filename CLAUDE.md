# Projeto: Controle de Validade de Produtos (Expiry Tracker)

## Contexto
- Autor: Cleiton Bitencourt, Analista de Software em rede de supermercados (suporte ERP, PDV, Oracle).
- Objetivo: um sistema SIMPLES, BEM FEITO e funcionando, para publicar no GitHub e no LinkedIn.
- Problema real que resolve: supermercados perdem dinheiro com produtos vencidos. O sistema avisa o que está perto de vencer para agir antes (promoção, troca com fornecedor, remanejamento).

## Modo de trabalho: construção assistida
- Você (Claude) pode escrever o código, MAS em passos pequenos.
- A cada passo: explique em português simples o que fez e por quê, e mostre como testar.
- Depois de cada passo que funcionar, peça ao Cleiton para fazer o commit ele mesmo, com mensagem em inglês (corrija o inglês dele se precisar).
- No final, faça 5 perguntas para verificar se ele entendeu o sistema (ele precisa conseguir explicar em entrevista).
- Respostas curtas. Analogias só em partes complexas.
- Não invente bibliotecas, funções ou regras fiscais. Na dúvida, diga que não sabe e cite a documentação oficial.

## Tecnologias (versão 1, para terminar hoje)
- Python
- SQLite (banco em arquivo, sem instalação)
- Streamlit (tela web simples)
- Versão 2 (futura, como aprendizado): migrar o banco para Oracle.

## Funcionalidades da versão 1 (escopo fechado)
1. **Produtos:** cadastro com código de barras (EAN/GTIN), descrição, categoria e preço de custo.
2. **Entrada de lotes (via nota fiscal):** chave de acesso da NF-e (44 dígitos), fornecedor, data de entrada, código de barras, quantidade, lote e data de validade.
   - Validar se a chave tem 44 dígitos numéricos.
   - Buscar o produto pelo código de barras; se não existir, pedir cadastro.
3. **Painel de alertas:** lotes vencidos, vencendo em até 7, 15 e 30 dias, com cores diferentes.
4. **Ação sobre o lote:** marcar como vendido, rebaixado (promoção), devolvido ao fornecedor ou descartado.
5. **Relatório de perdas:** valor total descartado por período e por categoria.

Fora do escopo da versão 1 (deixar listado no README como "Next steps"):
- Importar o XML da NF-e automaticamente.
- Leitura de código de barras pela câmera.
- Migração para Oracle.
- Login de usuários.

## Dados
- Usar SOMENTE dados fictícios (produtos, fornecedores e notas inventados).
- Nunca usar dados reais da empresa onde o Cleiton trabalha (notas, CNPJs, preços).
- Criar um script de dados de exemplo para a demonstração.

## Padrões profissionais
- Código, comentários, README e commits em INGLÊS.
- Estrutura:
  ```
  app.py            -> telas Streamlit
  database.py       -> criação e acesso ao banco
  seed_data.py      -> dados de exemplo
  requirements.txt
  README.md
  ```
- README com: problema, solução, funcionalidades, como rodar, prints das telas, próximos passos e a frase "Built with AI-assisted development (Claude Code)".
- Nada de senhas no código.

## Ordem de execução
1. Verificar se Python e Git estão instalados.
2. Criar a estrutura e o banco.
3. Cadastro de produtos.
4. Entrada de lotes.
5. Painel de alertas.
6. Ações e relatório de perdas.
7. Dados de exemplo, README e prints.
8. Subir no GitHub.
