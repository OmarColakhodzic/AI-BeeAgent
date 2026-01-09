import React, { useState } from "react";

const inputStyle = {
  width: "100%",
  padding: "8px 12px",
  marginTop: 6,
  marginBottom: 16,
  borderRadius: 6,
  border: "1.5px solid #ccc",
  fontSize: 16,
  boxSizing: "border-box",
  transition: "border-color 0.3s",
};

const labelStyle = {
  display: "block",
  fontWeight: "600",
  fontSize: 14,
  color: "#333",
};

const buttonStyle = {
  padding: "12px 20px",
  marginRight: 10,
  backgroundColor: "#4CAF50",
  border: "none",
  borderRadius: 6,
  color: "white",
  fontWeight: "600",
  fontSize: 16,
  cursor: "pointer",
  transition: "background-color 0.3s",
};

const buttonSecondaryStyle = {
  ...buttonStyle,
  backgroundColor: "#f44336",
};

const buttonDisabledStyle = {
  ...buttonStyle,
  backgroundColor: "#cccccc",
  cursor: "not-allowed",
};

const containerStyle = {
  maxWidth: 440,
  margin: "30px auto",
  padding: 24,
  borderRadius: 10,
  boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
  backgroundColor: "#fff",
  fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
  color: "#222",
};

const titleStyle = {
  textAlign: "center",
  marginBottom: 24,
  fontWeight: "700",
  fontSize: 28,
  color: "#333",
  userSelect: "none",
};

const textareaStyle = {
  width: "100%",
  minHeight: 80,
  borderRadius: 6,
  border: "1.5px solid #ccc",
  padding: 10,
  fontSize: 15,
  resize: "vertical",
  boxSizing: "border-box",
  marginTop: 10,
  marginBottom: 16,
};

const errorStyle = {
  color: "red",
  fontWeight: "600",
  marginBottom: 16,
  userSelect: "none",
};

const infoStyle = {
  color: "#2196F3",
  fontWeight: "600",
  marginBottom: 16,
  userSelect: "none",
  backgroundColor: "#E3F2FD",
  padding: "10px",
  borderRadius: "6px",
  border: "1px solid #BBDEFB",
};

const progressStyle = {
  backgroundColor: "#4CAF50",
  height: "6px",
  borderRadius: "3px",
  marginTop: "10px",
  transition: "width 0.5s ease-in-out",
};

export default function App() {
  const options = [
    { value: "nista", label: "Ništa" },
    { value: "priorihrana", label: "Prihrana" },
    { value: "provjera_varoe", label: "Provjera varoe" },
    { value: "preseljenje", label: "Preseljenje" },
    { value: "berba", label: "Berba" },
    { value: "zalivanje", label: "Zalivanje" },
    { value: "hranjivanje", label: "Hranjivanje" },
    { value: "prskanje", label: "Prskanje" },
    { value: "povecanje_ramova", label: "Povećanje ramova" },
    { value: "smanjenje_ramova", label: "Smanjenje ramova" },
    { value: "kontrola_stetocina", label: "Kontrola štetočina" },
    { value: "promjena_lokacije", label: "Promjena lokacije" },
    { value: "provjera_zdravlja", label: "Provjera zdravlja" },
    { value: "ciscenje_zajednice", label: "Čišćenje zajednice" },
    { value: "dodatna_inspekcija", label: "Dodatna inspekcija" },
  ];

  function getLabel(value) {
    const option = options.find((o) => o.value === value);
    return option ? option.label : value;
  }

  const initialForm = {
    temperature: 15,
    humidity: 50,
    frames: 8,
    strength: 5,
    varoa: "",
  };

  const [form, setForm] = useState(initialForm);
  const [prediction, setPrediction] = useState(null);
  const [obsId, setObsId] = useState(null);
  const [comment, setComment] = useState("");
  const [error, setError] = useState(null);
  const [info, setInfo] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);

  const [showCorrectionModal, setShowCorrectionModal] = useState(false);
  const [correctionInput, setCorrectionInput] = useState("");

  function validateForm() {
    if (
      form.temperature === "" ||
      isNaN(form.temperature) ||
      form.temperature < -50 ||
      form.temperature > 60
    ) {
      setError("Temperatura mora biti broj između -50 i 60.");
      return false;
    }
    if (
      form.humidity === "" ||
      isNaN(form.humidity) ||
      form.humidity < 0 ||
      form.humidity > 100
    ) {
      setError("Vlaga mora biti broj između 0 i 100.");
      return false;
    }
    if (
      form.frames === "" ||
      isNaN(form.frames) ||
      form.frames < 1 ||
      form.frames > 50
    ) {
      setError("Broj ramova mora biti između 1 i 50.");
      return false;
    }
    if (
      form.strength === "" ||
      isNaN(form.strength) ||
      form.strength < 1 ||
      form.strength > 10
    ) {
      setError("Snaga zajednice mora biti između 1 i 10.");
      return false;
    }
    if (form.varoa !== 0 && form.varoa !== 1) {
      setError("Molimo odaberite prisustvo varoe (Da ili Ne).");
      return false;
    }
    setError(null);
    return true;
  }

  async function pollPredictionResult(observationId) {
    const maxAttempts = 30;
    const pollInterval = 500;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      setProgress((attempt / maxAttempts) * 100);
      setInfo(`Agent obrađuje... (${attempt}/${maxAttempts})`);

      await new Promise(resolve => setTimeout(resolve, pollInterval));

      try {
        const res = await fetch(`http://localhost:8000/predictions/${observationId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();

        if (data.status === 'processed') {
          return {
            obs_id: observationId,
            prediction: data.predicted_action,
            ml_prediction: data.predicted_action,
            source: "ml",
            exploring: false,
            confidence: data.confidence
          };
        } else if (data.status === 'queued' || data.status === 'processing') {
          continue;
        } else {
          throw new Error(`Predikcija nije uspjela: ${data.error || 'Nepoznata greška'}`);
        }
      } catch (e) {
        console.error("Poll error:", e);
      }
    }

    throw new Error('Agent je predugo radio. Pokušajte ponovo.');
  }

  async function handlePredict() {
    if (!validateForm()) return;

    setIsProcessing(true);
    setInfo("Šaljem podatke agentu...");
    setProgress(10);

    try {
      const res = await fetch("http://localhost:8000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      if (!res.ok) throw new Error("Greška pri pozivu API-ja");

      const data = await res.json();

      if (data.status !== 'queued') {
        throw new Error(`Neočekivani odgovor: ${JSON.stringify(data)}`);
      }

      setObsId(data.observation_id);
      setInfo(`Podaci poslani. ID: ${data.observation_id}. Čekam agenta...`);
      setProgress(30);

      const predictionResult = await pollPredictionResult(data.observation_id);

      setPrediction(predictionResult.prediction);
      setInfo(null);
      setProgress(100);

    } catch (e) {
      setError("Greška: " + e.message);
    } finally {
      setIsProcessing(false);
      setTimeout(() => setProgress(0), 1000);
    }
  }

  async function sendFeedback(correct, userLabel = null) {
    let label = correct ? prediction : userLabel;
    if (!label) return;

    try {
      await fetch("http://localhost:8000/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          obs_id: obsId,
          user_label: label,
          correct,
          comment,
        }),
      });
      alert("Hvala! Model je naučio iz tvog feedbacka.");

      setForm(initialForm);
      setPrediction(null);
      setObsId(null);
      setComment("");
      setError(null);
      setInfo(null);
      setCorrectionInput("");
      setShowCorrectionModal(false);
    } catch {
      alert("Došlo je do greške pri slanju feedbacka.");
    }
  }

  function handleChange(field, value) {
    if (field === "varoa") {
      const parsed = parseInt(value);
      setForm({ ...form, varoa: parsed === 1 ? 1 : 0 });
      return;
    }
    const parsed = parseInt(value);
    setForm({ ...form, [field]: isNaN(parsed) ? "" : parsed });
  }

  return (
    <div style={containerStyle}>
      <h1 style={titleStyle}>🐝 BeeAgent — Pametni savjetnik</h1>

      {error && <div style={errorStyle}>{error}</div>}
      {info && <div style={infoStyle}>{info}</div>}

      <label style={labelStyle} htmlFor="temperature">
        Temperatura:
        <input
          id="temperature"
          type="number"
          style={inputStyle}
          value={form.temperature}
          onChange={(e) => handleChange("temperature", e.target.value)}
          min={-50}
          max={60}
          disabled={isProcessing}
        />
      </label>

      <label style={labelStyle} htmlFor="humidity">
        Vlaga (%):
        <input
          id="humidity"
          type="number"
          style={inputStyle}
          value={form.humidity}
          onChange={(e) => handleChange("humidity", e.target.value)}
          min={0}
          max={100}
          disabled={isProcessing}
        />
      </label>

      <label style={labelStyle} htmlFor="frames">
        Broj ramova:
        <input
          id="frames"
          type="number"
          style={inputStyle}
          value={form.frames}
          onChange={(e) => handleChange("frames", e.target.value)}
          min={1}
          max={50}
          disabled={isProcessing}
        />
      </label>

      <label style={labelStyle} htmlFor="strength">
        Snaga zajednice (1-10):
        <input
          id="strength"
          type="number"
          style={inputStyle}
          value={form.strength}
          onChange={(e) => handleChange("strength", e.target.value)}
          min={1}
          max={10}
          disabled={isProcessing}
        />
      </label>

      <label style={labelStyle} htmlFor="varoa">
        Prisustvo varoe:
        <select
          id="varoa"
          style={{ ...inputStyle, paddingRight: 30 }}
          value={form.varoa === "" ? "" : form.varoa}
          onChange={(e) => handleChange("varoa", e.target.value)}
          disabled={isProcessing}
        >
          <option value="" disabled>
            Odaberi...
          </option>
          <option value={0}>Ne</option>
          <option value={1}>Da</option>
        </select>
      </label>

      <button
        style={isProcessing ? buttonDisabledStyle : { ...buttonStyle, width: "100%" }}
        onClick={handlePredict}
        disabled={isProcessing}
      >
        {isProcessing ? "Agent obrađuje..." : "Pošalji podatke"}
      </button>

      {isProcessing && progress > 0 && (
        <div style={{ marginTop: "15px" }}>
          <div style={{ ...progressStyle, width: `${progress}%` }}></div>
        </div>
      )}

      {prediction && (
        <div style={{ marginTop: 30 }}>
          <h2
            style={{
              fontWeight: "700",
              fontSize: 22,
              color: "#2c3e50",
              userSelect: "none",
            }}
          >
            Preporuka agenta: <span>{getLabel(prediction)}</span>
          </h2>

          <textarea
            placeholder="Komentar (opcionalno)"
            style={textareaStyle}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />

          <div>
            <button style={buttonStyle} onClick={() => sendFeedback(true)}>
              Prihvati
            </button>
            <button
              style={buttonSecondaryStyle}
              onClick={() => setShowCorrectionModal(true)}
            >
              Odbaci / Ispravi
            </button>
          </div>
        </div>
      )}

      {showCorrectionModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100vw",
            height: "100vh",
            backgroundColor: "rgba(0,0,0,0.5)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 1000,
          }}
          onClick={() => setShowCorrectionModal(false)}
        >
          <div
            style={{
              backgroundColor: "white",
              padding: 20,
              borderRadius: 8,
              minWidth: 320,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3>Unesi ispravnu akciju</h3>
            <select
              style={{
                width: "100%",
                padding: "8px",
                fontSize: 16,
                marginBottom: 16,
                borderRadius: 4,
                border: "1.5px solid #ccc",
              }}
              value={correctionInput}
              onChange={(e) => setCorrectionInput(e.target.value)}
              autoFocus
            >
              <option value="" disabled>
                Odaberi akciju...
              </option>
              {options.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <div style={{ textAlign: "right" }}>
              <button
                style={{ ...buttonSecondaryStyle, marginRight: 8 }}
                onClick={() => {
                  setShowCorrectionModal(false);
                  setCorrectionInput("");
                }}
              >
                Otkaži
              </button>
              <button
                style={buttonStyle}
                onClick={() => {
                  if (!correctionInput) {
                    alert("Molimo odaberite jednu od ponuđenih akcija.");
                    return;
                  }
                  sendFeedback(false, correctionInput);
                }}
              >
                Pošalji
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}