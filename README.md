# 🌌 Zero-Trace

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-6f42c1?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge&logo=opensourceinitiative&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-Frontend-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![Encryption](https://img.shields.io/badge/Encryption-AES--256--GCM-0ea5e9?style=for-the-badge&logo=letsencrypt&logoColor=white)
![Crypto API](https://img.shields.io/badge/Web_Crypto-SubtleCrypto-f59e0b?style=for-the-badge&logo=webauthn&logoColor=white)
![Zero Knowledge](https://img.shields.io/badge/Architecture-Zero--Knowledge-ef4444?style=for-the-badge)


</div>

<br/>

> *"A transmission protocol designed for total digital privacy."*

**ZERO-TRACE** is a high-performance, private file-sharing node engineered for secure, ephemeral data transmission. By leveraging **Client-Side Encryption**, the server remains in a perpetual **Zero-Knowledge** state — your files are encrypted *before* they ever leave your browser. The decryption key never touches the server. Ever.

---

## 📡 Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ZERO-TRACE FLOW                          │
└─────────────────────────────────────────────────────────────────────┘

  [ SENDER SIDE ]                              [ RECEIVER SIDE ]
  ───────────────                              ─────────────────

  ┌──────────┐                                 ┌──────────────────┐
  │  Browser │                                 │     Browser      │
  │          │                                 │                  │
  │ 1. Select│                                 │ 7. Opens Link    │
  │    File  │                                 │    with #KEY     │
  └────┬─────┘                                 └───────┬──────────┘
       │                                               │
       ▼                                               ▼
  ┌──────────────────────┐                  ┌──────────────────────┐
  │  Web Crypto API      │                  │  Web Crypto API      │
  │  (SubtleCrypto)      │                  │  (SubtleCrypto)      │
  │                      │                  │                      │
  │  2. Generate Key     │                  │  8. Extract Key      │
  │     (AES-256-GCM)    │                  │     from URL #frag   │
  │  3. Encrypt File     │                  │  9. Decrypt File     │
  └──────────┬───────────┘                  └──────────┬───────────┘
             │                                         │
             │ Encrypted Blob                          │ Decrypted File
             ▼                                         ▲
  ┌──────────────────────┐                             │
  │  FastAPI Server      │ ──── Share Link ──────────► │
  │  (Zero-Knowledge)    │   https://host/dl/ID#KEY    │
  │                      │                             │
  │  4. Store Ciphertext │                  ┌──────────┴───────────┐
  │  5. Return File ID   │ ◄──── GET /dl ── │  FastAPI Server      │
  │  6. Build Share URL  │                  │                      │
  │                      │ ──── Ciphertext ►│  10. Serve Ciphertext│
  │  [BURN Protocol]     │                  │  [BURN: Delete File] │
  │  Auto-Expire: 3hrs   │                  └──────────────────────┘
  └──────────────────────┘
             │
             ▼
  ┌──────────────────────┐
  │  Session Reaper      │
  │  (Runs every 1hr)    │
  │  Purges files > 3hrs │
  └──────────────────────┘
```

---

## ⚡ Core Protocols

| Protocol | Description |
|---|---|
| 🔐 **AES-256-GCM** | Hardware-accelerated, government-grade encryption with built-in integrity verification — tampering is mathematically detectable. |
| 🧠 **Zero-Knowledge** | The decryption key lives exclusively in the URL `#fragment`, which is never sent to the server by HTTP spec. The node is blind to plaintext. |
| 🔥 **BURN Protocol** | Optional one-time-use self-destruct. The file is wiped from disk the microsecond the download stream completes. |
| 📦 **650MB Tunnel** | Efficient memory-spooled chunked transfer supports large asset delivery without destabilizing the server process. |
| ⏱️ **Session Decay** | A background reaper runs every hour, purging all transmissions older than 3 hours. No data lingers. |

---

## 🛠️ Tech Stack

<div align="center">

| Layer | Technology |
|---|---|
| **Backend Engine** | Python · FastAPI · Uvicorn |
| **Cryptography** | Web Crypto API (SubtleCrypto · AES-256-GCM) |
| **Frontend** | HTML5 · Glassmorphism UI |
| **Containerization** | `.env` Isolated Config |
| **Key Exchange** | URL Fragment (`#`) — never sent to server |

</div>

---

## 🚀 Deployment

### Prerequisites

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![pip](https://img.shields.io/badge/pip-latest-3775A9?logo=pypi&logoColor=white)


### 1. Clone the Repository

```bash
git clone https://github.com/Arghyadip01/ZERO-TRACE.git
cd ZERO-TRACE
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
APP_HOST="host address"
APP_PORT="port"
```

> **Note:** You can bind to `0.0.0.0` for external access. Always place this node behind an HTTPS reverse proxy (e.g., Nginx + Certbot) in production.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Launch the Node

```bash
uvicorn app:app --env-file .env --reload
```

---

## 🔑 Usage Guide

1. **Open** `http://localhost:8000` (or your configured host/port)
2. **Select** the file you wish to transmit
3. **Toggle** `🔥 Protocol: BURN` if you want the link to self-destruct after one download
4. **Upload** — the file is encrypted client-side before any network transfer
5. **Share** the generated link (e.g., `https://yourhost/dl/abc123#<AES_KEY>`)
6. **Receiver** opens the link — the key after `#` is extracted locally, the ciphertext is fetched, and decryption occurs entirely in the browser

> ⚠️ The key is in the URL fragment. Do not share the link over channels that log URLs (e.g., some link-preview services).

---

---

## 📦 Requirements

```txt
fastapi
uvicorn[standard]
python-multipart
python-dotenv
aiofiles
```

---

## 🛡️ Security Model

```
What the server SEES:         What the server NEVER SEES:
─────────────────────         ───────────────────────────
✅ Encrypted ciphertext       ❌ The decryption key
✅ File size                  ❌ File contents (plaintext)
✅ Upload timestamp           ❌ Original filename
✅ File ID (random UUID)      ❌ Receiver's identity
```

The URL fragment (`#key`) is a browser-enforced boundary — it is never included in HTTP requests to the server. This is the cryptographic foundation of the Zero-Knowledge guarantee.

---

## ⚠️ Disclaimer

This tool is provided for **legitimate, private, and secure file sharing**. All cryptographic operations are performed exclusively client-side. The node operator has **zero access** to the plaintext contents of any file transmitted through this system.

- Always verify the integrity of the share URL before authorizing decryption
- Deploy behind HTTPS in any production or internet-facing environment
- This tool does not anonymize your IP — use Tor or a VPN if network-layer anonymity is required

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for details.

---

<div align="center">

Developed by **[Arghyadip01](https://github.com/Arghyadip01)** © 2026

*Files face Oblivion. Your privacy endures.*

</div>