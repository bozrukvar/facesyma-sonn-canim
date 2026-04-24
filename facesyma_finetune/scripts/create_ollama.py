"""
scripts/create_ollama.py
========================
Fine-tuned modeli Ollama'ya kaydet (geliştirme ortamı için).

Unsloth train.py zaten GGUF üretir.
Bu script sadece Modelfile'ı oluşturup Ollama'ya kaydeder.

Kullanım:
  python create_ollama.py --gguf ../training/facesyma-llama3.1-8b_gguf
  python create_ollama.py --gguf model.gguf --name facesyma
"""

import subprocess, sys, argparse
from pathlib import Path

MODELFILE_TEMPLATE = """\
FROM {gguf_path}

SYSTEM \"\"\"\
Sen Facesyma'nın yapay zeka kişisel danışmanısın. \
Yüz analizi sonuçlarını kullanarak derin karakter içgörüleri, \
kariyer önerileri, liderlik analizi ve kişisel gelişim tavsiyeleri sunarsın. \
Samimi, destekleyici ve spesifik ol. Türkçe konuş.
\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096
PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|end_of_text|>"
"""


def find_gguf(gguf_dir: Path) -> Path:
    """Dizindeki ilk .gguf dosyasını bul."""
    candidates = sorted(gguf_dir.glob("*.gguf"))
    if not candidates:
        raise FileNotFoundError(f"{gguf_dir} içinde .gguf dosyası bulunamadı.")
    # Q4_K_M öncelikli
    for c in candidates:
        if "q4_k_m" in c.name.lower():
            return c
    return candidates[0]


def run(cmd: list):
    print(f"$ {' '.join(str(c) for c in cmd)}")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"HATA: komut başarısız")
        sys.exit(1)


def main():
    p = argparse.ArgumentParser()
    _paa = p.add_argument
    _paa("--gguf",  required=True, help="GGUF dizini veya dosyası")
    _paa("--name",  default="facesyma", help="Ollama model adı")
    args = p.parse_args()

    _name = _name
    gguf_path = Path(args.gguf)
    if gguf_path.is_dir():
        gguf_path = find_gguf(gguf_path)

    if not gguf_path.exists():
        print(f"HATA: {gguf_path} bulunamadı")
        sys.exit(1)

    print(f"GGUF: {gguf_path} ({gguf_path.stat().st_size/1e9:.1f} GB)")

    # Modelfile oluştur
    modelfile = gguf_path.parent / "Modelfile"
    modelfile.write_text(MODELFILE_TEMPLATE.format(gguf_path=gguf_path.resolve()))
    print(f"Modelfile: {modelfile}")

    # Ollama'ya kaydet
    print(f"\nOllama'ya kaydediliyor: {_name}")
    run(["ollama", "create", _name, "-f", str(modelfile)])

    print(f"\nHazır! Test:")
    print(f"  ollama run {_name}")
    print(f"\nAPI:")
    print(f"  curl http://localhost:11434/api/chat -d '{{")
    print(f'    "model":"{_name}",')
    print(f'    "messages":[{{"role":"user","content":"Merhaba!"}}]')
    print(f"  }}'")


if __name__ == "__main__":
    main()
