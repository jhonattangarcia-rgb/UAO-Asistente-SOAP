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

const container = document.createElement("div");
const toggleBtn = document.createElement("button");
const status = document.createElement("span");

container.style.display = "flex";
container.style.alignItems = "center";
container.style.gap = "12px";
container.style.fontFamily = "'Source Sans Pro', sans-serif";
container.style.padding = "8px 4px";
container.style.boxSizing = "border-box";

toggleBtn.style.display = "inline-flex";
toggleBtn.style.alignItems = "center";
toggleBtn.style.gap = "8px";
toggleBtn.style.padding = "8px 18px";
toggleBtn.style.fontSize = "14px";
toggleBtn.style.fontWeight = "600";
toggleBtn.style.color = "#ffffff";
toggleBtn.style.background = "#2f6fed";
toggleBtn.style.border = "none";
toggleBtn.style.borderRadius = "999px";
toggleBtn.style.cursor = "pointer";
toggleBtn.style.transition = "background-color 0.2s ease";

status.style.fontSize = "13px";
status.style.color = "#5b6472";

document.body.style.margin = "0";
document.body.style.backgroundColor = "transparent";
document.body.style.color = "#31333f";

container.appendChild(toggleBtn);
container.appendChild(status);
document.body.appendChild(container);

type RecorderState = {
  mediaRecorder: MediaRecorder | null;
  audioChunks: Blob[];
  isRecording: boolean;
};

const state: RecorderState = {
  mediaRecorder: null,
  audioChunks: [],
  isRecording: false,
};

const setStatus = (message: string) => {
  status.textContent = message;
};

const setIdleAppearance = () => {
  toggleBtn.textContent = "🎙️ Grabar audio";
  toggleBtn.style.background = "#2f6fed";
};

const setRecordingAppearance = () => {
  toggleBtn.textContent = "⏹️ Detener grabación";
  toggleBtn.style.background = "#c0292c";
};

const ensureFrameHeight = () => {
  const height = Math.max(
    document.body.scrollHeight,
    document.documentElement.scrollHeight,
    56,
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
    toggleBtn.disabled = false;
  } catch (error) {
    setStatus(`Error al acceder al micrófono: ${error}`);
    toggleBtn.disabled = true;
    console.error(error);
  }
}

setIdleAppearance();
toggleBtn.disabled = true;

toggleBtn.addEventListener("click", () => {
  if (!state.mediaRecorder) {
    return;
  }
  if (!state.isRecording) {
    state.audioChunks = [];
    state.mediaRecorder.start();
    state.isRecording = true;
    setRecordingAppearance();
    setStatus("Grabando...");
  } else {
    state.mediaRecorder.stop();
    state.isRecording = false;
    setIdleAppearance();
  }
  ensureFrameHeight();
});

window.addEventListener("load", () => {
  startHandshake();
  ensureFrameHeight();
  setTimeout(ensureFrameHeight, 250);
  initRecorder();
});
