# Publicação: Releases de dados, repositório público e equipe

Passo a passo para o autor. Os scripts só geram arquivos locais. **Commit, push, Releases e configurações do GitHub são feitos por você**, com os comandos abaixo. Comandos em PowerShell; no Linux/macOS, troque `C:\radar_pacotes` por `~/radar_pacotes` (padrões em `config/pacotes.yaml`).

Carga de referência neste documento: `2026-10-19`.

## 0. Antes de tudo (uma vez)

- **Visibilidade do repositório de código:** `luccaamp/radar-seguro-cartorio` **já está público** (conferido com `gh repo view` em 2026-10-19). Se precisar mudar: *Settings → General → Danger Zone → Change repository visibility*.
- **Repositório de dados:** `luccaamp/radar-seguro-cartorio-dados` deve continuar **privado**.
- **Auditoria do histórico** (2026-10-19, 8 commits): nada exige reescrever o histórico (ver `docs/diario.md`).
- **Backup externo de `C:\radar_arquivo\`:** depois da D-032, é a única cópia local dos originais grandes (14,8 GB) e da linha de base da limpeza. As fontes podem trocar o arquivo publicado. O Release `originais-<ano>` (passo 3) já serve de cópia externa dos originais, menos os `.COMT`, que saem do `.7z`; um disco externo é a segunda.
- **Silver no Release público:** aprovado (D-030), com a regra corrigida: nenhuma estimativa do modelo por serventia, dados de origem sem dado pessoal.

## 1. Gerar o conjunto público e os pacotes

```powershell
uv run pipeline.py                                   # carga nova (ou --a-partir-de silver)
uv run python scripts/gerar_publico.py               # data/publico/ (versionado): auditor + LGPD + manifesto
uv run pytest                                        # suíte padrão (inclui coerência do conjunto público)
uv run pytest -m dados_reais                         # testes com os dados completos
uv run python scripts/empacotar_dados.py --nivel publico      # C:\radar_pacotes\publico   (≈ 3 MB; a cada carga)
uv run python scripts/empacotar_dados.py --nivel equipe       # C:\radar_pacotes\equipe    (≈ 85 MB; a cada carga)
uv run python scripts/empacotar_dados.py --nivel originais    # C:\radar_pacotes\originais (≈ 8,3 GB; uma vez por ano de originais)
```

**Três Releases, cada um com seu manifesto:**

| Release | Repositório | Quando | Conteúdo |
|---|---|---|---|
| `dados-<carga>` | público | a cada carga | silver (D-030, D-031) |
| `carga-<carga>` | privado | a cada carga | **sempre enxuto**: bronze oficial (extratos + `original.json`), silver, gold completo, banco |
| `originais-<ano>` | privado | **uma vez** (e de novo só se os originais mudarem) | os originais grandes (zips do CNPJ, `.7z` da RAIS, `BaseCompleta.zip` da SUSEP), **menos os `.COMT`** da RAIS |

Os `.COMT` (6,5 GB) ficam fora porque saem do `.7z`: o coletor extrai de novo quando faltam, e regerar o extrato a partir do `.7z` dá o mesmo SHA-256 (`tests/test_coletores.py`). A regra está em `config/pacotes.yaml` (`originais_excluir`).

**Onde ficam os pacotes:** por padrão em `C:\radar_pacotes\<nivel>`, fora da pasta do projeto (`config/pacotes.yaml`, `pastas.pacotes`, ou a variável `RADAR_PACOTES`). O projeto fica em `C:\projetos\radar-seguro-cartorio`, fora do OneDrive (D-033); os pacotes continuam fora dele para o clone ficar leve e nada grande entrar no git por engano. Nunca gere pacotes dentro de uma pasta sincronizada (OneDrive): pode estourar a cota gratuita.

Cada script imprime os tamanhos por camada e o total. O `manifesto.json` de cada pacote tem a carga, a data de referência de cada fonte, a versão das premissas, o commit e o SHA-256 e o tamanho de cada arquivo e de cada parte.

## 2. Commit do código e do conjunto público

Faça o commit (inclui `data/publico/`) e o push para a `main` (ou PR, depois da proteção do passo 4). O Release público deve apontar para um commit que já tenha o mesmo `data/publico/` da carga.

## 3. Publicar os Releases

**Público** (qualquer pessoa baixa sem login):
```powershell
gh release create dados-2026-10-19 C:\radar_pacotes\publico\silver-2026-10-19.zip C:\radar_pacotes\publico\manifesto.json `
  --repo luccaamp/radar-seguro-cartorio --target main `
  --title "Dados públicos — carga 2026-10-19" `
  --notes "Silver da carga 2026-10-19 (dados de origem das fontes oficiais, sem dado pessoal; D-030). Instalar: uv run python scripts/baixar_dados.py --nivel publico --camadas silver --carga 2026-10-19"
```

**Equipe, carga** (privado; sempre enxuto, a cada carga):
```powershell
$arquivos = (Get-ChildItem C:\radar_pacotes\equipe -File).FullName
gh release create carga-2026-10-19 $arquivos --repo luccaamp/radar-seguro-cartorio-dados `
  --title "Carga 2026-10-19" `
  --notes "Bronze oficial (extratos + original.json), silver, gold completo (com interno_*) e banco. Uso interno (CONTRIBUTING.md, LGPD da equipe). Originais grandes: Release originais-2026."
```

**Equipe, originais** (privado; **uma vez**: os originais não mudam a cada carga):
```powershell
$arquivos = (Get-ChildItem C:\radar_pacotes\originais -File).FullName
gh release create originais-2026 $arquivos --repo luccaamp/radar-seguro-cartorio-dados `
  --title "Originais 2026 (CNPJ 2026-10, RAIS 2025, SUSEP 2026-10-17)" `
  --notes "Originais grandes das fontes (D-032), menos os .COMT da RAIS (saem do .7z). Instalar: uv run python scripts/baixar_dados.py --nivel originais --ano 2026"
```
Se um snapshot novo de CNPJ, RAIS ou SUSEP for coletado, gere de novo com `--nivel originais` e suba só os arquivos novos com `gh release upload originais-2026 <arquivo> --repo ...` (ou crie `originais-<ano novo>`). Nunca apague um Release de originais em uso.

- **O que vai para cada Release** (tamanhos de 2026-10-20):
  - **o público:** 1 zip e o manifesto;
  - **o da carga:** 12 arquivos e o manifesto;
  - **o dos originais:** 6 arquivos (≈ 8,3 GB) e o manifesto. São 25 originais; o CNPJ vai em partes `.partNNN` de menos de 2 GiB.
- **Upload que falhar no meio:** use `gh release upload <tag> <arquivo> --repo ... --clobber` só para o arquivo que faltou.
- **Pelo site** (arquivos pequenos, como o Release público): *Releases → Draft a new release → Choose a tag* (digite `dados-2026-10-19`, "Create new tag") → arraste o zip e o `manifesto.json` → *Publish release*.

**Conferir depois de publicar**, num clone temporário fora da pasta do projeto (e fora do OneDrive):
```powershell
uv run python scripts/baixar_dados.py --nivel publico --camadas silver --carga 2026-10-19
uv run python scripts/baixar_dados.py --nivel equipe --camadas banco --carga 2026-10-19
uv run python scripts/baixar_dados.py --nivel originais --ano 2026   # vai para a pasta de originais, fora do projeto
```

## 4. Proteger a `main` no repositório público

**Situação atual (2026-10-20): feito.** A ruleset `main protegida` está **ativa** no repositório público, com:
- ✅ *Restrict deletions*;
- ✅ *Require a pull request before merging*, com **Required approvals = 0**;
- ✅ *Block force pushes*;
- **Bypass list:** o **dono do repositório** (o autor), por escolha própria.

Na prática:
- **o autor** pode dar push direto na `main` (está na Bypass list); mesmo assim, ninguém apaga a `main` nem força push nela;
- **os colaboradores** não podem dar push direto: trabalham numa branch e abrem um PR, e o merge não exige aprovação de outra pessoa (0 aprovações).

Como foi criada (para refazer em outro repositório): *Settings → Rules → Rulesets → New ruleset → New branch ruleset*:

1. **Ruleset name:** `main protegida`. **Enforcement status:** *Active*.
2. **Target branches:** *Add target → Include default branch*.
3. **Branch rules:** as três marcadas acima.
4. **Bypass list:** *Add bypass* → o dono do repositório (ou deixe vazia, se quiser que nem o dono dê push direto).
5. *Create*.

Teste: um colaborador que der `git push origin main` deve ser recusado; um PR dele deve permitir o merge sem aprovação de outra pessoa. O push direto do autor passa, por causa da Bypass list.

## 5. Convidar colaboradores

Nos **dois** repositórios: *Settings → Collaborators → Add people* (nome de usuário ou e-mail do GitHub).

- Em repositório de conta pessoal, todo colaborador recebe permissão de escrita. No repositório de código, a proteção do passo 4 impede push direto na `main`. No de dados, a regra "ninguém apaga nem substitui Release" está no `CONTRIBUTING.md`.
- Mande o link do `CONTRIBUTING.md`. Ele explica o `gh auth login` e o `baixar_dados.py --nivel equipe`.

## 6. Checklist de "nova carga"

1. `uv run pipeline.py ingest` (precisa de internet). Os originais grandes vão para `C:\radar_arquivo\bronze_originais`; o bronze recebe os extratos e o `original.json` (D-032). Atualize os snapshots em `config/escopo.yaml`. Rode `uv run pytest -m dados_reais tests/test_coletores.py`: regerar cada extrato a partir do original dá o mesmo SHA-256.
2. `uv run pipeline.py`. Contratos sem erro; leia os avisos das reconciliações.
3. Confira os números de referência na página Início e explique no `docs/diario.md` o que mudou e por quê, com a cascata.
4. `uv run python scripts/gerar_publico.py`. Precisa sair com "0 vazamentos" e "ok"; senão, não publique.
5. `uv run pytest`, `uv run pytest -m dados_reais` e, se o painel mudou, `uv run pytest -m visual`.
6. `uv run python scripts/prints_painel.py --saida docs/qa/atual --checar` e uma olhada na galeria.
7. Commit e push (ou PR) com `data/publico/`.
8. Os dois pacotes e os dois Releases (passos 1 e 3), com a data nova.
9. Teste a instalação a partir dos Releases (fim do passo 3).
10. Atualize a carga citada no README ("Como rodar", passo 2).

## 7. Manter as últimas 3 cargas

```powershell
gh release list --repo luccaamp/radar-seguro-cartorio
gh release list --repo luccaamp/radar-seguro-cartorio-dados
# a mais antiga, quando houver mais de 3 (a decisão é sua; apagar Release não tem volta):
gh release delete dados-AAAA-MM-DD --repo luccaamp/radar-seguro-cartorio --cleanup-tag
gh release delete carga-AAAA-MM-DD --repo luccaamp/radar-seguro-cartorio-dados --cleanup-tag
```

O número de cargas mantidas está em `config/pacotes.yaml` (`manter_ultimas_cargas: 3`).
