"""D-032, uso único (2026-10-19): cria o original.json das pastas do bronze da carga atual a partir do _metadados.json
que os coletores gravavam, PRESERVANDO URL, tamanho, SHA-256 e a hora de coleta original. Não move nada (o movimento
dos originais é feito à parte, com MANIFESTO.md em C:\\radar_arquivo). Não sobrescreve um original.json existente.

Uso: uv run python scripts/arquivo/d032_registrar_originais.py [raiz do projeto]
"""
import json
import sys
from pathlib import Path

PASTAS = ["rais/2025", "cnpj/2026-10", "susep_ses/2026-10-17"]   # snapshots da carga oficial (config/escopo.yaml)

raiz = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
for rel in PASTAS:
    pasta = raiz / "data" / "bronze" / rel
    destino = pasta / "original.json"
    if destino.exists():
        print(f"{rel}: original.json já existe, nada a fazer")
        continue
    meta = json.loads((pasta / "_metadados.json").read_text(encoding="utf-8"))
    arquivos = {nome: {"url": m["url"], "bytes": m["bytes"], "sha256": m["sha256"], "coletado_em": m["coletado_em"],
                       "versao_coletor": m.get("versao_coletor"), "guardado_em": f"{rel}/{nome}"}
                for nome, m in meta.items()}   # mesma ordem do _metadados.json
    destino.write_text(json.dumps({
        "descricao": "Originais desta fonte (D-032): ficam fora do bronze oficial, na pasta de originais "
                     "(config/pacotes.yaml); aqui ficam o registro e o extrato que o silver lê. Gerado a partir do "
                     "_metadados.json da coleta (2026-10-19).", "arquivos": arquivos}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"{rel}: original.json com {len(arquivos)} originais")
