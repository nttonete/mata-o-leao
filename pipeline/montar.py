#!/usr/bin/env python3
"""Monta um vídeo do Mata o Leão a partir de uma pasta de roteiro.

Uso:  python3 pipeline/montar.py roteiros/2026-10-27-slug

A pasta precisa ter:
  roteiro.json   (ver roteiros/MODELO-roteiro.json)
  audio/01.mp3, audio/02.mp3, ...   uma narração por segmento, na ordem

Saída: videos/<nome-da-pasta>.mp4  (1080x1920, H.264 + AAC, -14 LUFS)
"""
import json
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTES = os.path.join(RAIZ, "assets", "fonts")
LEAO = os.path.join(RAIZ, "assets", "leao-abertura.mp4")

W, H, FPS = 1080, 1920, 30
# Zonas seguras do TikTok: barra de busca no topo, ícones à direita, legenda embaixo.
TOP_SAFE = 290
SIDE = 150
BOTTOM_SAFE = 440

CORES = {
    "fundo": (12, 18, 15), "fundo2": (20, 32, 25),
    "dourado": (240, 185, 60), "branco": (245, 245, 240), "cinza": (150, 165, 155),
    "verde": (60, 200, 120), "vermelho": (235, 90, 80),
}
PESOS = {"black": "InterDisplay-Black.otf", "xbold": "InterDisplay-ExtraBold.otf",
         "bold": "InterDisplay-Bold.otf", "semi": "InterDisplay-SemiBold.otf"}


def sh(*cmd):
    subprocess.run(cmd, check=True)


def duracao(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def font(peso, tam):
    return ImageFont.truetype(os.path.join(FONTES, PESOS[peso]), tam)


def wrap(d, texto, f, maxw):
    linhas, cur = [], ""
    for w in texto.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            linhas.append(cur)
            cur = w
    linhas.append(cur)
    return linhas


def fit(d, texto, peso, tam, maxw, manchete=False):
    """Quebra o texto sem estourar a largura. Manchetes (>=100px) encolhem para caber numa linha.
    Se encolher até 15% economizar uma linha, encolhe (evita palavra sozinha)."""
    f = font(peso, tam)
    if manchete:
        while d.textlength(texto, font=f) > maxw and tam > 60:
            tam -= 4
            f = font(peso, tam)
    linhas = wrap(d, texto, f, maxw)
    while any(d.textlength(l, font=f) > maxw for l in linhas) and tam > 30:
        tam -= 4
        f = font(peso, tam)
        linhas = wrap(d, texto, f, maxw)
    if len(linhas) > 1:
        for t2 in range(tam - 2, int(tam * 0.85) - 1, -2):
            f2 = font(peso, t2)
            l2 = wrap(d, texto, f2, maxw)
            if len(l2) < len(linhas):
                return l2, f2, t2
    return linhas, f, tam


def fundo():
    img = Image.new("RGB", (W, H), CORES["fundo"])
    d = ImageDraw.Draw(img)
    a, b = CORES["fundo"], CORES["fundo2"]
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3)))
    return img


def moldura(d, rodape):
    tag, f = "MATA O LEÃO", font("black", 40)
    tw = d.textlength(tag, font=f)
    x = (W - tw) / 2
    d.rounded_rectangle([x - 28, TOP_SAFE + 10, x + tw + 28, TOP_SAFE + 82], radius=36, fill=CORES["dourado"])
    d.text((x, TOP_SAFE + 20), tag, font=f, fill=CORES["fundo"])
    if rodape:
        f2 = font("semi", 30)
        linhas = wrap(d, rodape, f2, W - 2 * SIDE)
        y = H - BOTTOM_SAFE + 10 - (len(linhas) - 1) * 36
        for ln in linhas:
            d.text(((W - d.textlength(ln, font=f2)) / 2, y), ln, font=f2, fill=CORES["cinza"])
            y += 36


def cartela(blocos, rodape, saida):
    """blocos: [{"t": texto, "peso": "bold", "tam": 72, "cor": "branco", "gap": 30}
                 | {"caixa": texto, "cor": "dourado", "tam": 90}]"""
    img = fundo()
    d = ImageDraw.Draw(img)
    moldura(d, rodape)
    maxw = W - 2 * SIDE
    itens, total = [], 0
    for b in blocos:
        if "caixa" in b:
            linhas, f, tam = fit(d, b["caixa"], "black", b.get("tam", 80), maxw - 80)
            h = len(linhas) * int(tam * 1.15) + 70
            itens.append(("caixa", linhas, f, CORES[b.get("cor", "dourado")], tam, h))
            total += h + 50
        else:
            tam = b.get("tam", 72)
            linhas, f, tam = fit(d, b["t"], b.get("peso", "bold"), tam, maxw, manchete=tam >= 100)
            lh = int(tam * 1.15)
            gap = b.get("gap", 30)
            itens.append(("texto", linhas, f, CORES[b.get("cor", "branco")], lh, gap))
            total += lh * len(linhas) + gap
    topo, base = TOP_SAFE + 140, H - BOTTOM_SAFE - 40
    y = topo + max(0, (base - topo - total) / 2)
    for it in itens:
        if it[0] == "caixa":
            _, linhas, f, cor, tam, h = it
            d.rounded_rectangle([SIDE - 20, y, W - SIDE + 20, y + h], radius=40, fill=cor)
            ty = y + 35
            for ln in linhas:
                d.text(((W - d.textlength(ln, font=f)) / 2, ty), ln, font=f, fill=CORES["fundo"])
                ty += int(tam * 1.15)
            y += h + 50
        else:
            _, linhas, f, cor, lh, gap = it
            for ln in linhas:
                d.text(((W - d.textlength(ln, font=f)) / 2, y), ln, font=f, fill=cor)
                y += lh
            y += gap
    img.save(saida)


def gancho_png(gancho, saida):
    """Texto por cima do leão: {"linha1": "EMPRESA DO SIMPLES?", "destaque": "PRAZO: 30/10", "linha2": "(nesta sexta)"}"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(850, H):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(220 * (y - 850) / (H - 850))))
    moldura(d, None)
    maxw = W - 2 * SIDE
    y = 1110
    if gancho.get("linha1"):
        linhas, f, tam = fit(d, gancho["linha1"], "black", 64, maxw)
        for ln in linhas:
            d.text(((W - d.textlength(ln, font=f)) / 2, y), ln, font=f, fill=CORES["branco"])
            y += int(tam * 1.15)
        y += 25
    if gancho.get("destaque"):
        linhas, f, tam = fit(d, gancho["destaque"], "black", 110, maxw - 80, manchete=True)
        for ln in linhas:
            tw = d.textlength(ln, font=f)
            d.rounded_rectangle([(W - tw) / 2 - 40, y, (W + tw) / 2 + 40, y + tam * 1.4], radius=30, fill=CORES["dourado"])
            d.text(((W - tw) / 2, y + tam * 0.13), ln, font=f, fill=CORES["fundo"])
            y += tam * 1.4 + 20
        y += 15
    if gancho.get("linha2"):
        linhas, f, tam = fit(d, gancho["linha2"], "bold", 52, maxw)
        for ln in linhas:
            d.text(((W - d.textlength(ln, font=f)) / 2, y), ln, font=f, fill=CORES["branco"])
            y += int(tam * 1.15)
    if y > H - BOTTOM_SAFE:
        print("AVISO: gancho invade a área da legenda; encurte o texto", file=sys.stderr)
    img.save(saida)


def clipe_cartela(png, dur, saida):
    n = math.ceil(dur * FPS)
    sh("ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-i", png, "-t", f"{dur:.3f}",
       "-vf", f"scale=2160:3840,zoompan=z='1+0.05*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
              f":d={n}:s={W}x{H}:fps={FPS},format=yuv420p",
       "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", saida)


def main(pasta):
    pasta = os.path.abspath(pasta)
    nome = os.path.basename(pasta.rstrip("/"))
    rot = json.load(open(os.path.join(pasta, "roteiro.json"), encoding="utf-8"))
    tmp = os.path.join(pasta, "_build")
    os.makedirs(tmp, exist_ok=True)
    rodape = rot.get("rodape", "Conteúdo educativo")
    segs = rot["segmentos"]

    # 1) narração: tira pausas longas, mede cada trecho
    wavs, durs = [], []
    for i, _ in enumerate(segs, 1):
        src = os.path.join(pasta, "audio", f"{i:02d}.mp3")
        dst = os.path.join(tmp, f"a{i:02d}.wav")
        sh("ffmpeg", "-y", "-v", "error", "-i", src, "-af",
           "silenceremove=start_periods=1:start_threshold=-40dB:stop_periods=-1:stop_duration=0.35:"
           "stop_threshold=-40dB:stop_silence=0.22,apad=pad_dur=0.15,aresample=48000", "-ac", "2", dst)
        wavs.append(dst)
        durs.append(duracao(dst))

    # 2) vídeo: abertura com o leão (opcional) + uma cartela por segmento
    partes = []
    abertura = rot.get("abertura") or {}
    usar_leao = abertura.get("leao", True) and os.path.exists(LEAO)
    for i, (seg, dur) in enumerate(zip(segs, durs), 1):
        png = os.path.join(tmp, f"c{i:02d}.png")
        cartela(seg["cartela"], rodape, png)
        if i == 1 and usar_leao:
            lt = min(5.0, dur)
            gp = os.path.join(tmp, "gancho.png")
            gancho_png(abertura.get("gancho", {}), gp)
            p = os.path.join(tmp, "v00.mp4")
            sh("ffmpeg", "-y", "-v", "error", "-i", LEAO, "-loop", "1", "-i", gp, "-t", f"{lt:.3f}",
               "-filter_complex",
               f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1[v];"
               "[1:v]format=rgba,fade=in:st=0.3:d=0.35:alpha=1[o];[v][o]overlay=0:0:shortest=1,format=yuv420p",
               "-t", f"{lt:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", p)
            partes.append(p)
            if dur - lt > 0.3:
                p2 = os.path.join(tmp, "v01.mp4")
                clipe_cartela(png, dur - lt, p2)
                partes.append(p2)
        else:
            p = os.path.join(tmp, f"v{i:02d}.mp4")
            clipe_cartela(png, dur, p)
            partes.append(p)

    lista = os.path.join(tmp, "vlist.txt")
    open(lista, "w").write("".join(f"file '{p}'\n" for p in partes))
    video = os.path.join(tmp, "video.mp4")
    sh("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", video)

    # 3) áudio: narração + rugido do leão por baixo nos primeiros segundos
    alista = os.path.join(tmp, "alist.txt")
    open(alista, "w").write("".join(f"file '{w}'\n" for w in wavs))
    narr = os.path.join(tmp, "narracao.wav")
    sh("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", alista, "-c", "pcm_s16le", narr)
    # música de fundo (opcional): assets/musica/<arquivo>, baixa e abaixando mais quando há voz
    musica = rot.get("musica")
    if musica:
        trilha = os.path.join(RAIZ, "assets", "musica", musica)
        total = duracao(narr)
        com_musica = os.path.join(tmp, "narracao_musica.wav")
        sh("ffmpeg", "-y", "-v", "error", "-i", narr, "-stream_loop", "-1", "-i", trilha, "-filter_complex",
           f"[1:a]aresample=48000,atrim=0:{total:.3f},volume={rot.get('volume_musica', 0.5)},"
           f"afade=in:st=0:d=1.5,afade=out:st={max(total - 2.5, 0):.3f}:d=2.5[m];"
           "[0:a]asplit=2[v][sc];"
           "[m][sc]sidechaincompress=threshold=0.05:ratio=3:attack=30:release=400[md];"
           "[v][md]amix=inputs=2:duration=first:normalize=0[a]",
           "-map", "[a]", "-c:a", "pcm_s16le", com_musica)
        narr = com_musica
    mix = os.path.join(tmp, "mix.wav")
    if usar_leao:
        sh("ffmpeg", "-y", "-v", "error", "-i", narr, "-i", LEAO, "-filter_complex",
           "[1:a]atrim=0:5,afade=out:st=3.8:d=1.2,volume=0.35,aresample=48000[r];"
           "[0:a][r]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
           "-map", "[a]", "-c:a", "pcm_s16le", mix)
    else:
        sh("ffmpeg", "-y", "-v", "error", "-i", narr, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", mix)

    os.makedirs(os.path.join(RAIZ, "videos"), exist_ok=True)
    final = os.path.join(RAIZ, "videos", f"{nome}.mp4")
    sh("ffmpeg", "-y", "-v", "error", "-i", video, "-i", mix, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
       "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", final)

    # 4) capa (frame com o gancho) e folha de contato para conferência visual
    sh("ffmpeg", "-y", "-v", "error", "-ss", "2", "-i", final, "-frames:v", "1", os.path.join(tmp, "capa.jpg"))
    thumbs = [Image.open(os.path.join(tmp, f"c{i:02d}.png")).convert("RGB").resize((216, 384))
              for i in range(1, len(segs) + 1)]
    folha = Image.new("RGB", (216 * len(thumbs), 384))
    for k, t in enumerate(thumbs):
        folha.paste(t, (216 * k, 0))
    folha.save(os.path.join(tmp, "conferencia.png"))
    print(f"OK {final}  {duracao(final):.1f}s")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
