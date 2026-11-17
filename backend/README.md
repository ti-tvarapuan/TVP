# API de legendagem de vídeos

API Flask para legendar vídeos e traduzir documentos. Vídeos passam por extração de áudio com FFmpeg, transcrição com faster-whisper e tradução com TranslateGemma no Ollama. Documentos TXT e PDF com texto selecionável podem ser enviados para tradução direta. O modelo padrão é `translategemma:4b`.

## Como funciona

1. O cliente envia um vídeo ou uma URL HTTP(S) para `POST /api/subtitles`.
2. A API cria em `videos/` uma pasta com o nome do arquivo recebido e salva nela o vídeo e o áudio extraído em WAV mono, 16 kHz.
3. faster-whisper transcreve o áudio em inglês, preservando os tempos dos segmentos.
4. Ollama traduz cada segmento para português brasileiro.
5. A API grava a transcrição traduzida em WebVTT na mesma pasta e retorna caminhos locais e URLs HTTP.
6. Opcionalmente, o cliente envia os caminhos locais para `POST /api/videos/with-subtitles`. FFmpeg cria um MP4 com a faixa de legenda selecionável, também salvo nessa pasta.

O processamento é síncrono: a requisição permanece aberta durante o download, transcrição e tradução.

## Requisitos

- Python 3.10 ou superior
- FFmpeg instalado e disponível no `PATH`
- Ollama instalado e em execução
- Modelo TranslateGemma disponível no Ollama (padrão configurado: `translategemma:4b`)
- Dependências Python listadas em `requirements.txt`

### 1. Instale o Ollama e baixe o modelo

Instale o Ollama pelo [site oficial](https://ollama.com/download), inicie o serviço e baixe o [TranslateGemma](https://ollama.com/library/translategemma) na variante padrão de 4 bilhões de parâmetros:

```powershell
ollama pull translategemma:4b
```

Confira se o modelo está disponível com `ollama list`. Se o nome/tag do modelo que você pretende usar for diferente, atualize `OLLAMA_MODEL` no arquivo `.env`.

### 2. Instale o FFmpeg

Instale uma distribuição do FFmpeg compatível com seu sistema e adicione o executável `ffmpeg` ao `PATH`. Confirme no terminal:

```powershell
ffmpeg -version
```

Se o FFmpeg não estiver no `PATH`, configure `FFMPEG_BINARY` no `.env` com o caminho completo para o executável.

### 3. Prepare o Python e as dependências

## Instalação e execução

No PowerShell, a partir da pasta do projeto:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python main.py
```

Por padrão, o servidor Flask fica disponível em `http://localhost:5000`. O modelo Whisper é carregado sob demanda na primeira requisição de legendagem. O padrão é `small` em GPU NVIDIA (`cuda`) com `float16`.

## Configuração

O projeto carrega as configurações do arquivo `.env` na raiz. Copie `.env.example` para `.env` e ajuste os valores antes de iniciar a API. As configurações também podem ser definidas por variáveis de ambiente do sistema. Exemplo de `.env`:

```powershell
WHISPER_MODEL=small
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=translategemma:4b
```

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `MAX_VIDEO_SIZE_MB` | `2048` | Tamanho máximo de upload ou download por vídeo, em MB. |
| `MAX_DOCUMENT_SIZE_MB` | `25` | Tamanho máximo de cada arquivo TXT ou PDF, em MB. |
| `MAX_DOCUMENT_CHARACTERS` | `500000` | Máximo de caracteres extraídos do documento. |
| `MAX_DOCUMENT_PAGES` | `500` | Máximo de páginas processadas em um PDF. |
| `TRANSLATION_CHUNK_CHARACTERS` | `2500` | Tamanho aproximado dos blocos enviados ao TranslateGemma. |
| `VIDEO_FOLDER` | `videos` na raiz do projeto | Pasta central dos arquivos por vídeo. |
| `FFMPEG_BINARY` | `ffmpeg` | Executável do FFmpeg ou caminho completo para ele. |
| `WHISPER_MODEL` | `small` | Modelo faster-whisper, por exemplo `base`, `small`, `medium` ou `large-v3`. |
| `WHISPER_DEVICE` | `cuda` | Dispositivo do Whisper: `cpu` ou `cuda`. CUDA exige GPU NVIDIA com CUDA 12 e cuDNN 9 disponíveis. |
| `WHISPER_COMPUTE_TYPE` | `float16` | Tipo de cálculo do Whisper; use `float16` em GPU e `int8` em CPU. |
| `OLLAMA_URL` | `http://localhost:11434` | Endereço do servidor Ollama. |
| `OLLAMA_MODEL` | `translategemma:4b` | Nome/tag do modelo instalado no Ollama. |

## Endpoints

### `GET /health`

Verifica se a API está ativa.

Resposta `200`:

```json
{"status":"ok"}
```

### `POST /api/documents/translate`

Recebe um arquivo `.txt` ou `.pdf` pelo campo multipart `file` e retorna a tradução em JSON. O TXT precisa estar codificado em UTF-8. PDFs precisam conter texto selecionável; arquivos escaneados devem passar por OCR antes de serem enviados. O PDF de entrada é convertido para texto e a resposta não tenta reproduzir a formatação ou as imagens do documento original.

Campos multipart opcionais:

| Campo | Padrão | Descrição |
| --- | --- | --- |
| `target_language` | `Portuguese` | Idioma de destino, por exemplo `English`, `Spanish` ou `Japanese`. |
| `source_language` | `auto` | Idioma de origem, detectado pelo modelo por padrão. Também pode ser informado, como `English`. |

Exemplos:

```powershell
curl.exe -X POST -F "file=@documento.txt" -F "target_language=Portuguese" http://localhost:5000/api/documents/translate
curl.exe -X POST -F "file=@relatorio.pdf" -F "source_language=English" -F "target_language=Portuguese" http://localhost:5000/api/documents/translate
```

Resposta `200`:

```json
{
  "filename": "relatorio.pdf",
  "source_format": "pdf",
  "source_language": "English",
  "target_language": "Portuguese",
  "translated_text": "Texto traduzido..."
}
```

O texto longo é dividido em blocos para tradução, mantendo os parágrafos. Os limites de arquivo, páginas, caracteres extraídos e tamanho aproximado dos blocos são configuráveis pelas variáveis `MAX_DOCUMENT_SIZE_MB`, `MAX_DOCUMENT_PAGES`, `MAX_DOCUMENT_CHARACTERS` e `TRANSLATION_CHUNK_CHARACTERS`. Erros de entrada retornam `400`, limites excedidos retornam `413`, e falhas do Ollama retornam `502`.

### `POST /api/audio/extract`

Extrai a primeira faixa de áudio do vídeo e responde com um MP3 (192 kbit/s) para download. Envie um vídeo no campo multipart `video` ou uma URL do YouTube no campo `url`. Para URLs, aceite `application/json` com `{"url":"https://www.youtube.com/watch?v=VIDEO_ID"}` ou um formulário multipart.

Exemplos:

```powershell
curl.exe -X POST -F "video=@aula.mp4" http://localhost:5000/api/audio/extract --output aula.mp3
curl.exe -X POST -H "Content-Type: application/json" -d '{"url":"https://www.youtube.com/watch?v=VIDEO_ID"}' http://localhost:5000/api/audio/extract --output audio.mp3
```

Formatos de upload aceitos: MP4, MOV, MKV, AVI, WebM, MPEG e MPG. O limite é controlado por `MAX_VIDEO_SIZE_MB`. A resposta é `audio/mpeg`; entradas inválidas retornam `400`, e falhas no download ou no FFmpeg retornam `502`. O vídeo e o áudio temporários são removidos quando o download da resposta termina.

### `POST /api/subtitles`

Recebe um arquivo multipart no campo `video` **ou** uma URL HTTP(S) no campo `url`. Envie apenas uma das opções.

Upload de arquivo:

```powershell
curl.exe -X POST -F "video=@aula_ingles.mp4" http://localhost:5000/api/subtitles
```

Download a partir de URL:

```powershell
curl.exe -X POST -F "url=https://exemplo.com/aula.mp4" http://localhost:5000/api/subtitles
```

Formatos aceitos no upload: MP4, MOV, MKV, AVI, WebM, MPEG e MPG. A URL deve apontar para um arquivo de vídeo acessível por HTTP(S).

Resposta `201`:

```json
{
  "video_path": "C:/projeto/videos/aula.mp4/aula.mp4",
  "subtitle_path": "C:/projeto/videos/aula.mp4/aula.vtt",
  "audio_path": "C:/projeto/videos/aula.mp4/aula.wav",
  "video_url": "http://localhost:5000/api/videos/aula.mp4/aula.mp4",
  "subtitle_url": "http://localhost:5000/api/subtitles/aula.mp4/aula.vtt"
}
```

`video_path` e `subtitle_path` são caminhos no sistema de arquivos do servidor. O frontend deve usar as URLs para carregar os arquivos e conservar os caminhos locais para solicitar o MP4 com a legenda incorporada.

Possíveis erros: `400` para entrada ou formato inválido; `422` quando nenhuma fala é detectada; `502` para falhas no FFmpeg ou Ollama; `500` para erro interno.

### `GET /api/videos/<pasta>/<arquivo>`

Serve o vídeo original processado. A URL inclui a pasta identificada pelo nome do arquivo e é retornada em `video_url`.

### `GET /api/subtitles/<pasta>/<arquivo>`

Serve o arquivo WebVTT salvo junto do vídeo. A URL é retornada em `subtitle_url`.

Exemplo para exibir o vídeo original com legenda selecionável no navegador:

```html
<video controls crossorigin="anonymous">
  <source src="VIDEO_URL" type="video/mp4">
  <track
    src="SUBTITLE_URL"
    kind="subtitles"
    srclang="pt-BR"
    label="Português"
    default
  >
</video>
```

Substitua `VIDEO_URL` e `SUBTITLE_URL` pelas URLs do JSON. As rotas de vídeo e legenda incluem cabeçalho CORS para permitir o carregamento por um frontend em outra origem.

### `POST /api/videos/with-subtitles`

Recebe JSON com os caminhos locais retornados por `POST /api/subtitles` e responde com um MP4 para download. A faixa de legenda é selecionável pelo player; ela não é desenhada permanentemente sobre a imagem.

Corpo da requisição:

```json
{
  "video_path": "C:/projeto/videos/aula.mp4/aula.mp4",
  "subtitle_path": "C:/projeto/videos/aula.mp4/aula.vtt"
}
```

Exemplo de integração no frontend:

```javascript
const result = await fetch("http://localhost:5000/api/subtitles", {
  method: "POST",
  body: formData, // video no campo "video" ou URL no campo "url"
});
const job = await result.json();

const downloadResponse = await fetch("http://localhost:5000/api/videos/with-subtitles", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    video_path: job.video_path,
    subtitle_path: job.subtitle_path,
  }),
});

if (!downloadResponse.ok) {
  throw new Error("Não foi possível gerar o vídeo com legenda.");
}

const blob = await downloadResponse.blob();
const objectUrl = URL.createObjectURL(blob);
const link = document.createElement("a");
link.href = objectUrl;
link.download = "video_pt.mp4";
link.click();
URL.revokeObjectURL(objectUrl);
```

O endpoint aceita somente arquivos existentes na pasta do vídeo dentro de `videos/`. O MP4 gerado fica salvo ao lado do original e da legenda após o envio da resposta.

## Organização do projeto

```text
app/
  __init__.py              # fábrica da aplicação Flask
  config.py                # configurações por variáveis de ambiente
  routes.py                # endpoints HTTP de vídeo e áudio
  document_routes.py       # endpoint de tradução de documentos
  services/
    media.py               # extração do áudio com FFmpeg
    transcription.py       # transcrição com faster-whisper
    translation.py         # tradução com TranslateGemma pelo cliente Ollama
    documents.py           # leitura e validação de TXT e PDF
    document_translation.py # tradução de documentos em blocos
    subtitles.py           # formatação e gravação WebVTT
    video.py               # incorporação da faixa de legenda no MP4
main.py                    # inicialização do servidor
```

Cada processamento mantém os arquivos em `videos/<nome-do-arquivo>/`: o vídeo, o áudio WAV extraído, a transcrição traduzida em WebVTT e, quando solicitado, o MP4 com legenda. Em URLs, a pasta usa o nome do arquivo extraído do caminho. Planeje uma rotina de limpeza dessa pasta em instalações de longa duração. Para produção, use um servidor WSGI e configure os limites de tamanho e timeout do proxy de acordo com a duração dos vídeos.
