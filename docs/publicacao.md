# Publicação: Releases de dados, repositório público e equipe

Passo a passo para o autor. Os scripts só geram arquivos locais. **Commit, push, Releases e configurações do GitHub são feitos por você**, com os comandos abaixo. Comandos em PowerShell; no Linux/macOS, troque `C:\radar_pacotes` por `~/radar_pacotes` (padrões em `config/pacotes.yaml`).

Carga de referência neste documento: `2026-10-19`.

## 0. Antes de tudo (uma vez)

- **Visibilidade do repositório de código:** `luccaamp/radar-seguro-cartorio` **já está público** (conferido com `gh repo view` em 2026-10-19). Se precisar mudar: *Settings → General → Danger Zone → Change repository visibility*.
- **Repositório de dados:** `luccaamp/radar-seguro-cartorio-dados` deve continuar **privado**.
- **Auditoria do histórico** (2026-10-19, 8 commits): nada exige reescrever o histórico (ver `docs/diario.md`).
- **Backup externo de `C:\radar_arquivo\`:** depois da D-032, é a única cópia local dos originais grandes (14,8 GB) e da linha de base da limpeza. As fontes podem trocar o arquivo publicado. Publicar o pacote `--com-originais` no Release privado já serve de cópia externa; um disco externo é a segunda.
- **Silver no Release público:** aprovado (D-030), com a regra corrigida: nenhuma estimativa do modelo por serventia, dados de origem sem dado pessoal.

## 1. Gerar o conjunto público e os dois pacotes

```powershell
uv run pipeline.py                                   # carga nova (ou --a-partir-de silver)
uv run python scripts/gerar_publico.py               # data/publico/ (versionado): auditor + LGPD + manifesto
uv run pytest                                        # suíte padrão (inclui coerência do conjunto público)
uv run pytest -m dados_reais                         # testes com os dados completos
uv run python scripts/empacotar_dados.py --nivel publico                     # C:\radar_pacotes\publico (≈ 3 MB)
uv run python scripts/empacotar_dados.py --nivel equipe                      # C:\radar_pacotes\equipe (≈ 85 MB)
uv run python scripts/empacotar_dados.py --nivel equipe --com-originais --saida C:\radar_pacotes\equipe_com_originais   # ≈ 9,8 GB
```

**Onde ficam os pacotes:**
- por padrão em `C:\radar_pacotes\<nivel>`, fora do OneDrive (`config/pacotes.yaml`, `pastas.pacotes`, ou a variável `RADAR_PACOTES`). O projeto fica no OneDrive, e gerar pacotes grandes dentro dele faria o OneDrive sincronizar tudo, o que pode estourar a cota gratuita;
- desde a D-032, o bronze oficial tem 144 MB, então o pacote da equipe caiu de 8,4 GB para ≈ 85 MB. Os originais grandes (14,8 GB, ≈ 9,7 GB comprimidos) entram só com `--com-originais`.

Cada script imprime os tamanhos por camada e o total. O `manifesto.json` de cada pacote tem a carga, a data de referência de cada fonte, a versão das premissas, o commit e o SHA-256 e o tamanho de cada arquivo e de cada parte.

## 2. Commit do código e do conjunto público

Faça o commit (inclui `data/publico/`) e o push para a `main` (ou PR, depois da proteção do passo 4). O Release público deve apontar para um commit que já tenha o mesmo `data/publico/` da carga.

## 3. Publicar os dois Releases

**Público** (qualquer pessoa baixa sem login):
```powershell
gh release create dados-2026-10-19 C:\radar_pacotes\publico\silver-2026-10-19.zip C:\radar_pacotes\publico\manifesto.json `
  --repo luccaamp/radar-seguro-cartorio --target main `
  --title "Dados públicos — carga 2026-10-19" `
  --notes "Silver da carga 2026-10-19 (dados de origem das fontes oficiais, sem dado pessoal; D-030). Instalar: uv run python scripts/baixar_dados.py --nivel publico --camadas silver --carga 2026-10-19"
```

**Equipe** (privado; arquivos em partes abaixo de 2 GiB). Escolha **um** dos dois pacotes para o Release `carga-<data>`, porque cada Release tem um `manifesto.json` só:
- **com originais (recomendado):** `C:\radar_pacotes\equipe_com_originais`, 19 arquivos, ≈ 9,8 GB. Tem tudo do pacote enxuto, mais a camada `originais`. Serve também como **cópia externa** dos originais, que hoje só existem em `C:\radar_arquivo\` (D-032);
- **enxuto:** `C:\radar_pacotes\equipe`, 12 arquivos, ≈ 85 MB. Use se não quiser subir os originais.

```powershell
$arquivos = (Get-ChildItem C:\radar_pacotes\equipe_com_originais -File).FullName
gh release create carga-2026-10-19 $arquivos --repo luccaamp/radar-seguro-cartorio-dados `
  --title "Carga 2026-10-19 (completa)" `
  --notes "Bronze oficial (extratos + original.json), silver, gold completo (com interno_*), banco e originais grandes (camada originais). Uso interno (CONTRIBUTING.md, LGPD da equipe)."
```

- **O que vai para cada Release:**
  - **o público** leva 1 zip e o manifesto;
  - **o da equipe com originais** leva 19 arquivos e o manifesto. O CNPJ original vai em partes `.partNNN`, cada uma abaixo de 2 GiB.
- **Upload que falhar no meio:** use `gh release upload carga-2026-10-19 <arquivo> --repo ... --clobber` só para o arquivo que faltou.
- **Pelo site** (arquivos pequenos, como o Release público): *Releases → Draft a new release → Choose a tag* (digite `dados-2026-10-19`, "Create new tag") → arraste o zip e o `manifesto.json` → *Publish release*.

**Conferir depois de publicar**, numa pasta fora do OneDrive:
```powershell
uv run python scripts/baixar_dados.py --nivel publico --camadas silver --carga 2026-10-19
uv run python scripts/baixar_dados.py --nivel equipe --camadas banco --carga 2026-10-19
```

## 4. Proteger a `main` no repositório público

*Settings → Rules → Rulesets → New ruleset → New branch ruleset*:

1. **Ruleset name:** `main protegida`. **Enforcement status:** *Active*.
2. **Target branches:** *Add target → Include default branch*.
3. **Branch rules:**
   - ✅ *Restrict deletions*;
   - ✅ *Require a pull request before merging*, com **Required approvals = 0**. Assim você, único revisor, faz merge dos próprios PRs; o push direto na `main` fica bloqueado para todos;
   - ✅ *Block force pushes*.
4. **Bypass list:** deixe vazia, para que nem você consiga dar push direto. Se um dia precisar de uma correção urgente sem PR, adicione temporariamente *Repository admin* com *Allow for pull requests only* ou *Always*, e retire depois.
5. *Create*.

Teste: `git push origin main` com um commit local deve ser recusado; um PR deve permitir o merge sem aprovação de outra pessoa.

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
