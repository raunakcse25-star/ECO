<div align="center">

```
███████╗ ██████╗ ██████╗
██╔════╝██╔════╝██╔═══██╗
█████╗  ██║     ██║   ██║
██╔══╝  ██║     ██║   ██║
███████╗╚██████╗╚██████╔╝
╚══════╝ ╚═════╝ ╚═════╝
```

**Efficient Compressed Operations**

 <img src="src/assets/logo.jpeg" width="350" alt="8INARYBINDERS Logo">

*Private. Serverless. Blazing fast.*

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Built with WebRTC](https://img.shields.io/badge/Transport-WebRTC-blue)](https://webrtc.org/)
[![Compression: Huffman](https://img.shields.io/badge/Compression-Huffman-orange)](https://en.wikipedia.org/wiki/Huffman_coding)

</div>

---

## What is ECO?

**ECO** is a browser-based, peer-to-peer file transfer utility that never touches a server. Files travel directly from one device to another — compressed in memory, encrypted in transit, and gone without a trace once the session ends.

No accounts. No uploads. No cloud. Just two browsers and a direct pipe between them.

---

## Team

| Member | Role |
|---|---|
| 👑 **Nilesh Kumar Singh** | Project Lead & Integration — architecture, roadmap, and binding it all together |
| 🧠 **Raunak** | Compression Engineer — built the custom Huffman & RLE encoder/decoder from scratch |
| 🎨 **Saksham** | UI/UX Designer — responsive landing page, file drop zone, and overall interface |
| 🛰️ **Piyush Kumar** | Network Engineer — WebRTC P2P data channel & signaling server setup |

---

## Why ECO?

| Feature | ECO | Cloud Storage (Drive, Dropbox) |
|---|---|---|
| Server stores your file | ❌ Never | ✅ Always |
| Requires an account | ❌ No | ✅ Yes |
| Files leave your RAM | ❌ No | ✅ Yes |
| Compression before transfer | ✅ Custom Huffman + RLE | ❌ Varies |
| True P2P (no relay after handshake) | ✅ Yes | ❌ No |
| Works offline (LAN) | ✅ Possible | ❌ No |

---

## How It Works

```
SENDER                          RECEIVER
  │                                 │
  │  1. Select file                 │
  │  2. RLE + Huffman compress      │
  │  3. WebRTC handshake ──────────▶│
  │                                 │  4. Direct encrypted channel open
  │◀──────────────────── Confirmed ─│
  │                                 │
  │  5. Stream compressed bytes ───▶│
  │                                 │  6. Decompress in RAM
  │                                 │  7. Download prompt
  │                                 │
       [Central server exits here]
```

Once the WebRTC connection is established, the signaling server is **completely out of the picture**. Your data never passes through any infrastructure we (or anyone else) control.

---

## Core Pillars

### 🔒 Zero-Knowledge Privacy
Files are streamed directly from the **sender's RAM** to the **receiver's RAM**. Nothing is written to a server disk, nothing is logged, nothing persists after the session ends. ECO cannot see your files — by design.

### ⚡ Bit-Level Compression
ECO implements a **custom Huffman Coding + Run-Length Encoding pipeline** from scratch in JavaScript — no third-party compression libraries. Before any bytes leave your device, the file is compressed locally. For text-heavy files (logs, code, JSON, CSVs), this can yield **30–60% size reduction**, meaning faster transfers even on slow connections.

### 🛰️ True P2P via WebRTC
ECO uses **WebRTC Data Channels** to establish a direct, encrypted tunnel between browsers. A lightweight signaling server handles the initial handshake (SDP exchange), but once the connection is open, the server is bypassed entirely. The channel is secured by **DTLS-SRTP** encryption — the same standard used in video calls.

---

## Technical Stack

| Layer | Technology | Role |
|---|---|---|
| **Compression** | Huffman + RLE (Vanilla JS) | Bit-level & run-length pre-transfer encoding |
| **Transport** | WebRTC Data Channels | Encrypted P2P pipe |
| **Signaling** | Lightweight Node.js server | One-time handshake only |
| **UI** | Tailwind CSS | Responsive, minimal interface |

---

## Getting Started

### Prerequisites
- Node.js `v18+`
- A modern browser (Chrome, Firefox, Edge — WebRTC required)

### Installation

```bash
# Clone the repo
git clone https://github.com/nileshatgithab/ECO.git
cd ECO

# Install dependencies
npm install

# Start the signaling server
npm start
```

Open `http://localhost:3000` in **two separate browser tabs or devices** on the same network.

### Usage

1. **Sender** opens ECO and selects a file.
2. ECO compresses the file locally using RLE + Huffman coding.
3. A **session code** is generated and displayed.
4. **Receiver** enters the session code on their end.
5. WebRTC handshake completes — the direct pipe opens.
6. File streams across. Receiver gets a download prompt. Done.

---

## Project Structure

```
eco/
├── src/
│   ├── compression/
│   │   ├── huffman.js        # Custom Huffman encoder/decoder
│   │   └── rle.js            # Run-Length Encoding compression
│   ├── transport/
│   │   └── webrtc.js         # WebRTC P2P channel management
│   ├── ui/
│   │   └── script.js         # Frontend logic & file handling
│   └── server/
│       └── server.js         # Signaling server (handshake only)
├── public/
│   ├── index.html            # Main UI entry point
│   └── style.css             # Stylesheet
├── assets/
│   └── logo.png              # BINARYBINDERS logo
├── package.json
├── SIGNALING.md              # Signaling server documentation
└── README.md
```

---

## Compression: Under the Hood

ECO uses two complementary lossless compression algorithms that work together to maximize size reduction before any bytes hit the network.

### Huffman Coding (`huffman.js`)
Works in three phases:

1. **Frequency Analysis** — Scans the input file, counting byte occurrences.
2. **Tree Construction** — Builds a binary tree where the most frequent bytes get the shortest bit codes.
3. **Re-encoding** — Rewrites the file using variable-length bit codes, stripping redundancy.

The tree is serialized and sent ahead of the payload so the receiver can reconstruct the original file perfectly.

### Run-Length Encoding (`rle.js`)
A lightweight pre-pass that collapses consecutive repeated bytes into a count + value pair. For example, `AAAAAAA` becomes `7A` — dramatically shrinking files with long runs of repeated data (bitmaps, sparse logs, padded files).

> **Combined pipeline:** RLE runs first to collapse repetition, then Huffman encodes the result at the bit level for maximum compression. Both algorithms are **lossless** — your files arrive byte-for-byte identical to what was sent.

> Text-heavy files (source code, JSON, logs) compress best. Binary files (images, videos already compressed) see minimal gains — ECO detects this and skips compression when it would add overhead.

---

## Roadmap

- [ ] Multi-file / folder transfer support
- [ ] LAN peer discovery (mDNS)
- [ ] Transfer resume on connection drop
- [ ] Mobile PWA support
- [ ] Progress visualization with live compression ratio display
- [ ] Optional password-protected sessions

---

## Contributing

Contributions are welcome — bug reports, feature ideas, or pull requests.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-idea`
3. Commit your changes: `git commit -m 'Add: your feature'`
4. Push and open a Pull Request

Please keep PRs focused and include a clear description of what changed and why.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built by **BINARYBINDERS** · No cloud. No compromise.

</div>
