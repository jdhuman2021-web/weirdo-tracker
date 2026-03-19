# Dev Tools & Terminal Extensions Index

**20 Commonly Used Tools for Windows/PowerShell Development**

---

## 🖥️ Terminal Emulators

| # | Tool | Description | Install |
|---|------|-------------|---------|
| 1 | **Windows Terminal** | Modern terminal app with tabs, panes, GPU rendering, Unicode support. Replaces old cmd.exe console. | `winget install Microsoft.WindowsTerminal` |
| 2 | **Cmder** | Portable console emulator with Unix tools (ls, grep, ssh) bundled. Great for Git integration. | `choco install cmder` |
| 3 | **ConEmu** | Customizable terminal with Quake-style dropdown, task automation, and multi-tab support. | `choco install conemu` |

---

## 🎨 Shell Enhancements

| # | Tool | Description | Install |
|---|------|-------------|---------|
| 4 | **Oh My Posh** | Cross-platform prompt engine with themes, git status, cloud CLI indicators (AWS, Azure, GCP). | `winget install JanDeDobbeleer.OhMyPosh` |
| 5 | **PowerShell 7** | Latest PowerShell with pipelines, cross-platform, improved performance vs. Windows PowerShell 5.1. | `winget install Microsoft.PowerShell` |
| 6 | **z.lua** | Fast directory jumper (like zsh-z). `cd` less, jump more via frecency algorithm. | `choco install z.lua` |
| 7 | **fzf** | Fuzzy finder for files, history, processes. Ctrl+R history, Ctrl+T file search. | `choco install fzf` |

---

## 📦 Package Managers

| # | Tool | Description | Install |
|---|------|-------------|---------|
| 8 | **Scoop** | Dev-focused package manager. CLI tools, portable apps, no admin required. | `iwr -useb get.scoop.sh | iex` |
| 9 | **Chocolatey** | Windows package manager. Broad software library, admin-friendly. | `choco install -y chocolatey` |
| 10 | **winget** | Microsoft's native package manager. Built into Windows 10/11. | Pre-installed |

---

## 🔧 Version Control

| # | Tool | Description | Install |
|---|------|-------------|---------|
| 11 | **Git for Windows** | Distributed version control with Bash emulation, SSH, GPG signing. | `winget install Git.Git` |
| 12 | **GitHub CLI (gh)** | Official GitHub CLI. PRs, issues, actions from terminal. | `winget install GitHub.cli` |
| 13 | **Lazygit** | Terminal UI for Git. Visual branch graph, staging, commits. | `choco install lazygit` |

---

## 🐳 Containers & VMs

| # | Tool | Description | Install |
|---|------|-------------|---------|
| 14 | **Docker Desktop** | Container runtime with Kubernetes, WSL2 backend, image management. | `winget install Docker.DockerDesktop` |
| 15 | **WSL2** | Windows Subsystem for Linux 2. Run Ubuntu, Debian, etc. natively on Windows. | `wsl --install` |
| 16 | **Multipass** | Lightweight Ubuntu VMs. Quick spin-up for testing, isolated environments. | `winget install Canonical.Multipass` |

---

## 🧪 API & Debugging

| # | Tool | Description | Install |
|---|------|-------------|---------|
| 17 | **HTTPie** | Human-friendly HTTP client. Better curl alternative with JSON, auth, colors. | `choco install httpie` |
| 18 | **jq** | JSON processor. Parse, filter, transform JSON from APIs. | `choco install jq` |
| 19 | **Postman** | API testing GUI. Collections, environments, automated testing. | `winget install Postman` |
| 20 | **Wireshark** | Network protocol analyzer. Deep packet inspection, troubleshooting. | `choco install wireshark` |

---

## 🔌 VS Code Extensions (Bonus)

| Extension | Purpose |
|-----------|---------|
| **Remote - WSL** | Edit Linux files from Windows VS Code |
| **Docker** | Container management, Dockerfile linting |
| **GitLens** | Git blame, history, code navigation |
| **PowerShell** | IntelliSense, debugging, snippets |
| **REST Client** | Test APIs directly in VS Code |
| **Prettier** | Code formatting (JS, TS, JSON, YAML) |
| **Thunder Client** | Lightweight Postman alternative |

---

## 🚀 Quick Install Script (PowerShell)

```powershell
# Install core tools in one go
winget install Microsoft.WindowsTerminal
winget install Microsoft.PowerShell
winget install Git.Git
winget install GitHub.cli
winget install JanDeDobbeleer.OhMyPosh
winget install Docker.DockerDesktop
choco install fzf
choco install jq
choco install httpie
choco install lazygit

# Enable WSL2
wsl --install -d Ubuntu
```

---

## 📊 My Top 5 Recommendations

| Priority | Tool | Why |
|----------|------|-----|
| 1 | **Windows Terminal** | Modern, fast, tabs, Unicode — essential |
| 2 | **PowerShell 7** | Better pipelines, cross-platform, active dev |
| 3 | **Oh My Posh** | Prompt themes + git/cloud status visibility |
| 4 | **Git + GitHub CLI** | Version control + PR management from terminal |
| 5 | **fzf** | Fuzzy search transforms workflow (history, files) |

---

## 🎯 For Your Setup (Crypto + Recruiting)

| Use Case | Recommended Tools |
|----------|-------------------|
| **Solana tracker automation** | PowerShell 7, jq (JSON parsing), HTTPie (API calls) |
| **Notion/database management** | Windows Terminal, Oh My Posh (git status) |
| **API testing (DexScreener)** | HTTPie, jq, Postman |
| **Document/version control** | Git, GitHub CLI, Lazygit |
| **Containerized testing** | Docker Desktop, WSL2 |

---

## ✅ Install Checklist

- [ ] Windows Terminal
- [ ] PowerShell 7
- [ ] Git for Windows
- [ ] GitHub CLI
- [ ] Oh My Posh
- [ ] fzf
- [ ] jq
- [ ] HTTPie
- [ ] Docker Desktop (optional)
- [ ] WSL2 (optional)

---

## 🍀 Pro Tips

1. **Start small** — Install 3-5 tools, master them, then add more
2. **Profile backup** — Export your PowerShell profile before customizing
3. **Test in WSL** — Some tools work better in Linux environment
4. **Use winget first** — Native, no admin prompts
5. **Scoop for dev tools** — Cleaner than Chocolatey for dev-focused packages

---

**Want me to:**
- Run an install command for any of these?
- Set up Oh My Posh theme + PowerShell profile?
- Create a PowerShell profile template (with fzf, z.lua, git)?
- Check what's already installed on your machine?

Let me know! 🎯
