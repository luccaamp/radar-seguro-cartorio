# Repositório reproduzível — painel para qualquer pessoa, dados completos para a equipe

> **Para o Claude Code.** Objetivo final:
> - **Qualquer pessoa** clona `luccaamp/radar-seguro-cartorio` (que vai ficar **público**) e vê o painel **com os mesmos números** da carga oficial em poucos minutos, roda os testes e, se quiser, recalcula.
> - **Colegas da equipe** (colaboradores convidados) trabalham em **todas as etapas** e conseguem **qualquer camada de dados** (bronze, silver, gold completo com `interno_*`, banco) **da mesma carga** que eu, pelo repositório **privado** `luccaamp/radar-seguro-cartorio-dados`, que já existe (só com README).
>
> Tudo gratuito, sem serviço novo (sem GitHub Actions, sem deploy). **Você prepara e testa tudo localmente: nada de commit, push, criação de Release ou mudança de configuração no GitHub.** Quem publica sou eu.
>
> **Ambiente:** o `gh` (GitHub CLI) já está instalado e autenticado como `luccaamp`, com escopo `repo`. Você pode usá-lo **só para leitura** (ex.: `gh repo view`, `gh release list`), nunca para criar, apagar ou alterar nada.

---

## 0. Regras

- `CLAUDE.md` acima de tudo. Não apagar nada. Docs só com acréscimos; decisões novas a partir de **D-029**.
- **LGPD:** nada que vá para o repositório **público** (código, gold versionado, Release público) pode ter `interno_*`, nenhuma ESTIMATIVA do modelo no nível de serventia (passivo, déficit, probabilidade, IS, prêmio), nem nome, CPF ou e-mail de pessoa física. Dados de origem já publicados pelas fontes oficiais (CNJ, RAIS/PDET, Receita, IBGE, SUSEP) podem ir, desde que sem dado pessoal. *(Regra corrigida pelo autor em 2026-10-19; antes dizia "dado no nível de serventia", o que conflitava com o silver no Release público. Ver D-030.)* O pacote **da equipe** pode ter tudo, mas só vai para o repositório **privado**.
- **Números de referência** (não podem mudar): 2.525 · 12.134 · ≈ 1.121 · R$ 311,9 mi · R$ 238,1 mi · ≈ 486 · R$ 36,9 mi · R$ 18,4 mi · R$ 368,7 mil · teto R$ 4,76 mi.
- Testes na cópia do banco; banco real e Parquet intactos antes e depois da suíte.
- **Pergunte-me antes de:** escolher a licença (sugira; eu decido), versionar mais de 20 MB de dados no repositório público, ou mudar a estrutura de pastas.
- Pastas temporárias de teste: **fora do OneDrive**. Apague-as no fim.

---

## 1. Diagnóstico (primeiro)

### 1.1 Auditoria do repositório antes de ficar público
Quando o repositório virar público, **todo o histórico** do git fica visível, não só a versão atual. Verifique **todos os commits**, e só diagnostique (não reescreva histórico sem me perguntar):
- segredos: tokens, senhas, chaves de API, `.env` real;
- arquivos de dados commitados por engano (bronze, silver, gold com `interno_*`, `.duckdb`, CSV do BI, RAIS);
- arquivos grandes (> 5 MB);
- dado pessoal: nomes, CPF, e-mails de titulares, inclusive em testes ou docs;
- transcrições de conversa (`conversas/`), caminhos pessoais e qualquer coisa que eu não gostaria de expor.

Para cada achado: commit, arquivo e gravidade, e a recomendação: (a) não é problema; (b) remover só da versão atual; (c) **exige reescrever o histórico** (explique como, com qual ferramenta gratuita e os riscos; **não faça**).

### 1.2 Clone limpo
1. Clone o repositório numa pasta temporária fora do OneDrive.
2. Tente, como um estranho: `uv sync`; `uv run pytest`; `uv run streamlit run app/Inicio.py` (só verificar se sobe e se a página carrega; depois derrubar); `uv run pipeline.py --help` (**não** rodar a coleta).
3. Anote cada erro.
4. Liste o que está e o que não está no git, com os tamanhos: bronze por fonte, silver, gold público, gold `interno_*`, banco, CSV do BI, prints de QA.

O diagnóstico vai no relatório final; não precisa parar aqui, **exceto** se a auditoria 1.1 achar algo de gravidade (c). Nesse caso, pare e me mostre antes de seguir.

---

## 2. O que implementar

### 2.1 Gold público versionado (D-029)
- Quem clonar já tem os dados de que o painel precisa, sem rodar nada.
- **Duas formas aceitas; escolha a mais simples e justifique:**
  - **(a)** versionar a própria `data/gold/`, com o `.gitignore` excluindo `interno_*` e o `.duckdb`;
  - **(b)** uma pasta `data/publico/`, atualizada de propósito por script (evita mudanças nos binários a cada carga).
- Conteúdo: só as tabelas **públicas** que o painel lê (Parquet), a geometria pública do mapa e um `manifesto.json` (data de referência de cada fonte, data e hora da carga, versão das premissas, commit, e o SHA-256 e o tamanho de cada arquivo).
- Script `scripts/gerar_publico.py`: gera esse conjunto a partir do gold, roda o **auditor de ataque por diferença** e os contratos de "sem dado pessoal" sobre ele, e falha se houver `interno_*`, coluna de CNS, nome de pessoa ou área abaixo do limiar fora das exceções aprovadas.
- Meta: menos de 20 MB.
- **Teste de coerência:** se o gold local existir, o conjunto público tem de bater com ele (por hash). Se não bater, o teste avisa "dados públicos desatualizados: rode `scripts/gerar_publico.py`".

### 2.2 Modo demonstração
- Sem banco local, o painel monta um DuckDB temporário a partir do gold público e mostra uma faixa discreta: "Modo demonstração: dados da carga de DD/MM/AAAA. Para recalcular, veja 'Como rodar' no README."
- Funções que gravam (ex.: "Salvar cenário") ficam desativadas, com explicação curta.
- O rodapé mostra a carga em uso (ver 2.5.5).

### 2.3 Simulador sem dados internos
**[VERIFICAR]** Quais controles do Simulador precisam de `interno_*`, silver ou RAIS para recalcular?
- **Controles de seguro e déficit** (prob. de déficit e parte descoberta por classe, escolha de garantia, taxa, share, sinistralidade, despesas, cenário do STF): recalcular a partir de uma tabela pública pequena com os **totais por classe** (`gold.simulador_base_classe`). **Teste:** resultado idêntico ao motor completo nas premissas padrão e em 5 combinações aleatórias.
- **Controles do passivo e do rateio** (FAP, INSS no aviso, base de remuneração, vínculos mínimos, regra v1 × v2, método de rateio): uma **grade pequena de variantes pré-calculadas**, só com totais (`gold.simulador_variantes`). No modo demonstração, o controle oferece só os valores da grade.
- O que não couber em nenhuma das duas: desativado no modo demonstração, com "disponível com os dados completos".
- **No modo completo (o meu e o da equipe), o Simulador continua exatamente como hoje.**

### 2.4 Testes e pipeline num clone limpo
- `uv run pytest` passa **sem o banco real e sem bronze**: usa o gold público, ou dados pequenos de teste em `tests/dados/` (sem dado pessoal). O que exigir dados reais fica marcado `@pytest.mark.dados_reais`, fora da suíte padrão, com o motivo.
- **Pipeline sem o CSV do BI:** as conferências com o BI viram aviso "arquivo ausente"; os totais de controle em `config/qualidade.yaml` continuam valendo.
- **Pipeline a partir de qualquer camada:** `uv run pipeline.py --a-partir-de bronze|silver|gold` (ou equivalente). Recalcula as camadas seguintes **sem coletar de novo**.

### 2.5 Dados da equipe e dados públicos em Releases (D-030)

**Desenho** (decidido; não mude):

| Onde | Quem acessa | Release | Conteúdo |
|---|---|---|---|
| `luccaamp/radar-seguro-cartorio` (público) | qualquer pessoa, sem login | `dados-AAAA-MM-DD` | **silver** + `manifesto.json` (o gold público já está no próprio repositório) |
| `luccaamp/radar-seguro-cartorio-dados` (privado) | só colaboradores convidados | `carga-AAAA-MM-DD` | **pacote completo:** bronze (todas as fontes, em partes < 2 GiB), silver, gold completo **com `interno_*`**, banco `.duckdb` + `manifesto.json` |

Limites do GitHub: cada arquivo do Release abaixo de 2 GiB; sem limite total nem de banda.

**[VERIFICAR] antes de empacotar o público:** para cada tabela do silver, liste os campos e confirme que não há dado pessoal. O pacote público só sai se os contratos de "sem dado pessoal" passarem.

**Implementar:**
1. **`scripts/empacotar_dados.py --carga AAAA-MM-DD --nivel publico|equipe`**: gera em `pacotes/<nivel>/` (no `.gitignore`):
   - **publico:** silver (zip; partes < 2 GiB se preciso) + manifesto;
   - **equipe:** bronze por fonte, silver, gold completo e banco, cada um comprimido (arquivos já comprimidos, como o 7z da RAIS, vão como estão), em partes < 2 GiB, + manifesto com hash e tamanho de cada arquivo original e de cada parte, data da carga, datas de referência, versão das premissas e commit.
   - Informe os tamanhos de cada camada e o total de cada pacote.
2. **`scripts/baixar_dados.py --carga AAAA-MM-DD --camadas bronze,silver,gold,banco --nivel publico|equipe`**:
   - o usuário escolhe as camadas;
   - **publico:** baixa por URL pública, sem login;
   - **equipe:** usa o `gh` autenticado para baixar do repositório privado (`gh release download`); se o `gh` não estiver logado ou a pessoa não tiver acesso, mensagem clara de como pedir acesso;
   - junta as partes, **confere todos os hashes**, extrai para `data/<camada>/` e falha se algo não bater;
   - `--origem <pasta>` instala de uma pasta local (plano B: OneDrive ou pendrive);
   - nunca sobrescreve dados locais sem `--substituir`.
3. **Carga em uso:** `data/carga_atual.json` com a carga instalada e o nível. O rodapé do painel mostra, ex.: "Carga 2026-10-18 · dados completos" ou "· demonstração".
4. **Passo a passo para mim** (em `docs/publicacao.md`), com os comandos exatos:
   - gerar os dois pacotes;
   - publicar os dois Releases com `gh release create … --repo …` (e pelo site, para arquivos pequenos);
   - tornar o repositório principal **público** (onde clicar);
   - **proteger a `main`** no repositório público (exigir pull request; como eu, sendo o único revisor, consigo fazer merge dos meus próprios PRs: 0 aprovações obrigatórias ou permitir que o administrador passe por cima; e bloquear push direto e force-push);
   - convidar colaboradores nos dois repositórios;
   - checklist de "nova carga" (o que rodar, em que ordem, o que conferir antes de publicar);
   - manter as últimas 3 cargas.

### 2.6 Documentação
**README** ("Como rodar"), com comandos para Windows (PowerShell) e Linux/macOS:
1. **Ver o painel (≈ 2 min):** instalar o `uv` → `uv sync` → `uv run streamlit run app/Inicio.py` (modo demonstração).
2. **Recalcular com os dados públicos:** `baixar_dados.py --nivel publico --camadas silver` → `pipeline.py --a-partir-de silver`.
3. **Reproduzir do zero:** coleta completa (tempo e espaço estimados), com o aviso de que **as fontes se atualizam e os números podem diferir**. Usar os hashes do manifesto para comparar. Passo opcional do CSV do BI.
4. **Equipe:** apontar para o `CONTRIBUTING.md`.

Também no README: tabela de fontes (link oficial, data de referência, termo de uso), requisitos e licença.

**`CONTRIBUTING.md`:**
- como pedir acesso (eu convido nos dois repositórios; instalar o `gh` e fazer `gh auth login`);
- como baixar os dados da equipe e qual camada usar em cada tarefa (coletor → bronze; limpeza → silver; modelo → silver; painel e chat → gold);
- fluxo: **branch por tarefa → pull request → revisão por mim**; a `main` é protegida;
- antes do PR: `uv run pytest` passando; se mexeu no painel, `scripts/prints_painel.py` com os prints anexados; se mudou número, explicar a cascata e regerar o gold público;
- regras do projeto em resumo (fonte e data em todo número; decisões em `decisoes.md`; erros em `erros_ia.md`; dados nunca no git, exceto o gold público);
- **só eu publico Releases**; ninguém apaga ou substitui Release;
- **LGPD da equipe:** o pacote da equipe e as `interno_*` são de uso interno; não publicar, não colar em issues, PRs ou prints, e não enviar a serviços externos (inclusive IAs online).

**LICENSE:** sugira uma (ex.: MIT) e me pergunte antes de criar.

### 2.7 Prova final
Numa pasta temporária fora do OneDrive, simule um clone com os arquivos que **seriam** versionados (respeitando o `.gitignore`) e rode, **exatamente como escrito no README e no CONTRIBUTING**:
1. ver o painel (modo demonstração) e cronometrar;
2. `uv run pytest`;
3. `baixar_dados.py --origem pacotes/publico` → `pipeline.py --a-partir-de silver` → comparar o hash do gold público com o meu (**idêntico**);
4. `baixar_dados.py --origem pacotes/equipe --camadas bronze` → `pipeline.py --a-partir-de bronze` → hash idêntico.

Apague a pasta temporária no fim.

---

## 3. Fora do escopo
- Commit, push, Releases e configurações no GitHub (faço eu, com o passo a passo).
- Deploy online e GitHub Actions.
- Bloco 2.

---

## 4. Ordem
1. Diagnóstico: auditoria do histórico (1.1, parando se houver gravidade c) e clone limpo (1.2).
2. Gold público + script + auditor (2.1).
3. Modo demonstração (2.2) e Simulador (2.3).
4. Testes e pipeline (2.4).
5. Pacotes e scripts de dados (2.5).
6. Documentação (2.6), parando para me perguntar sobre a licença.
7. Prova final (2.7).

---

## 5. Relatório ao fim (e PARE)
1. Auditoria do histórico: achados e recomendações.
2. Clone limpo **antes**: o que quebrava.
3. O que foi feito em 2.1 a 2.6, com os arquivos A/M.
4. Tamanhos: gold público versionado, pacote público, pacote da equipe (por camada).
5. Prova final: os 4 caminhos, com o tempo de cada um, e os hashes idênticos.
6. Testes: suíte padrão no clone simulado e no meu ambiente; banco real e Parquet intactos; números de referência iguais.
7. O que eu faço agora: resumo do `docs/publicacao.md`.
8. Sugestão de mensagem de commit.

**Pare. Não comece o Bloco 2. Nada de commit, push ou Release.**
