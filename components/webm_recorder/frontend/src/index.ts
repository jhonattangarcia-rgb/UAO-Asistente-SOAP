const startBtn = document.createElement("button");
const stopBtn = document.createElement("button");

const sendToStreamlit = (message: object) => {
  window.parent.postMessage({ isStreamlitMessage: true, ...message }, "*");
};

const setComponentReady = () => {
  sendToStreamlit({ type: "streamlit:componentReady", apiVersion: 1 });
};

const setComponentValue = (value: unknown) => {
  sendToStreamlit({ type: "streamlit:setComponentValue", value, dataType: "json" });
};

const setFrameHeight = (height: number) => {
  sendToStreamlit({ type: "streamlit:setFrameHeight", height });
};

const startHandshake = () => {
  setComponentReady();
  setTimeout(setComponentReady, 100);
  setTimeout(setComponentReady, 300);
  setTimeout(setComponentReady, 800);
};

const onMessage = (event: MessageEvent) => {
  if (!event.data || event.data.type !== "streamlit:render") {
    return;
  }
  ensureFrameHeight();
  setTimeout(ensureFrameHeight, 250);
  setComponentValue(null);
};

window.addEventListener("message", onMessage, false);
const status = document.createElement("div");
const container = document.createElement("div");

startBtn.textContent = "Start";
stopBtn.textContent = "Stop";
stopBtn.disabled = true;
status.textContent = "Listo para grabar";

container.style.fontFamily = "sans-serif";
container.style.padding = "12px";
startBtn.style.marginRight = "8px";
startBtn.style.padding = "8px 14px";
stopBtn.style.padding = "8px 14px";
startBtn.style.cursor = "pointer";
stopBtn.style.cursor = "pointer";
startBtn.style.background = "#111827";
stopBtn.style.background = "#111827";
startBtn.style.color = "#f8fafc";
stopBtn.style.color = "#f8fafc";
startBtn.style.border = "1px solid #374151";
stopBtn.style.border = "1px solid #374151";
startBtn.style.borderRadius = "6px";
stopBtn.style.borderRadius = "6px";
startBtn.style.fontSize = "14px";
stopBtn.style.fontSize = "14px";
status.style.marginTop = "10px";
status.style.color = "#d1d5db";

container.appendChild(startBtn);
container.appendChild(stopBtn);
container.appendChild(status);

document.body.style.margin = "0";
document.body.style.backgroundColor = "#0e1117";
document.body.style.color = "#fff";
document.body.appendChild(container);

type RecorderState = {
  mediaRecorder: MediaRecorder | null;
  audioChunks: Blob[];
};

const state: RecorderState = {
  mediaRecorder: null,
  audioChunks: [],
};

const setStatus = (message: string) => {
  status.textContent = message;
};

const ensureFrameHeight = () => {
  const height = Math.max(
    document.body.scrollHeight,
    document.documentElement.scrollHeight,
    320,
  );
  setFrameHeight(height);
};

async function initRecorder() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    state.mediaRecorder = new MediaRecorder(stream);

    state.mediaRecorder.ondataavailable = (event: BlobEvent) => {
      if (event.data && event.data.size > 0) {
        state.audioChunks.push(event.data);
      }
    };

    state.mediaRecorder.onstop = () => {
      const blob = new Blob(state.audioChunks, { type: "audio/webm" });
      state.audioChunks = [];
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result as string;
        const base64data = result.split(",")[1];
        setComponentValue(base64data);
        setStatus("Grabación lista para transcribir");
      };
      reader.readAsDataURL(blob);
    };

    setStatus("Listo para grabar");
  } catch (error) {
    setStatus(`Error al acceder al micrófono: ${error}`);
    console.error(error);
  }
};

startBtn.addEventListener("click", () => {
  if (!state.mediaRecorder) {
    return;
  }
  state.audioChunks = [];
  state.mediaRecorder.start();
  setStatus("Grabando...");
  startBtn.disabled = true;
  stopBtn.disabled = false;
  ensureFrameHeight();
});

stopBtn.addEventListener("click", () => {
  if (!state.mediaRecorder || state.mediaRecorder.state !== "recording") {
    return;
  }
  state.mediaRecorder.stop();
  stopBtn.disabled = true;
  startBtn.disabled = false;
  ensureFrameHeight();
});

const onRender = () => {
  ensureFrameHeight();
  setTimeout(ensureFrameHeight, 250);
  setComponentValue(null);
};

window.addEventListener("load", () => {
  startHandshake();
  ensureFrameHeight();
  setTimeout(ensureFrameHeight, 250);
  initRecorder();
});
