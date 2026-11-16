# TVP Frontend

Aplicação React, TypeScript e Vite para enviar vídeos locais ou URLs do YouTube ao backend TVP.

## Funcionalidades

- Envio de vídeo por seletor de arquivo ou arrastar e soltar.
- YouTube: baixar o vídeo original ou enviá-lo para legendagem.
- Detecção automática do idioma falado e seleção do idioma das legendas: Portuguese, English, Spanish, French, German, Italian, Japanese, Chinese e Arabic.
- Acompanhamento de progresso por Server-Sent Events (SSE).
- Player customizado com reprodução, busca, volume, legendas e tela cheia. O download fica em uma ação separada.
- Exportação MP4 com legenda queimada na imagem.

## Executar localmente

Requer Node.js e npm. Inicie primeiro o backend conforme [`../backend/README.md`](../backend/README.md), por padrão em `http://localhost:5000`.

```bash
npm install
npm run dev
```

O Vite encaminha `/api` e `/health` ao backend local. Defina `VITE_API_URL` para usar outro endereço.

## Estrutura

- `src/App.tsx`: seleção de origem, idioma e estado do fluxo.
- `src/features/transcription/`: tipos, chamadas e leitura dos eventos SSE.
- `src/components/video-uploader.tsx`: seletor e área de arrastar e soltar.
- `src/components/video-player.tsx` e `video-player.css`: player e controles customizados.
- `src/components/video-result.tsx`: resultado e download do MP4.
- `nginx.conf`: proxy da API com buffering SSE desativado.
