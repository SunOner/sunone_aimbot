import { useEffect, useMemo, useRef, useState } from "react";

const TABS = [
  { id: "HELPER", label: "Helper" },
  { id: "CONFIG", label: "Config" },
  { id: "EXPORT", label: "Export" },
  { id: "TRAIN", label: "Train" },
  { id: "TESTS", label: "Tests" }
];

const BAUDRATES = [2400, 4800, 9600, 19200, 31250, 38400, 57600, 74880, 115200];

const EXPORT_DEFAULTS = {
  model_name: "",
  image_size: 640,
  precision: "half",
  data_yaml_path: "logic/game.yaml",
  add_nms: true
};

const TRAIN_DEFAULTS = {
  use_user_pretrained_models: false,
  selected_pretrained_model: "",
  selected_checkpoint: "",
  resume: false,
  data_yaml: "logic/game.yaml",
  epochs: 80,
  img_size: 640,
  use_cache: false,
  augment: true,
  augment_degrees: 5,
  augment_flipud: 0.2,
  train_device: "0",
  batch_mode: "auto",
  batch_ratio: 0.7,
  batch_fixed: 16,
  profile: false,
  disable_wandb: true
};

const TEST_DEFAULTS = {
  input_model: "",
  source_method: "Default",
  topmost: true,
  model_image_size: 640,
  input_device: "0",
  input_delay: 30,
  resize_factor: 80,
  ai_conf: 0.2
};

const CONFIG_VERSION_POLL_INTERVAL_MS = 5000;
const CONFIG_SAVE_DEBOUNCE_MS = 350;
const TOAST_LIMIT = 4;
const TOAST_DURATION_MS = 4500;
const ERROR_TOAST_DURATION_MS = 9000;
const DETECTION_SIZE_PRESETS = [640, 320, 160];
const STREAM_STATUS_PREFIX = "__SUNONE_HELPER_STREAM_STATUS__";
const HELPER_TOKEN_COOKIE = "sunone_helper_token";
const HELPER_TOKEN_HEADER = "X-Sunone-Helper-Token";

const CONSOLE_BACKGROUND_LINES = [
  "sunone@helper:~$ boot --quiet --profile dark",
  "[watch] config.ini version poll interval=5000ms",
  "[capture] standby fps_cap=60",
  "[models] scan ./models/*.pt ./models/*.onnx ./models/*.engine",
  "[overlay] dark console backdrop enabled",
  "0x19AF link=ok packets=024 latency=low",
  "01001110 00110001 01110010 01100101",
  "sys.trace helper_ui idle render pipeline",
  "route /api/system/meta -> cached status",
  "telemetry cpu=low gpu=idle redraw=css-only",
  "kernel matrix-rain alpha=0.08",
  "watchdog no-canvas no-timers no-audio",
  "sunone@helper:~$ tail -f runtime.log",
  "status ready"
];

const CONSOLE_BACKGROUND_TEXT = Array.from({ length: 8 }, () => CONSOLE_BACKGROUND_LINES.join("\n")).join("\n");

function toOptions(values) {
  return values.map((item) => (typeof item === "string" ? { value: item, label: item } : item));
}

function ConsoleBackdrop() {
  return (
    <div className="console-backdrop" aria-hidden="true">
      <pre className="console-stream">{CONSOLE_BACKGROUND_TEXT}</pre>
    </div>
  );
}

function isMissingVersion(value) {
  const normalized = String(value ?? "").trim().toLowerCase();
  return !normalized || normalized === "0" || normalized === "n/a" || normalized === "none" || normalized === "null";
}

function compareVersions(left, right) {
  const leftParts = String(left ?? "").match(/\d+/g)?.map(Number) || [];
  const rightParts = String(right ?? "").match(/\d+/g)?.map(Number) || [];
  const maxLength = Math.max(leftParts.length, rightParts.length);

  for (let index = 0; index < maxLength; index += 1) {
    const leftPart = leftParts[index] || 0;
    const rightPart = rightParts[index] || 0;
    if (leftPart !== rightPart) return leftPart - rightPart;
  }

  return 0;
}

function parseErrorPayload(payload, fallbackMessage) {
  if (!payload) return fallbackMessage;
  if (typeof payload === "string") return payload;
  if (payload.detail) {
    if (typeof payload.detail === "string") return payload.detail;
    if (payload.detail.message) {
      return payload.detail.message;
    }
  }
  if (payload.message) return payload.message;
  return fallbackMessage;
}

function parseOutputPayload(payload) {
  if (!payload || typeof payload === "string") return "";
  if (payload.detail && typeof payload.detail === "object" && payload.detail.output) return payload.detail.output;
  return payload.output || "";
}

function createApiError(payload, fallbackMessage) {
  const error = new Error(parseErrorPayload(payload, fallbackMessage));
  const output = parseOutputPayload(payload);
  if (output) error.output = output;
  return error;
}

function parseStreamOutput(rawOutput) {
  const markerIndex = rawOutput.lastIndexOf(STREAM_STATUS_PREFIX);
  if (markerIndex === -1) {
    return { output: rawOutput, status: null };
  }

  const output = rawOutput.slice(0, markerIndex).trimEnd();
  const statusLine = rawOutput.slice(markerIndex + STREAM_STATUS_PREFIX.length).trim().split(/\r?\n/)[0];
  try {
    return { output, status: JSON.parse(statusLine) };
  } catch {
    return { output, status: null };
  }
}

function getDetectionSizePreset(config) {
  const width = Number(config?.detection_window_width);
  const height = Number(config?.detection_window_height);
  const preset = DETECTION_SIZE_PRESETS.find((size) => width === size && height === size);
  return preset ? String(preset) : "custom";
}

function readCookie(name) {
  const prefix = `${name}=`;
  return document.cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(prefix))
    ?.slice(prefix.length) || "";
}

function withHelperHeaders(options = {}) {
  const method = String(options.method || "GET").toUpperCase();
  if (method === "GET" || method === "HEAD") return options;

  const headers = new Headers(options.headers || {});
  const token = readCookie(HELPER_TOKEN_COOKIE);
  if (token) headers.set(HELPER_TOKEN_HEADER, token);
  return { ...options, headers };
}

function sameConfigVersion(left, right) {
  return Number(left?.mtime_ns || 0) === Number(right?.mtime_ns || 0) && Number(left?.size || 0) === Number(right?.size || 0);
}

async function apiRequest(path, options = {}) {
  const response = await fetch(path, withHelperHeaders(options));
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    throw createApiError(payload, `Request failed: ${response.status}`);
  }
  if (payload && payload.ok === false) {
    throw createApiError(payload, "Request failed");
  }
  return payload;
}

function App() {
  const [activeTab, setActiveTab] = useState("HELPER");
  const [loading, setLoading] = useState(true);
  const [busyKey, setBusyKey] = useState("");
  const [toasts, setToasts] = useState([]);
  const [output, setOutput] = useState("");

  const [meta, setMeta] = useState(null);
  const [status, setStatus] = useState(null);
  const [config, setConfig] = useState(null);
  const [exportForm, setExportForm] = useState(EXPORT_DEFAULTS);
  const [trainForm, setTrainForm] = useState(TRAIN_DEFAULTS);
  const [testForm, setTestForm] = useState(TEST_DEFAULTS);
  const [testVideo, setTestVideo] = useState(null);
  const [activeConfigSection, setActiveConfigSection] = useState("detection");
  const [configSearch, setConfigSearch] = useState("");
  const [detectionSizeMode, setDetectionSizeMode] = useState("auto");
  const configSaveTimers = useRef(new Map());
  const pendingConfigSaves = useRef(new Set());
  const configSaveVersions = useRef(new Map());
  const toastTimers = useRef(new Map());
  const outputRef = useRef(null);
  const busyRef = useRef("");
  const configVersionRef = useRef(null);

  const hotkeyOptions = meta?.hotkey_options || [];
  const modelOptions = meta?.models || [];
  const ptModelOptions = meta?.pt_models || [];
  const checkpointOptions = meta?.last_checkpoints || [];
  const deviceOptions = meta?.device_options || ["cpu", "0"];
  const currentDetectionSizePreset = config && detectionSizeMode !== "custom" ? getDetectionSizePreset(config) : "custom";
  const isBusy = !!busyKey;

  const dismissToast = (id) => {
    const timerId = toastTimers.current.get(id);
    if (timerId) window.clearTimeout(timerId);
    toastTimers.current.delete(id);
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  const showNotice = (type, text) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const toast = { id, type, text };
    setToasts((prev) => [...prev, toast].slice(-TOAST_LIMIT));
    const duration = type === "error" ? ERROR_TOAST_DURATION_MS : TOAST_DURATION_MS;
    const timerId = window.setTimeout(() => dismissToast(id), duration);
    toastTimers.current.set(id, timerId);
  };

  const showError = (error) => {
    if (error?.output) setOutput(error.output);
    showNotice("error", String(error?.message || error));
  };

  const startBusy = (key) => {
    if (busyRef.current) {
      showNotice("error", "Another helper action is already running.");
      return false;
    }
    busyRef.current = key;
    setBusyKey(key);
    return true;
  };

  const finishBusy = (key) => {
    if (busyRef.current === key) {
      busyRef.current = "";
    }
    setBusyKey("");
  };

  const normalizeConfig = (sourceConfig, sourceMeta = meta) => {
    const normalizedConfig = { ...sourceConfig };
    if (sourceMeta?.models?.length && !sourceMeta.models.includes(normalizedConfig.ai_model_name)) {
      normalizedConfig.ai_model_name = sourceMeta.models[0];
    }
    return normalizedConfig;
  };

  const mergeRemoteConfig = (remoteConfig) => {
    setConfig((prev) => {
      if (!prev) return remoteConfig;
      const next = { ...prev };
      Object.entries(remoteConfig).forEach(([key, value]) => {
        if (!pendingConfigSaves.current.has(key)) {
          next[key] = value;
        }
      });
      return next;
    });
  };

  const refreshStatusOnly = async (force = false) => {
    const refreshed = await apiRequest(`/api/system/meta${force ? "?force=1" : ""}`);
    setMeta(refreshed);
    setStatus(refreshed.status);
  };

  const refreshConfigOnly = async (silent = true) => {
    try {
      const configRes = await apiRequest("/api/config");
      configVersionRef.current = configRes.version || null;
      mergeRemoteConfig(normalizeConfig(configRes.config));
    } catch (error) {
      if (!silent) showError(error);
    }
  };

  const refreshConfigIfChanged = async (silent = true) => {
    try {
      const versionRes = await apiRequest("/api/config/version");
      if (sameConfigVersion(configVersionRef.current, versionRes.version)) return;
      await refreshConfigOnly(silent);
    } catch (error) {
      if (!silent) showError(error);
    }
  };

  const loadInitial = async () => {
    setLoading(true);
    try {
      const [metaRes, configRes] = await Promise.all([apiRequest("/api/system/meta?force=1"), apiRequest("/api/config")]);
      const normalizedConfig = normalizeConfig(configRes.config, metaRes);
      configVersionRef.current = configRes.version || null;
      setMeta(metaRes);
      setStatus(metaRes.status);
      setConfig(normalizedConfig);
      setDetectionSizeMode("auto");

      setExportForm((prev) => ({
        ...prev,
        model_name: metaRes.pt_models?.includes(prev.model_name) ? prev.model_name : metaRes.pt_models?.[0] || ""
      }));
      setTrainForm((prev) => ({
        ...prev,
        selected_pretrained_model: metaRes.pretrained_models?.includes(prev.selected_pretrained_model)
          ? prev.selected_pretrained_model
          : metaRes.pretrained_models?.[0] || "",
        selected_checkpoint: prev.selected_checkpoint || metaRes.last_checkpoints?.[0] || "",
        train_device: metaRes.device_options?.includes(prev.train_device)
          ? prev.train_device
          : metaRes.device_options?.[1] || "0"
      }));
      setTestForm((prev) => ({
        ...prev,
        input_model: metaRes.models?.includes(prev.input_model) ? prev.input_model : metaRes.models?.[0] || "",
        input_device: metaRes.device_options?.includes(prev.input_device)
          ? prev.input_device
          : metaRes.device_options?.[1] || "0"
      }));
    } catch (error) {
      showError(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitial();
  }, []);

  useEffect(() => {
    return () => {
      configSaveTimers.current.forEach((timerId) => window.clearTimeout(timerId));
      configSaveTimers.current.clear();
      toastTimers.current.forEach((timerId) => window.clearTimeout(timerId));
      toastTimers.current.clear();
    };
  }, []);

  useEffect(() => {
    if (!meta) return undefined;
    const intervalId = window.setInterval(() => {
      if (!document.hidden) refreshConfigIfChanged(true);
    }, CONFIG_VERSION_POLL_INTERVAL_MS);
    return () => window.clearInterval(intervalId);
  }, [meta]);

  useEffect(() => {
    if (!outputRef.current) return;
    outputRef.current.scrollTop = outputRef.current.scrollHeight;
  }, [output]);

  const runAction = async (key, endpoint, confirmText = "") => {
    if (confirmText && !window.confirm(confirmText)) return;
    if (!startBusy(key)) return;
    setOutput("");
    try {
      const payload = await apiRequest(endpoint, { method: "POST" });
      if (payload.output) setOutput(payload.output);
      showNotice("success", payload.message || "Action completed.");
      if (endpoint !== "/api/actions/run-aimbot") await refreshStatusOnly(true);
    } catch (error) {
      showError(error);
    } finally {
      finishBusy(key);
    }
  };

  const runStreamingAction = async (key, endpoint, label, requestOptions = {}) => {
    if (!startBusy(key)) return;
    let fullOutput = `Starting ${label}...\n`;
    setOutput(fullOutput);

    try {
      const response = await fetch(endpoint, withHelperHeaders({ method: "POST", ...requestOptions }));
      if (!response.ok) {
        let payload = null;
        try {
          payload = await response.json();
        } catch {
          payload = null;
        }
        throw createApiError(payload, `${label} failed.`);
      }

      if (response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          fullOutput += decoder.decode(value, { stream: true });
          setOutput(parseStreamOutput(fullOutput).output);
        }
        fullOutput += decoder.decode();
      } else {
        fullOutput += await response.text();
      }

      const parsed = parseStreamOutput(fullOutput);
      setOutput(parsed.output);

      if (!parsed.status) {
        throw new Error(`${label} finished without status.`);
      }
      if (parsed.status.ok === false) {
        const error = new Error(parsed.status.message || `${label} failed.`);
        error.output = parsed.output;
        throw error;
      }

      showNotice("success", parsed.status.message || `${label} completed.`);
      await refreshStatusOnly(true);
    } catch (error) {
      if (fullOutput && !error?.output) {
        const outputError = error instanceof Error ? error : new Error(String(error));
        outputError.output = `${fullOutput.trimEnd()}\n${outputError.message}`;
        showError(outputError);
      } else {
        showError(error);
      }
    } finally {
      finishBusy(key);
    }
  };

  const persistConfigField = async (key, value) => {
    const saveVersion = (configSaveVersions.current.get(key) || 0) + 1;
    configSaveVersions.current.set(key, saveVersion);
    pendingConfigSaves.current.add(key);
    try {
      const payload = await apiRequest("/api/config", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key, value })
      });
      if (configSaveVersions.current.get(key) !== saveVersion) return;
      pendingConfigSaves.current.delete(key);
      configVersionRef.current = payload.version || configVersionRef.current;
      if (payload.config) {
        mergeRemoteConfig(normalizeConfig(payload.config));
      }
    } catch (error) {
      if (configSaveVersions.current.get(key) === saveVersion) {
        showError(error);
      }
    } finally {
      if (configSaveVersions.current.get(key) === saveVersion) {
        pendingConfigSaves.current.delete(key);
      }
    }
  };

  const scheduleConfigSave = (key, value, type = "text") => {
    pendingConfigSaves.current.add(key);
    const currentTimer = configSaveTimers.current.get(key);
    if (currentTimer) window.clearTimeout(currentTimer);

    const delay = type === "number" || type === "text" ? CONFIG_SAVE_DEBOUNCE_MS : 0;
    if (delay === 0) {
      configSaveTimers.current.delete(key);
      persistConfigField(key, value);
      return;
    }

    const timerId = window.setTimeout(() => {
      configSaveTimers.current.delete(key);
      persistConfigField(key, value);
    }, delay);
    configSaveTimers.current.set(key, timerId);
  };

  const exportModel = async () => {
    if (!exportForm.model_name) {
      showNotice("error", "Select model before export.");
      return;
    }
    await runStreamingAction("export", "/api/export/stream", "Model export", {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(exportForm)
    });
  };
  const startTrain = async () => {
    const selectedModel = trainForm.use_user_pretrained_models
      ? trainForm.selected_checkpoint
      : trainForm.selected_pretrained_model;
    if (!selectedModel) {
      showNotice("error", "Select model before training.");
      return;
    }

    let batchSize = -1;
    if (trainForm.batch_mode === "ratio") batchSize = Number(trainForm.batch_ratio);
    if (trainForm.batch_mode === "fixed") batchSize = Number(trainForm.batch_fixed);

    const payload = {
      selected_model_path: selectedModel,
      resume: trainForm.resume,
      data_yaml: trainForm.data_yaml,
      epochs: Number(trainForm.epochs),
      img_size: Number(trainForm.img_size),
      use_cache: !!trainForm.use_cache,
      augment: !!trainForm.augment,
      augment_degrees: Number(trainForm.augment_degrees),
      augment_flipud: Number(trainForm.augment_flipud),
      train_device: trainForm.train_device,
      batch_size: batchSize,
      profile: !!trainForm.profile,
      disable_wandb: !!trainForm.disable_wandb
    };

    await runStreamingAction("train", "/api/train/stream", "Training", {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  };

  const runTests = async () => {
    if (testForm.source_method === "Input file" && !testVideo) {
      showNotice("error", "Select a video file.");
      return;
    }
    const formData = new FormData();
    Object.entries(testForm).forEach(([key, value]) => formData.append(key, String(value)));
    if (testVideo) formData.append("video_file", testVideo);

    await runStreamingAction("tests", "/api/tests/run/stream", "Detection test", {
      body: formData
    });
  };

  const sections = useMemo(() => {
    if (!config) return [];
    const aiModelField = modelOptions.length
      ? { key: "ai_model_name", label: "AI model", type: "select", options: modelOptions, help: "Detector model used at runtime." }
      : { key: "ai_model_name", label: "AI model", type: "text", help: "Detector model used at runtime." };

    return [
      {
        id: "detection",
        title: "Detection Area",
        description: "Control the captured region around your crosshair.",
        fields: [
          {
            key: "detection_size_preset",
            label: "Size preset",
            type: "detection_preset",
            options: [
              ...DETECTION_SIZE_PRESETS.map((size) => ({ value: String(size), label: `${size} x ${size}` })),
              { value: "custom", label: "Custom" }
            ],
            help: "Preset applies the same width and height. Use Custom for manual values."
          },
          { key: "detection_window_width", label: "Width", type: "number", min: 64, step: 1, visible: currentDetectionSizePreset === "custom", help: "Capture width in pixels." },
          { key: "detection_window_height", label: "Height", type: "number", min: 64, step: 1, visible: currentDetectionSizePreset === "custom", help: "Capture height in pixels." },
          { key: "circle_capture", label: "Circle capture", type: "bool", advanced: true, help: "Use circular clipping for capture." }
        ]
      },
      {
        id: "capture",
        title: "Capture Input",
        description: "Choose how frames are read from your screen/device.",
        fields: [
          {
            key: "capture_method",
            label: "Method",
            type: "select",
            options: [
              { value: "bettercam", label: "Bettercam" },
              { value: "obs", label: "OBS" },
              { value: "mss", label: "MSS" }
            ],
            help: "MSS is usually the safest default."
          },
          { key: "capture_fps", label: "Capture FPS", type: "number", min: 1, max: 240, step: 1, help: "Higher FPS reduces latency but costs CPU/GPU." },
          { key: "bettercam_monitor_id", label: "Bettercam monitor ID", type: "number", step: 1, advanced: true, visible: config.capture_method === "bettercam" },
          { key: "bettercam_gpu_id", label: "Bettercam GPU ID", type: "number", step: 1, advanced: true, visible: config.capture_method === "bettercam" },
          { key: "obs_camera_id", label: "OBS camera ID", type: "select", options: meta?.obs_camera_options || ["auto"], advanced: true, visible: config.capture_method === "obs" }
        ]
      },
      {
        id: "aim",
        title: "Aim & Hotkeys",
        description: "Core aiming behavior and keyboard/mouse bindings.",
        fields: [
          { key: "body_y_offset", label: "Body Y offset", type: "number", step: 0.01, min: -0.99, max: 0.99, help: "Vertical target shift. Start with small values." },
          { key: "hotkey_targeting", label: "Targeting keys", type: "multiselect", options: hotkeyOptions, help: "Hold one of these keys to activate targeting." },
          { key: "hotkey_exit", label: "Exit key", type: "select", options: hotkeyOptions },
          { key: "hotkey_pause", label: "Pause key", type: "select", options: hotkeyOptions },
          { key: "disable_prediction", label: "Disable prediction", type: "bool", help: "Turn off motion prediction for targets." },
          { key: "prediction_interval", label: "Prediction interval", type: "number", step: 0.1, min: 0.1, max: 5, advanced: true, visible: !config.disable_prediction },
          { key: "hideout_targets", label: "Hideout targets", type: "bool", advanced: true },
          { key: "disable_headshot", label: "Disable headshot", type: "bool", advanced: true },
          { key: "third_person", label: "Third person mode", type: "bool", advanced: true },
          { key: "hotkey_reload_config", label: "Reload key", type: "select", options: hotkeyOptions, advanced: true }
        ]
      },
      {
        id: "mouse",
        title: "Mouse / Shooting / Arduino",
        description: "Sensitivity, FOV, trigger behavior and optional Arduino control.",
        fields: [
          { key: "mouse_dpi", label: "Mouse DPI", type: "number", step: 100, min: 100, help: "Use your real mouse DPI value." },
          { key: "mouse_sensitivity", label: "Mouse sensitivity", type: "number", step: 0.1, min: 0.1, help: "In-game sensitivity multiplier." },
          { key: "mouse_fov_width", label: "Mouse FOV width", type: "number", step: 1 },
          { key: "mouse_fov_height", label: "Mouse FOV height", type: "number", step: 1 },
          { key: "mouse_lock_target", label: "Mouse lock target", type: "bool" },
          { key: "mouse_auto_aim", label: "Mouse auto aim", type: "bool" },
          { key: "mouse_min_speed_multiplier", label: "Min speed multiplier", type: "number", step: 0.01, advanced: true },
          { key: "mouse_max_speed_multiplier", label: "Max speed multiplier", type: "number", step: 0.01, advanced: true },
          { key: "mouse_ghub", label: "Mouse GHUB", type: "bool", advanced: true },
          { key: "mouse_rzr", label: "Mouse Razer", type: "bool", advanced: true },
          { key: "auto_shoot", label: "Auto shoot", type: "bool", advanced: true },
          { key: "triggerbot", label: "Triggerbot", type: "bool", advanced: true },
          { key: "force_click", label: "Force click", type: "bool", advanced: true },
          { key: "bscope_multiplier", label: "bScope multiplier", type: "number", step: 0.1, advanced: true },
          { key: "arduino_move", label: "Arduino move", type: "bool", advanced: true },
          { key: "arduino_shoot", label: "Arduino shoot", type: "bool", advanced: true },
          { key: "arduino_port", label: "Arduino port", type: "text", advanced: true, visible: config.arduino_move || config.arduino_shoot },
          { key: "arduino_baudrate", label: "Arduino baudrate", type: "select", options: BAUDRATES.map(String), advanced: true, visible: config.arduino_move || config.arduino_shoot },
          { key: "arduino_16_bit_mouse", label: "Arduino 16-bit mouse", type: "bool", advanced: true, visible: config.arduino_move || config.arduino_shoot }
        ]
      },
      {
        id: "ai",
        title: "AI / Overlay / Debug",
        description: "Model, confidence threshold, on-screen overlay and debug window.",
        fields: [
          aiModelField,
          { key: "ai_model_image_size", label: "AI image size", type: "select", options: ["320", "480", "640"], help: "640 is usually the best quality baseline." },
          { key: "ai_conf", label: "AI confidence", type: "number", step: 0.01, min: 0.01, max: 0.99, help: "Lower value detects more, higher value is stricter." },
          { key: "ai_device", label: "AI device", type: "select", options: deviceOptions },
          { key: "show_overlay", label: "Show overlay", type: "bool" },
          { key: "show_window", label: "Show debug window", type: "bool" },
          { key: "ai_enable_amd", label: "AI enable AMD", type: "bool", advanced: true },
          { key: "disable_tracker", label: "Disable tracker", type: "bool", advanced: true },
          { key: "overlay_show_borders", label: "Overlay borders", type: "bool", advanced: true, visible: config.show_overlay },
          { key: "overlay_show_boxes", label: "Overlay boxes", type: "bool", advanced: true, visible: config.show_overlay },
          { key: "overlay_show_target_line", label: "Overlay target line", type: "bool", advanced: true, visible: config.show_overlay },
          { key: "overlay_show_target_prediction_line", label: "Overlay prediction line", type: "bool", advanced: true, visible: config.show_overlay },
          { key: "overlay_show_labels", label: "Overlay labels", type: "bool", advanced: true, visible: config.show_overlay },
          { key: "overlay_show_conf", label: "Overlay confidence", type: "bool", advanced: true, visible: config.show_overlay },
          { key: "show_detection_speed", label: "Show detection speed", type: "bool", advanced: true, visible: config.show_window },
          { key: "show_window_fps", label: "Show window FPS", type: "bool", advanced: true, visible: config.show_window },
          { key: "show_boxes", label: "Show boxes", type: "bool", advanced: true, visible: config.show_window },
          { key: "show_labels", label: "Show labels", type: "bool", advanced: true, visible: config.show_window },
          { key: "show_conf", label: "Show confidence", type: "bool", advanced: true, visible: config.show_window },
          { key: "show_target_line", label: "Show target line", type: "bool", advanced: true, visible: config.show_window },
          { key: "show_target_prediction_line", label: "Show target prediction", type: "bool", advanced: true, visible: config.show_window },
          { key: "show_bscope_box", label: "Show bScope box", type: "bool", advanced: true, visible: config.show_window },
          { key: "show_history_points", label: "Show history points", type: "bool", advanced: true, visible: config.show_window },
          { key: "debug_window_always_on_top", label: "Debug window always on top", type: "bool", advanced: true, visible: config.show_window },
          { key: "spawn_window_pos_x", label: "Spawn X", type: "number", step: 1, advanced: true, visible: config.show_window },
          { key: "spawn_window_pos_y", label: "Spawn Y", type: "number", step: 1, advanced: true, visible: config.show_window },
          { key: "debug_window_scale_percent", label: "Scale percent", type: "number", step: 1, advanced: true, visible: config.show_window },
          { key: "debug_window_screenshot_key", label: "Screenshot key", type: "select", options: hotkeyOptions, advanced: true, visible: config.show_window }
        ]
      }
    ];
  }, [config, currentDetectionSizePreset, deviceOptions, hotkeyOptions, meta, modelOptions]);

  const visibleConfigSections = useMemo(() => {
    const query = configSearch.trim().toLowerCase();
    return sections
      .map((section) => ({
        ...section,
        fields: section.fields.filter((field) => {
          if (field.visible === false) return false;
          if (!query) return true;
          const source = `${field.label} ${field.key} ${field.help || ""}`.toLowerCase();
          return source.includes(query);
        })
      }))
      .filter((section) => section.fields.length > 0);
  }, [configSearch, sections]);

  const selectedConfigSection = useMemo(() => {
    const fallback = visibleConfigSections[0] || null;
    if (!fallback) return null;
    return visibleConfigSections.find((section) => section.id === activeConfigSection) || fallback;
  }, [activeConfigSection, visibleConfigSections]);
  const updateConfig = (key, value, type = "text") => {
    let nextValue = value;
    if (type === "number") nextValue = Number(value);
    if (type === "bool") nextValue = !!value;
    if (key === "detection_window_width" || key === "detection_window_height") {
      setDetectionSizeMode("custom");
    }
    setConfig((prev) => ({ ...prev, [key]: nextValue }));
    scheduleConfigSave(key, nextValue, type);
  };

  const updateDetectionSizePreset = (value) => {
    if (value === "custom") {
      setDetectionSizeMode("custom");
      return;
    }

    const nextSize = Number(value);
    if (!Number.isFinite(nextSize)) return;
    setDetectionSizeMode("auto");
    setConfig((prev) => ({
      ...prev,
      detection_window_width: nextSize,
      detection_window_height: nextSize
    }));
    scheduleConfigSave("detection_window_width", nextSize, "select");
    scheduleConfigSave("detection_window_height", nextSize, "select");
  };

  const renderField = (field) => {
    if (field.visible === false) return null;
    const options = field.options ? toOptions(field.options) : [];
    const value = field.type === "detection_preset" ? currentDetectionSizePreset : config[field.key];
    const label = (
      <span className="field-label">
        <span>{field.label}</span>
        {field.help && (
          <span className="help-tip" tabIndex="0" aria-label={field.help}>
            ?
            <span className="tooltip" role="tooltip">{field.help}</span>
          </span>
        )}
      </span>
    );

    if (field.type === "detection_preset") {
      return (
        <label className="field config-option" key={field.key}>
          {label}
          <select value={value} onChange={(event) => updateDetectionSizePreset(event.target.value)}>
            {options.map((option) => (
              <option value={option.value} key={`${field.key}-${option.value}`}>{option.label}</option>
            ))}
          </select>
        </label>
      );
    }

    if (field.type === "bool") {
      return (
        <label className="field config-option bool-option" key={field.key}>
          <input
            className="toggle-input"
            type="checkbox"
            checked={!!value}
            onChange={(event) => updateConfig(field.key, event.target.checked, "bool")}
          />
          <span className="toggle-switch" aria-hidden="true" />
          <div className="toggle-copy">
            {label}
          </div>
        </label>
      );
    }

    if (field.type === "multiselect") {
      return (
        <label className="field config-option" key={field.key}>
          {label}
          <select
            multiple
            value={Array.isArray(value) ? value : []}
            onChange={(event) => {
              const selected = Array.from(event.target.selectedOptions).map((item) => item.value);
              updateConfig(field.key, selected, "multiselect");
            }}
          >
            {options.map((option) => (
              <option value={option.value} key={`${field.key}-${option.value}`}>{option.label}</option>
            ))}
          </select>
        </label>
      );
    }

    if (field.type === "select") {
      return (
        <label className="field config-option" key={field.key}>
          {label}
          <select value={String(value ?? "")} onChange={(event) => updateConfig(field.key, event.target.value, "select")}>
            {options.map((option) => (
              <option value={option.value} key={`${field.key}-${option.value}`}>{option.label}</option>
            ))}
          </select>
        </label>
      );
    }

    return (
      <label className="field config-option" key={field.key}>
        {label}
        <input
          type={field.type === "number" ? "number" : "text"}
          value={value ?? ""}
          min={field.min}
          max={field.max}
          step={field.step}
          onChange={(event) => updateConfig(field.key, event.target.value, field.type)}
        />
      </label>
    );
  };

  const statusCards = useMemo(() => {
    if (!status) return [];
    const installedAimbotVersion = status.aimbot_versions?.offline?.app_version || "0";
    const githubAimbotVersion = status.aimbot_versions?.online?.app_version || "0";
    const torchGpuSupport = status.torch_gpu_support;
    const torchGpuValue = torchGpuSupport === null || torchGpuSupport === undefined ? "Not installed" : String(torchGpuSupport);
    const torchVersion = status.torch?.version ? ` / ${status.torch.version}` : "";
    const torchCuda = status.torch?.torch_cuda ? ` CUDA ${status.torch.torch_cuda}` : "";

    return [
      { label: "Installed Aimbot", value: installedAimbotVersion },
      { label: "GitHub Aimbot", value: githubAimbotVersion },
      { label: "CUDA 12.8", value: status.cuda?.available ? "Detected" : "Missing" },
      { label: "Torch GPU", value: `${torchGpuValue}${torchVersion}${torchCuda}` },
      { label: "TensorRT", value: status.tensorrt?.available ? status.tensorrt.version : "Not installed" },
      { label: "Python / Ultralytics", value: `${status.python || "N/A"} / ${status.ultralytics || "N/A"}` }
    ];
  }, [status]);

  const helperWarnings = useMemo(() => {
    if (!status || !config) return [];

    const warnings = [];
    const installedAimbotVersion = status.aimbot_versions?.offline?.app_version || "0";
    const githubAimbotVersion = status.aimbot_versions?.online?.app_version || "0";
    const installedAimbotMissing = isMissingVersion(installedAimbotVersion);
    const githubAimbotMissing = isMissingVersion(githubAimbotVersion);
    const selectedMouseMethods = [config.arduino_move, config.mouse_ghub, config.mouse_rzr].filter(Boolean).length;

    if (installedAimbotMissing) {
      warnings.push({ text: "Local version file is missing or unreadable. The helper cannot verify the installed aimbot version." });
    }
    if (githubAimbotMissing) {
      warnings.push({ text: "Could not fetch the current GitHub version. Check your internet connection or GitHub availability." });
    }
    if (!installedAimbotMissing && !githubAimbotMissing && compareVersions(installedAimbotVersion, githubAimbotVersion) < 0) {
      warnings.push({ text: `Installed version ${installedAimbotVersion} is older than GitHub version ${githubAimbotVersion}. Use Update/Reinstall Aimbot.` });
    }
    if (!status.cuda?.available) {
      warnings.push({ text: "CUDA 12.8 was not found in PATH. Install CUDA 12.8 or use Download CUDA 12.8 before GPU features." });
    }
    if (status.torch_gpu_support !== true) {
      const torchDetails = status.torch?.executable
        ? ` Python: ${status.torch.executable}. Torch: ${status.torch.version || "not installed"}, CUDA build: ${status.torch.torch_cuda || "none"}.`
        : "";
      warnings.push({ text: `PyTorch does not see CUDA/GPU. Reinstall Torch with CUDA support and check NVIDIA driver/CUDA installation.${torchDetails}` });
    }
    if (!status.tensorrt?.available) {
      warnings.push({ text: "TensorRT is not installed. TensorRT engine export and accelerated inference will not be available." });
    }
    if (!status.python || !status.ultralytics) {
      warnings.push({ text: "Python or Ultralytics version could not be detected. Check that required Python packages are installed." });
    }

    if (Number(config.capture_fps) >= 120) {
      warnings.push({ text: "A large number of frames per second can affect the behavior of automatic aiming. (Shaking)." });
    }
    if (Number(config.detection_window_width) >= 600) {
      warnings.push({ text: "The object detector window is more than 600 pixels wide, and a large object detector window can have a bad effect on performance." });
    }
    if (Number(config.detection_window_height) >= 600) {
      warnings.push({ text: "The object detector window is more than 600 pixels in height, a large object detector window can have a bad effect on performance." });
    }
    if (String(config.ai_model_name || "").toLowerCase().endsWith(".pt")) {
      warnings.push({
        text: "Export the model to `.engine` for better performance!",
        help: "HOW TO EXPORT TO ENGINE:",
        href: "https://github.com/SunOner/sunone_aimbot_docs/blob/main/ai_models/ai_models.md"
      });
    }
    if (Number(config.ai_conf) <= 0.1) {
      warnings.push({ text: "A small value of `AI_conf` can lead to a large number of false positives." });
    }
    if (!config.mouse_ghub && !config.arduino_move && !config.arduino_shoot) {
      warnings.push({ text: "win32api is detected in some games." });
    }
    if (config.mouse_ghub && !config.arduino_move && !config.arduino_shoot) {
      warnings.push({ text: "ghub is detected in some games." });
    }
    if (!config.arduino_move) {
      warnings.push({ text: "Using standard libraries for mouse moving such as `win32` or `Ghub driver` without bypassing, for example, how Arduino can speed up the account blocking process, use it at your own risk." });
    }
    if (!config.arduino_shoot && config.auto_shoot) {
      warnings.push({ text: "Using standard libraries for mouse shooting such as `win32` or `Ghub driver` without bypassing, for example, how Arduino can speed up the account blocking process, use it at your own risk." });
    }
    if (selectedMouseMethods > 1) {
      warnings.push({ text: "You use more than one mouse input method." });
    }
    if (config.show_window) {
      warnings.push({ text: "An open debug window can affect performance." });
    }

    return warnings;
  }, [config, status]);

  if (loading || !config || !meta || !status) {
    return (
      <div className="loading">
        <ConsoleBackdrop />
        <span>Loading Sunone Helper...</span>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <ConsoleBackdrop />

      {toasts.length > 0 && (
        <div className="toast-stack" aria-live="polite">
          {toasts.map((toast) => (
            <div className={`toast ${toast.type}`} key={toast.id} role={toast.type === "error" ? "alert" : "status"}>
              <span className="toast-marker" aria-hidden="true">{toast.type === "success" ? "OK" : "!"}</span>
              <p>{toast.text}</p>
              <button type="button" className="toast-dismiss" aria-label="Dismiss notification" onClick={() => dismissToast(toast.id)}>
                x
              </button>
            </div>
          ))}
        </div>
      )}

      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">SO</div>
          <div>
            <h1>Sunone Helper</h1>
          </div>
        </div>

        <nav className="tab-nav">
          {TABS.map((tab) => (
            <button key={tab.id} className={activeTab === tab.id ? "tab active" : "tab"} onClick={() => setActiveTab(tab.id)}>
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>

      </aside>

      <main className="workspace">
        {activeTab === "HELPER" && (
          <section className="panel">
            <div className="status-grid">
              {statusCards.map((item) => (
                <article key={item.label} className="status-card">
                  <div className="status-card-header">
                    <span className="status-card-label">{item.label}</span>
                  </div>
                  <strong>{item.value}</strong>
                </article>
              ))}
            </div>
            <div className="button-row">
              <button disabled={isBusy} onClick={() => runAction("run", "/api/actions/run-aimbot")}>Run Aimbot</button>
              <button disabled={isBusy} onClick={() => runAction("app", "/api/actions/reinstall-aimbot", "Reinstall/Update files from GitHub?")}>Update/Reinstall Aimbot</button>
              <button disabled={isBusy} onClick={() => runStreamingAction("torch", "/api/actions/reinstall-torch/stream", "Torch reinstall")}>Reinstall Torch</button>
              <button disabled={isBusy} onClick={() => runStreamingAction("trt", "/api/actions/reinstall-tensorrt/stream", "TensorRT reinstall")}>Reinstall TensorRT</button>
              <button disabled={isBusy} onClick={() => runStreamingAction("cuda", "/api/actions/download-cuda/stream", "CUDA download")}>Download CUDA 12.8</button>
            </div>
            {helperWarnings.length > 0 && (
              <div className="helper-warning-panel" role="status" aria-live="polite">
                {helperWarnings.map((warning, index) => (
                  <p className="helper-warning-line" key={`${warning.text}-${index}`}>
                    <span className="warning-prefix">WARNING:</span>{" "}
                    <span>{warning.text}</span>
                    {warning.href && (
                      <>
                        <br />
                        <span className="warning-prefix">{warning.help}</span>{" "}
                        <a href={warning.href} target="_blank" rel="noreferrer">{warning.href}</a>
                      </>
                    )}
                  </p>
                ))}
              </div>
            )}
          </section>
        )}

        {activeTab === "CONFIG" && (
          <section className="panel config-panel">
            <div className="config-toolbar">
              <label className="field config-search">
                <span>Search setting</span>
                <input
                  type="text"
                  placeholder="e.g. overlay, dpi, hotkey"
                  value={configSearch}
                  onChange={(event) => setConfigSearch(event.target.value)}
                />
              </label>
            </div>

            <nav className="config-section-nav">
              {visibleConfigSections.map((section) => (
                <button
                  key={section.id}
                  className={selectedConfigSection?.id === section.id ? "section-pill active" : "section-pill"}
                  onClick={() => setActiveConfigSection(section.id)}
                  type="button"
                >
                  {section.title}
                </button>
              ))}
            </nav>

            {configSearch.trim() ? (
              visibleConfigSections.length > 0 ? (
                visibleConfigSections.map((section) => (
                  <div key={section.id} className="section-block">
                    <h3>{section.title}</h3>
                    <p className="section-description">{section.description}</p>
                    <div className="field-grid">{section.fields.map((field) => renderField(field))}</div>
                  </div>
                ))
              ) : (
                <p className="empty-state">No settings found. Try another keyword.</p>
              )
            ) : selectedConfigSection ? (
              <div className="section-block">
                <h3>{selectedConfigSection.title}</h3>
                <p className="section-description">{selectedConfigSection.description}</p>
                <div className="field-grid">{selectedConfigSection.fields.map((field) => renderField(field))}</div>
              </div>
            ) : null}
          </section>
        )}

        {activeTab === "EXPORT" && (
          <section className="panel">
            <div className="field-grid">
              <label className="field"><span>Model</span><select value={exportForm.model_name} onChange={(event) => setExportForm((prev) => ({ ...prev, model_name: event.target.value }))}>{ptModelOptions.map((model) => <option key={model} value={model}>{model}</option>)}</select></label>
              <label className="field"><span>Image size</span><select value={String(exportForm.image_size)} onChange={(event) => setExportForm((prev) => ({ ...prev, image_size: Number(event.target.value) }))}>{["160", "320", "480", "640"].map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
              <label className="field"><span>Precision</span><select value={exportForm.precision} onChange={(event) => setExportForm((prev) => ({ ...prev, precision: event.target.value }))}><option value="half">half</option><option value="int8">int8</option></select></label>
              {exportForm.precision === "int8" && <label className="field"><span>Data YAML path</span><input value={exportForm.data_yaml_path} onChange={(event) => setExportForm((prev) => ({ ...prev, data_yaml_path: event.target.value }))} /></label>}
              <label className="field toggle-field"><span>Add NMS module</span><input type="checkbox" checked={!!exportForm.add_nms} disabled={exportForm.precision === "int8"} onChange={(event) => setExportForm((prev) => ({ ...prev, add_nms: event.target.checked }))} /></label>
            </div>
            <div className="button-row"><button disabled={isBusy} onClick={exportModel}>Export Model</button></div>
          </section>
        )}
        {activeTab === "TRAIN" && (
          <section className="panel">
            <div className="section-block">
              <h3>Model Source</h3>
              <div className="field-grid">
                <label className="field toggle-field">
                  <input
                    type="checkbox"
                    checked={!!trainForm.use_user_pretrained_models}
                    onChange={(event) =>
                      setTrainForm((prev) => ({ ...prev, use_user_pretrained_models: event.target.checked }))
                    }
                  />
                  <span>Use user checkpoints</span>
                </label>
                {trainForm.use_user_pretrained_models ? (
                  <label className="field">
                    <span>Checkpoint</span>
                    <select
                      value={trainForm.selected_checkpoint}
                      onChange={(event) =>
                        setTrainForm((prev) => ({ ...prev, selected_checkpoint: event.target.value }))
                      }
                    >
                      {checkpointOptions.map((model) => (
                        <option key={model} value={model}>
                          {model}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : (
                  <label className="field">
                    <span>Model</span>
                    <select
                      value={trainForm.selected_pretrained_model}
                      onChange={(event) =>
                        setTrainForm((prev) => ({ ...prev, selected_pretrained_model: event.target.value }))
                      }
                    >
                      {(meta.pretrained_models || []).map((model) => (
                        <option key={model} value={model}>
                          {model}
                        </option>
                      ))}
                    </select>
                  </label>
                )}
                <label className="field toggle-field">
                  <input
                    type="checkbox"
                    checked={!!trainForm.resume}
                    onChange={(event) => setTrainForm((prev) => ({ ...prev, resume: event.target.checked }))}
                  />
                  <span>Resume training</span>
                </label>
              </div>
            </div>

            {!trainForm.resume && (
              <div className="section-block">
                <h3>Data & Augmentation</h3>
                <div className="field-grid">
                  <label className="field">
                    <span>Data YAML</span>
                    <input
                      value={trainForm.data_yaml}
                      onChange={(event) => setTrainForm((prev) => ({ ...prev, data_yaml: event.target.value }))}
                    />
                  </label>
                  <label className="field">
                    <span>Epochs</span>
                    <input
                      type="number"
                      min="1"
                      step="1"
                      value={trainForm.epochs}
                      onChange={(event) => setTrainForm((prev) => ({ ...prev, epochs: Number(event.target.value) }))}
                    />
                  </label>
                  <label className="field">
                    <span>Image size</span>
                    <select
                      value={String(trainForm.img_size)}
                      onChange={(event) => setTrainForm((prev) => ({ ...prev, img_size: Number(event.target.value) }))}
                    >
                      {["1280", "640", "320", "160"].map((value) => (
                        <option key={value} value={value}>
                          {value}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="field toggle-field">
                    <input
                      type="checkbox"
                      checked={!!trainForm.use_cache}
                      onChange={(event) => setTrainForm((prev) => ({ ...prev, use_cache: event.target.checked }))}
                    />
                    <span>Use cache</span>
                  </label>
                  <label className="field toggle-field">
                    <input
                      type="checkbox"
                      checked={!!trainForm.augment}
                      onChange={(event) => setTrainForm((prev) => ({ ...prev, augment: event.target.checked }))}
                    />
                    <span>Use augmentation</span>
                  </label>
                  {trainForm.augment && (
                    <label className="field">
                      <span>Degrees</span>
                      <input
                        type="number"
                        value={trainForm.augment_degrees}
                        onChange={(event) =>
                          setTrainForm((prev) => ({ ...prev, augment_degrees: Number(event.target.value) }))
                        }
                      />
                    </label>
                  )}
                  {trainForm.augment && (
                    <label className="field">
                      <span>Flipud</span>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        value={trainForm.augment_flipud}
                        onChange={(event) =>
                          setTrainForm((prev) => ({ ...prev, augment_flipud: Number(event.target.value) }))
                        }
                      />
                    </label>
                  )}
                </div>
              </div>
            )}

            <div className="section-block">
              <h3>Resources & Logging</h3>
              <div className="field-grid">
                <label className="field">
                  <span>Device</span>
                  <select
                    value={String(trainForm.train_device)}
                    onChange={(event) => setTrainForm((prev) => ({ ...prev, train_device: event.target.value }))}
                  >
                    {deviceOptions.map((device) => (
                      <option key={device} value={device}>
                        {device}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  <span>Batch mode</span>
                  <select
                    value={trainForm.batch_mode}
                    onChange={(event) => setTrainForm((prev) => ({ ...prev, batch_mode: event.target.value }))}
                  >
                    <option value="auto">auto</option>
                    <option value="ratio">ratio</option>
                    <option value="fixed">fixed</option>
                  </select>
                </label>
                {trainForm.batch_mode === "ratio" && (
                  <label className="field">
                    <span>GPU ratio</span>
                    <input
                      type="number"
                      min="0.05"
                      max="0.95"
                      step="0.05"
                      value={trainForm.batch_ratio}
                      onChange={(event) => setTrainForm((prev) => ({ ...prev, batch_ratio: Number(event.target.value) }))}
                    />
                  </label>
                )}
                {trainForm.batch_mode === "fixed" && (
                  <label className="field">
                    <span>Batch size</span>
                    <input
                      type="number"
                      min="1"
                      step="1"
                      value={trainForm.batch_fixed}
                      onChange={(event) => setTrainForm((prev) => ({ ...prev, batch_fixed: Number(event.target.value) }))}
                    />
                  </label>
                )}
                <label className="field toggle-field">
                  <input
                    type="checkbox"
                    checked={!!trainForm.profile}
                    onChange={(event) => setTrainForm((prev) => ({ ...prev, profile: event.target.checked }))}
                  />
                  <span>Profile</span>
                </label>
                <label className="field toggle-field">
                  <input
                    type="checkbox"
                    checked={!!trainForm.disable_wandb}
                    onChange={(event) =>
                      setTrainForm((prev) => ({ ...prev, disable_wandb: event.target.checked }))
                    }
                  />
                  <span>Disable WANDB</span>
                </label>
              </div>
            </div>
            <div className="button-row">
              <button disabled={isBusy} onClick={startTrain}>
                Start Training
              </button>
            </div>
          </section>
        )}

        {activeTab === "TESTS" && (
          <section className="panel">
            <div className="field-grid">
              <label className="field"><span>Model</span><select value={testForm.input_model} onChange={(event) => setTestForm((prev) => ({ ...prev, input_model: event.target.value }))}>{modelOptions.map((model) => <option key={model} value={model}>{model}</option>)}</select></label>
              <label className="field"><span>Image size</span><select value={String(testForm.model_image_size)} onChange={(event) => setTestForm((prev) => ({ ...prev, model_image_size: Number(event.target.value) }))}>{["320", "480", "640"].map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
              <label className="field"><span>Source</span><select value={testForm.source_method} onChange={(event) => setTestForm((prev) => ({ ...prev, source_method: event.target.value }))}><option value="Default">Default</option><option value="Input file">Input file</option></select></label>
              {testForm.source_method === "Input file" && <label className="field"><span>Video file (.mp4)</span><input type="file" accept=".mp4" onChange={(event) => setTestVideo(event.target.files?.[0] || null)} /></label>}
              <label className="field toggle-field"><span>Window on top</span><input type="checkbox" checked={!!testForm.topmost} onChange={(event) => setTestForm((prev) => ({ ...prev, topmost: event.target.checked }))} /></label>
              <label className="field"><span>Device</span><select value={String(testForm.input_device)} onChange={(event) => setTestForm((prev) => ({ ...prev, input_device: event.target.value }))}>{deviceOptions.map((device) => <option key={device} value={device}>{device}</option>)}</select></label>
              <label className="field"><span>Frame delay</span><input type="number" min="1" max="120" value={testForm.input_delay} onChange={(event) => setTestForm((prev) => ({ ...prev, input_delay: Number(event.target.value) }))} /></label>
              <label className="field"><span>Resize (%)</span><input type="number" min="10" max="100" value={testForm.resize_factor} onChange={(event) => setTestForm((prev) => ({ ...prev, resize_factor: Number(event.target.value) }))} /></label>
              <label className="field"><span>AI confidence</span><input type="number" min="0.01" max="0.99" step="0.01" value={testForm.ai_conf} onChange={(event) => setTestForm((prev) => ({ ...prev, ai_conf: Number(event.target.value) }))} /></label>
            </div>
            <div className="button-row"><button disabled={isBusy} onClick={runTests}>Run Test</button></div>
          </section>
        )}

        {output && (
          <section className="output-panel" aria-label="Command output">
            <div className="output-header">
              <span>Command output</span>
              <button type="button" onClick={() => setOutput("")}>Clear</button>
            </div>
            <pre className="output" ref={outputRef}>{output}</pre>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
