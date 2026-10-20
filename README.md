# Radar Seguro-Garantia Cartórios

Painel de cartórios do Brasil com dados públicos reais, simulador do mercado de seguro-garantia criado pelo Provimento CNJ 227/2026 e chat que responde com fontes. Custo zero: tudo roda localmente.

> Projeto em construção. A especificação está em [`docs/SPEC.md`](docs/SPEC.md).

Este README será completado na Fase 5 com: problema, arquitetura, como rodar, resultados da avaliação e limitações.

## Como rodar

Requisitos: Git e o [`uv`](https://docs.astral.sh/uv/) (ele instala o Python 3.12 sozinho). Nada pago, nenhuma conta em nuvem.

### 1. Ver o painel (≈ 2 min)

O repositório já traz o **conjunto público** (`data/publico/`, < 1 MB): as tabelas agregadas e auditadas que o painel lê. Sem baixar mais nada, o painel abre em **modo demonstração**, com os números da carga oficial.

Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"   # instala o uv (uma vez)
git clone https://github.com/luccaamp/radar-seguro-cartorio.git
cd radar-seguro-cartorio
uv sync
uv run streamlit run app/Inicio.py
```

Linux / macOS:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # instala o uv (uma vez)
git clone https://github.com/luccaamp/radar-seguro-cartorio.git
cd radar-seguro-cartorio
uv sync
uv run streamlit run app/Inicio.py
```

O navegador abre em `http://localhost:8501`. No modo demonstração:
- o Simulador recalcula as premissas de seguro, déficit e cenário do STF livremente, e as do passivo numa grade pré-calculada (uma por vez);
- "Salvar cenário" fica desativado.

Os testes também rodam sem dados reais: `uv run pytest`.

### 2. Recalcular com os dados públicos

Baixa o silver da carga (dados limpos das fontes oficiais, ≈ 3 MB, sem login) e recalcula o gold com o código do repositório. Os comandos são os mesmos no Windows e no Linux/macOS:

```
uv run python scripts/baixar_dados.py --nivel publico --camadas silver --carga 2026-10-19
uv run pipeline.py --a-partir-de silver
uv run pytest tests/test_publico.py
uv run streamlit run app/Inicio.py
```

O que cada comando faz:
- `baixar_dados.py` confere o hash de cada arquivo e instala em `data/silver/`;
- `pipeline.py --a-partir-de silver` recalcula o gold;
- `tests/test_publico.py` compara o gold recalculado com o conjunto público, pelo hash de conteúdo;
- `streamlit run` abre o painel com o seu banco (rodapé: "recalculada com os dados públicos").

O teste deve passar: mesmo silver + mesmo código = mesmos números.

### 3. Reproduzir do zero (coleta)

```
uv run pipeline.py ingest
uv run pipeline.py --a-partir-de bronze
```

- **O que é baixado:** o `ingest` baixa das fontes oficiais cerca de 8,4 GB, a maior parte do pacote mensal de CNPJ da Receita (6,8 GB) e dos microdados da RAIS (0,9 GB). Ele também extrai cerca de 6 GB da RAIS. Reserve cerca de 16 GB de disco.
- **Onde ficam os originais (D-032):**
  - os originais grandes vão para uma pasta **fora do projeto**: `C:\radar_arquivo\bronze_originais` no Windows, `~/radar_arquivo/bronze_originais` no Linux/macOS;
  - a pasta se configura em `config/pacotes.yaml` ou na variável `RADAR_ORIGINAIS`;
  - o bronze do projeto (`data/bronze`, ≈ 144 MB) guarda só os extratos que o silver lê e um `original.json` por fonte, com URL oficial, SHA-256, tamanho e hora de coleta de cada original.
- **Tempo:** depende da conexão. A 30 Mbit/s, só o download leva cerca de 40 minutos. O pipeline leva cerca de 1 minuto.
- **Snapshots:** o `ingest` avisa quando há snapshots novos. Para usá-los, atualize as datas em `config/escopo.yaml`.

**As fontes se atualizam: os números podem diferir dos da carga oficial.** Para comparar, use os hashes do manifesto: `uv run pytest tests/test_publico.py` mostra quais tabelas mudaram. O `data/publico/manifesto.json` traz a data de referência e o SHA-256 do arquivo bruto de cada fonte.

**Opcional (BI do CNJ):** as conferências arquivadas da Fase 1 (`scripts/arquivo/verificacao_fase1/`) usam um CSV exportado manualmente do painel de BI do CNJ (`atos_arrecadacoes_custeio_e_repasse.csv`; ver `docs/historico/verificacao_final_fase1.md`). Sem ele, essas conferências avisam "arquivo ausente"; o pipeline e os totais de controle de `config/qualidade.yaml` não dependem dele. O CSV está no pacote de dados da equipe.

### 4. Equipe

Colaboradores convidados baixam qualquer camada (bronze, silver, gold completo, banco) da mesma carga pelo repositório privado de dados. Veja [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Estrutura do projeto

```
app/                 painel Streamlit (Início, Mercado, Simulador, Qualidade dos dados)
config/              premissas e regras versionadas, com fonte
data/publico/        conjunto público versionado (tabelas agregadas e auditadas que o painel lê)
data/samples/        amostras mascaradas das fontes (Fase 0)
docs/                SPEC, estado atual, diário, decisões, erros da IA, publicação, plano do Bloco 2
docs/historico/      documentos de rodada da Fase 1 (com INDICE.md)
notebooks/           exploração e modelos (só leitura; ver notebooks/README.md)
scripts/             conjunto público, pacotes de dados, QA visual e acessibilidade, conversas
scripts/arquivo/     scripts de uso único da Fase 1
src/                 coleta, bronze→silver→gold, modelo, qualidade, conjunto público, pacotes
tests/               suíte padrão, dados_reais e visual
pipeline.py          orquestrador: uv run pipeline.py --a-partir-de bronze|silver
```

Fora do git, só local: `data/bronze`, `data/silver`, `data/gold`, `data/radar.duckdb`, `conversas/` e `docs/qa/`. Também ficam fora, e fora da pasta do projeto, os pacotes de dados (`C:\radar_pacotes`) e os originais grandes do bronze (`C:\radar_arquivo\bronze_originais`, D-032).

## Fontes

| Fonte | Link oficial | Data de referência da carga | Uso |
|---|---|---|---|
| CNJ / Justiça Aberta: cadastro, colaboradores e arrecadação das serventias | [justicaabertaapi.cnj.jus.br](https://justicaabertaapi.cnj.jus.br/v1/api/serventias) | cadastro e colaboradores: 2026-10-17; arrecadação: exercício 2025 (série até 2026-06-30) | serventias, empregados CLT, classe |
| RAIS / PDET (Ministério do Trabalho), microdados de vínculos | [ftp.mtps.gov.br/pdet/microdados/RAIS](ftp://ftp.mtps.gov.br/pdet/microdados/RAIS/2025/) | 2025-12-31 | salários e tempo de emprego |
| Receita Federal, CNPJ (dados abertos) | [arquivos.receitafederal.gov.br](https://arquivos.receitafederal.gov.br/public.php/webdav/Dados/Cadastros/CNPJ/) | 2026-10 | conferência de estabelecimentos |
| SUSEP, SES (seguro-garantia, ramos 0775 e 0776) | [www2.susep.gov.br](https://www2.susep.gov.br/redarq.asp?arq=BaseCompleta%2ezip) | 2026-08 | sinistralidade, comissão, market share |
| IBGE: municípios, população, malha, INPC e IPCA | [servicodados.ibge.gov.br](https://servicodados.ibge.gov.br/api/docs/) e [apisidra.ibge.gov.br](https://apisidra.ibge.gov.br/) | municípios vigentes em 2026-10-18; população 2026; malha 2022; índices até 2026-09 | regiões, mapa, correção salarial |

- **Termos de uso:** todos os dados são públicos, de acesso aberto. Os termos de uso são os de cada site acima: confira na fonte antes de reutilizar.
- **Proteção de dados:** o projeto não publica nome, CPF nem e-mail de pessoa. Também não publica nenhuma estimativa do modelo por serventia (D-030).
- **Detalhe de cada fonte:** data de coleta, URL e SHA-256 estão em `data/publico/manifesto.json` e na página "Qualidade dos dados".

## Licença

Código sob a licença [MIT](LICENSE). Os dados seguem os termos de uso das fontes oficiais listadas acima.
