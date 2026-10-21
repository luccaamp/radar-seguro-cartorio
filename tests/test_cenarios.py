"""Cenários salvos do painel num arquivo próprio (D-034, src/cenarios.py). Arquivos temporários; nada em data/."""
import json

from src import cenarios

CENARIO = {"nome": "taxa 3%", "versao_premissas": 2, "cenario_stf": "mantem", "regra_classe": "v2",
           "metodo_rateio": "por_empregados_cnj", "nivel": "base", "premissas_alteradas": {}, "ajustes": {},
           "resultado": {"premio": 1.5}}


def test_sem_arquivo_comeca_vazio_e_cria_no_primeiro_salvar(tmp_path):
    arq = tmp_path / "sub" / "painel_estado.json"
    assert cenarios.ler(arq) == ([], None)
    assert cenarios.salvar(CENARIO, arq) == 1
    dados = json.loads(arq.read_text(encoding="utf-8"))
    assert dados["formato"] == cenarios.FORMATO and dados["cenarios"][0]["nome"] == "taxa 3%"


def test_salvos_continuam_numa_leitura_nova(tmp_path):
    arq = tmp_path / "painel_estado.json"
    ids = [cenarios.salvar({**CENARIO, "nome": n}, arq) for n in ("a", "b")]
    salvos, aviso = cenarios.ler(arq)   # leitura nova do disco = painel reiniciado
    assert ids == [1, 2] and aviso is None and [c["nome"] for c in salvos] == ["a", "b"]
    assert all("criado_em" in c for c in salvos)
    assert not list(tmp_path.glob("*.novo"))   # gravação atômica: nenhum temporário sobra


def test_arquivo_corrompido_abre_com_aviso_e_e_guardado_ao_salvar(tmp_path):
    arq = tmp_path / "painel_estado.json"
    arq.write_text('{"formato": 1, "cenarios": [', encoding="utf-8")
    salvos, aviso = cenarios.ler(arq)
    assert salvos == [] and aviso and "corrompido" in aviso
    assert cenarios.salvar(CENARIO, arq) == 1
    guardados = list(tmp_path.glob("painel_estado.json.corrompido-*"))
    assert len(guardados) == 1 and guardados[0].read_text(encoding="utf-8") == '{"formato": 1, "cenarios": ['
    assert cenarios.ler(arq)[1] is None


def test_estrutura_inesperada_conta_como_corrompido(tmp_path):
    arq = tmp_path / "painel_estado.json"
    arq.write_text("[1, 2]", encoding="utf-8")
    assert cenarios.ler(arq)[1]


def test_caminho_segue_a_variavel(tmp_path, monkeypatch):
    monkeypatch.setenv("RADAR_ESTADO", str(tmp_path / "x.json"))
    assert cenarios.caminho() == tmp_path / "x.json"
    monkeypatch.delenv("RADAR_ESTADO")
    assert cenarios.caminho() == cenarios.RAIZ / "data" / "painel_estado.json"
