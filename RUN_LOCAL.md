# Run it on localhost

## Easiest: one command

```bash
cd "/Users/anantjindal/Desktop/Webvision RTI"
./start.sh
```

Then open **http://localhost:5173**. Press `Ctrl+C` in that terminal to stop both servers.
The first run installs everything and creates `backend/.env` from the example.

## Or start the two servers yourself (two terminals)

Terminal 1, the API (port 8001):

```bash
cd "/Users/anantjindal/Desktop/Webvision RTI/backend"
source .venv/bin/activate
uvicorn app.main:app --port 8001
```

Terminal 2, the web app (port 5173):

```bash
cd "/Users/anantjindal/Desktop/Webvision RTI/frontend"
npm run dev
```

## Check that it works

- API: http://localhost:8001/health should show `{"llm":true,"stt":true,"tts":true}` once your NVIDIA keys are in `backend/.env`. `false` means that service has no key.
- Web: http://localhost:5173

## Tests

```bash
./start.sh --test
```

## If something goes wrong

- **"Internal Server Error" on the page:** the web app is running but the API is not. Start the API (terminal 1 above, or `./start.sh`) and refresh. Check http://localhost:8001/health.
- **"Port ... is already in use":** an old server is still running. Find it with `lsof -iTCP:8001 -sTCP:LISTEN` (or 5173), then `kill <PID>`.
- **Voice or help does nothing:** open `backend/.env` and check the five `NVIDIA_KEY_...` lines are filled. Restart the API after editing.
- **Page loads but data fails:** the web app talks to the API on port 8001. Make sure the API terminal is running.
- **Blank or old page:** hard refresh with `Cmd+Shift+R`.

## Before a demo

1. Start with `./start.sh` a few minutes early and open the site once.
2. Check http://localhost:8001/health shows all `true`.
3. Try the mic once in Chrome and allow microphone access.
4. Keep the internet on: voice, translation and help call NVIDIA.
