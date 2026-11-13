# TVP — Transcritor de Vídeo para Português

Frontend em React, TypeScript, Vite e shadcn/ui para enviar um vídeo à API Flask, assistir ao vídeo com legendas em português e baixar a versão com a faixa de legenda incluída.

## Executar localmente

Inicie primeiro o backend conforme as instruções em [`../backend/README.md`](../backend/README.md). A API deve estar disponível em `http://localhost:5000`.

```bash
npm install
npm run dev
```

O Vite encaminha as chamadas `/api` e `/health` ao backend local. Para usar outro endereço, defina `VITE_API_URL` no ambiente do Vite, por exemplo `http://localhost:5000`.

## Estrutura

- `src/features/transcription/`: contrato e chamadas da API de transcrição e download.
- `src/components/`: identidade TVP, envio de vídeo e visualização/download do resultado.
- `src/components/ui/`: componentes shadcn/ui.
