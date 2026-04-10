import CryptoJS from "crypto-js";

const STORAGE_KEY = "ai_writer_encrypted_draft_v1";

/** Dev: Vite proxies `/api` → FastAPI (see vite.config.js). Override with `VITE_API_BASE`. */
function apiBase() {
  const raw = import.meta.env.VITE_API_BASE;
  if (raw) return raw.replace(/\/$/, "");
  return "/api";
}

/**
 * Encrypts text with AES (CryptoJS). Ciphertext is what you could send over the wire;
 * this app keeps drafts only in localStorage — no fetch/XMLHttpRequest.
 */
export function encryptDraft(plainText, passphrase) {
  if (!passphrase) throw new Error("Passphrase is required to encrypt.");
  return CryptoJS.AES.encrypt(plainText, passphrase).toString();
}

export function decryptDraft(cipherText, passphrase) {
  if (!passphrase) throw new Error("Passphrase is required to decrypt.");
  const bytes = CryptoJS.AES.decrypt(cipherText, passphrase);
  const decoded = bytes.toString(CryptoJS.enc.Utf8);
  if (!decoded) throw new Error("Wrong passphrase or corrupted data.");
  return decoded;
}

/** Lightweight local rewrite — no backend, nothing in Network from this step. */
export function localRewrite(plainText) {
  const trimmed = plainText.trim();
  if (!trimmed) return "";
  const sentences = trimmed.split(/(?<=[.!?])\s+/).filter(Boolean);
  if (sentences.length < 2) {
    return trimmed.replace(/\bi\b/g, "I").replace(/\s+/g, " ").trim();
  }
  const [first, ...rest] = sentences;
  return [...rest, first].join(" ").replace(/\bi\b/g, "I");
}

export function mountAIContentRewriter(root) {
  if (!root) return;

  root.innerHTML = `
    <main style="max-width:42rem;margin:2rem auto;font-family:system-ui,sans-serif;line-height:1.5">
      <h1 style="font-size:1.25rem">Draft</h1>
      <p style="color:#444;font-size:0.9rem">
        Drafts can be encrypted with CryptoJS and saved in <code>localStorage</code>.
        Optional: send <strong>only ciphertext</strong> to the FastAPI/Flask server for rewrite
        (<code>POST /v1/content/rewrite-encrypted</code>).
      </p>
      <label style="display:block;margin:0.75rem 0 0.25rem">Passphrase</label>
      <input id="pass" type="password" autocomplete="off" placeholder="Used only in this tab"
        style="width:100%;padding:0.5rem;box-sizing:border-box" />
      <label style="display:block;margin:0.75rem 0 0.25rem">Content</label>
      <textarea id="body" rows="10" style="width:100%;padding:0.5rem;box-sizing:border-box"></textarea>
      <div style="display:flex;flex-wrap:wrap;gap:0.5rem;margin-top:0.75rem">
        <button type="button" id="save">Encrypt & save locally</button>
        <button type="button" id="load">Decrypt & load</button>
        <button type="button" id="rewrite">Local rewrite</button>
        <button type="button" id="rewrite-api">Server rewrite (encrypted)</button>
      </div>
      <p id="msg" style="margin-top:0.75rem;font-size:0.875rem;color:#666"></p>
    </main>
  `;

  const passEl = root.querySelector("#pass");
  const bodyEl = root.querySelector("#body");
  const msgEl = root.querySelector("#msg");

  const setMsg = (text, ok = true) => {
    msgEl.textContent = text;
    msgEl.style.color = ok ? "#166534" : "#b91c1c";
  };

  root.querySelector("#save").addEventListener("click", () => {
    try {
      const cipher = encryptDraft(bodyEl.value, passEl.value);
      localStorage.setItem(STORAGE_KEY, cipher);
      setMsg("Saved encrypted draft to localStorage.");
    } catch (e) {
      setMsg(e.message || String(e), false);
    }
  });

  root.querySelector("#load").addEventListener("click", () => {
    try {
      const cipher = localStorage.getItem(STORAGE_KEY);
      if (!cipher) {
        setMsg("Nothing saved yet.", false);
        return;
      }
      bodyEl.value = decryptDraft(cipher, passEl.value);
      setMsg("Loaded and decrypted.");
    } catch (e) {
      setMsg(e.message || String(e), false);
    }
  });

  root.querySelector("#rewrite").addEventListener("click", () => {
    bodyEl.value = localRewrite(bodyEl.value);
    setMsg("Applied local rewrite (no network).");
  });

  root.querySelector("#rewrite-api").addEventListener("click", async () => {
    try {
      const ciphertext = encryptDraft(bodyEl.value, passEl.value);
      const res = await fetch(`${apiBase()}/v1/content/rewrite-encrypted`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ciphertext, passphrase: passEl.value }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = data.detail;
        const msg =
          typeof detail === "string"
            ? detail
            : Array.isArray(detail)
              ? JSON.stringify(detail)
              : res.statusText || "Request failed";
        setMsg(msg, false);
        return;
      }
      bodyEl.value = data.plaintext ?? "";
      setMsg(`Server rewrite OK (${data.source ?? "?"}) — run FastAPI on port 8000 or set VITE_API_BASE.`);
    } catch (e) {
      setMsg(e.message || String(e), false);
    }
  });
}
