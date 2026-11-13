# Executar TVP com Docker Compose

Requisitos: Docker Engine/Desktop com o plugin `docker compose` ativo. O Compose inicia o backend Flask, o frontend servido pelo Nginx e o Ollama.

Na raiz do projeto:

```bash
docker compose up --build -d
docker compose exec ollama ollama pull translategemma:4b
```

O download do modelo é feito uma vez e fica no volume persistente `ollama_data`. Abra `http://localhost:8080`. Para acompanhar os serviços: `docker compose logs -f`.

Os vídeos recebidos, áudio WAV, legendas WebVTT e vídeos legendados ficam em `./videos` no host, montados em `/app/videos` no container do backend. O cache do Whisper também persiste em um volume Docker.

Para encerrar os containers mantendo os dados: `docker compose down`. Para remover também os volumes persistentes: `docker compose down -v`.

A porta publicada do frontend pode ser alterada com `FRONTEND_PORT` (padrão `8080`). O modelo Ollama pode ser alterado com `OLLAMA_MODEL`; ajuste o comando `ollama pull` para o mesmo modelo. `WHISPER_MODEL`, `WHISPER_DEVICE`, `WHISPER_COMPUTE_TYPE` e `MAX_VIDEO_SIZE_MB` também podem ser definidos no ambiente antes de subir o Compose.

O primeiro uso pode demorar enquanto o Whisper baixa seus pesos. A requisição de transcrição é síncrona, então o proxy mantém um timeout longo para vídeos extensos.
