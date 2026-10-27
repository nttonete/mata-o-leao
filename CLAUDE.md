# Mata o Leão – vídeo diário no TikTok

Conta de TikTok **@mataoleao** sobre impostos (reforma tributária, Simples, MEI, IR), feita sem aparecer:
narração por IA + cartelas de texto + abertura com um leão de terno. Público: donos de pequenas
empresas e trabalhadores que querem entender imposto sem juridiquês.

Este repositório é **público**: guarda só o modelo, os roteiros e os vídeos publicados. Nunca coloque
aqui dados pessoais, senhas, tokens ou qualquer coisa do dono da conta.

## Rotina diária (o que a tarefa agendada faz)

0. **Já tem post para hoje?** Se `historico.md` já tiver uma linha com a data de hoje (vídeo feito
   antes, por pedido do dono), não crie outro: só confirme com `getScheduledPosts` que ele está
   agendado e termine com um resumo curto.
1. **Escolher o tema.** Leia `pautas.md` e `historico.md`. Antes, faça uma busca rápida por novidades
   de impostos do dia (prazos da Receita, Comitê Gestor do Simples, reforma tributária, IR). Se houver
   prazo ou mudança relevante para o público, ela tem prioridade; senão, pegue a próxima pauta livre.
   Não repita tema já publicado nos últimos 30 dias.
2. **Pesquisar.** Confirme cada número, data e regra em pelo menos duas fontes confiáveis, de
   preferência oficiais (gov.br/receitafederal, Portal do Simples, Diário Oficial, Sebrae, CFC/CRC,
   Senado/Câmara). Se não der para confirmar com segurança, troque de tema. Nunca invente dado.
3. **Escrever o roteiro** em `roteiros/AAAA-MM-DD-slug/roteiro.json` (modelo em
   `roteiros/MODELO-roteiro.json`):
   - 6 a 8 segmentos, narração total de 650–850 caracteres (≈40–55 s).
   - 1º segmento = gancho forte (pergunta ou alerta). Último = chamada: "segue o Mata o Leão".
   - Cada segmento tem uma cartela com pouco texto (manchete + 1 ou 2 linhas).
   - `rodape`: "Conteúdo educativo • Fonte: <órgão/norma>".
   - `legenda`: gancho + 2–4 linhas úteis + pergunta/CTA + 4–8 hashtags (#impostos #mataoleao …).
   - `titulo_tiktok`: título curto (obrigatório no Metricool para TikTok).
   - **Música de fundo (sempre):** alterne entre as duas trilhas de `assets/musica/` (não gaste
     crédito gerando música nova): `"musica": "trilha-1-lofi.mp3", "volume_musica": 0.28` ou
     `"musica": "trilha-2-pop.mp3", "volume_musica": 0.5`. Use a que não foi usada no vídeo anterior
     (veja o roteiro mais recente). O montar.py já abaixa a música quando a voz entra.
   - Tom: simples, direto, sem juridiquês, sem prometer economia, sem orientação personalizada
     ("fale com seu contador" quando a decisão depende do caso). Neutro em política: explique a
     regra, não opine sobre governo, partido ou candidato.
4. **Narração (Runway, `generate_speech`)** – uma chamada por segmento, na ordem:
   `model: eleven_v3`, `voice: James`, `languageCode: por`, `stability: 0.5`, `seed: 11`, e comece
   **todo** `text` com a tag `[Brazilian Portuguese accent] ` (sem ela a voz às vezes puxa sotaque
   de Portugal). Escreva as falas no jeito brasileiro de falar ("você", "pra", "entrar com").
   Busque cada resultado com `get_task` e baixe para `roteiros/<pasta>/audio/01.mp3`, `02.mp3`, …
   Custa ~16 créditos por vídeo. Se a resposta indicar menos de 20 créditos restantes, avise o dono
   (ver "Avisos"). Se faltar crédito para terminar, não publique nada parcial.
5. **Montar:** `python3 pipeline/montar.py roteiros/<pasta>` → `videos/<pasta>.mp4`.
   Abra `roteiros/<pasta>/_build/conferencia.png` e `capa.jpg` e confira: texto cabe, nada cortado,
   sem erro de português. Corrija o roteiro e remonte se precisar.
6. **Publicar o arquivo:** commit de `roteiros/<pasta>/roteiro.json` + `videos/<pasta>.mp4` e push na
   `main`. Link público: `https://raw.githubusercontent.com/nttonete/mata-o-leao/main/videos/<pasta>.mp4`
   (confira com `curl -sI` que responde 200; pode levar 1–2 min depois do push).
7. **Agendar no Metricool** (`createScheduledPost`):
   - `blogId`: `7665544` (marca MataOLeão, TikTok @mataoleao — confira com `getBrandSettings`
     que `tiktokData` é `mataoleao`; se não for, NÃO publique e avise).
   - data: hoje às 19:00 (America/Sao_Paulo). Se já passou das 18:30, agende para amanhã 19:00.
   - `providers: [{"network":"tiktok"}]` — e, se `getBrandSettings` mostrar `instagramData` nessa
     marca, inclua também `{"network":"instagram"}` com
     `instagramData: {"type":"REEL","showReelOnFeed":true,"isAiGenerated":true}`.
   - `autoPublish: true`, `text`: a legenda,
     `media: [<link público>]`, `videoCoverMilliseconds: 2000`,
     `tiktokData: {"privacyOption":"PUBLIC_TO_EVERYONE","isAigc":true,"title":"<título curto do vídeo, obrigatório>","autoAddMusic":false,
     "disableComment":false,"disableDuet":false,"disableStitch":false,
     "commercialContentThirdParty":false,"commercialContentOwnBrand":false,"photoCoverIndex":0}`.
8. **Registrar:** acrescente uma linha em `historico.md` (data, tema, pasta, link do planner do
   Metricool) e marque a pauta como feita em `pautas.md`. Commit + push.

## Avisos ao dono
Ao final, mande um resumo curto (tema, horário agendado). Se algo falhar (pesquisa inconclusiva,
crédito, push, Metricool), não publique pela metade: explique o que travou e o que precisa dele.

## Arquivos
- `pipeline/montar.py` – gera cartelas e monta o vídeo (zonas seguras do TikTok já aplicadas).
- `assets/leao-abertura.mp4` – abertura de 5 s (leão de terno rugindo) usada em todo vídeo.
- `assets/fonts/` – Inter Display (licença OFL em `LICENSE-Inter.txt`).
- Cores das cartelas: `dourado`, `verde`, `vermelho`, `branco`, `cinza`.
