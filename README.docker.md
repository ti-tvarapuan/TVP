# Executar TVP com Docker Compose

Requisitos: Docker Engine/Desktop com o plugin `docker compose` ativo, GPU NVIDIA e suporte NVIDIA habilitado no Docker (NVIDIA Container Toolkit no Linux ou GPU passthrough configurado no Docker Desktop/WSL2). O Compose inicia o backend Flask com faster-whisper em CUDA, o frontend servido pelo Nginx e o Ollama.

Na raiz do projeto:

```bash
docker compose up --build -d
docker compose exec ollama ollama pull translategemma:4b
```

O download do modelo é feito uma vez e fica no volume persistente `ollama_data`. Abra `http://localhost:8080`. Para acompanhar os serviços: `docker compose logs -f`.

Os vídeos recebidos, áudios WAV, legendas WebVTT e arquivos gerados ficam temporariamente em RAM (`tmpfs`, até 4 GB) e desaparecem quando o container reinicia. O cache dos pesos do Whisper persiste em um volume Docker.

Para encerrar os containers mantendo os dados: `docker compose down`. Para remover também os volumes persistentes: `docker compose down -v`.

A porta publicada do frontend pode ser alterada com `FRONTEND_PORT` (padrão `8080`). O modelo Ollama pode ser alterado com `OLLAMA_MODEL`; ajuste o comando `ollama pull` para o mesmo modelo. Whisper usa `WHISPER_MODEL=large-v3-turbo`, `WHISPER_DEVICE=cuda` e `WHISPER_COMPUTE_TYPE=float16` por padrão. Para uma máquina sem GPU NVIDIA, defina `WHISPER_DEVICE=cpu` e `WHISPER_COMPUTE_TYPE=int8` em `.env` e remova `gpus: all` do serviço `backend` em `docker-compose.yml`.

O primeiro uso pode demorar enquanto o Whisper baixa seus pesos. A requisição de transcrição é síncrona, então o proxy mantém um timeout longo para vídeos extensos.


