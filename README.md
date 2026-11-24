# NetScope — Network Diagnostics & IP Analyzer

An educational Python desktop application for the Network Programming laboratory.

![NetScope desktop interface](preview.png)

## Features
- IPv4/IPv6 validation and classification using `ipaddress`
- DNS resolution with `socket.getaddrinfo()`
- IP intelligence: optional approximate country, region, ISP and ASN over verified HTTPS, plus offline address classification and security context; no threat reputation verdict.
- Local TCP echo client/server and bounded loopback port checks
- Responsive Tkinter/ttk interface using background threads and a queue
- SQLite activity history and CSV export

## Run locally
Python 3.10+ with Tkinter installed. No third-party Python packages are required.

```sh
python main.py
```

On Linux, use `python3 main.py`; install your distribution's Tkinter package if needed.

## Tests
```sh
python -m unittest -v
```

## Course concepts
| Lab | Application |
|---|---|
| Week 1 | IP classification, DNS, sockets |
| Weeks 2–3 | TCP client/server, encoding, error handling |
| Week 4 | Tkinter event-driven GUI |
| Week 5 | Local-only TCP port checks |
| Week 6 | Background threads and classes |
| Week 8 | Thread-safe queue |
| Week 9 | HTTPS certificate verification (not a custom TLS server) |
| Database labs | SQLite and GUI history |

## Scope and limitations
TCP lab operations are restricted to loopback. Public IP metadata requires an internet connection and is not precise physical location information. The desktop application runs locally; the GitHub Pages site is a presentation, not a hosted Python runtime.

[Arabic usage guide](README_AR.md)
