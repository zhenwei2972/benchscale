# Setting up benchscale

**Test prints so far.** The 12-hole shake-fill coupon set (deck, stand and lid) printed successfully on a
Bambu Lab A1 mini in PLA on 11 Oct 2026. It took 68 min against a 72 min slicer estimate, and the camera
frames at each stage show all three parts intact, with no stringing or detached parts. Filling it with real
tips has not been measured yet, and the full 96-hole rack and the tip-box dock have not been printed.

There are three ways to use benchscale. Claude Desktop and Claude Code use your Claude account, so you
need no API key.

| Way | Best for | You need |
|---|---|---|
| [Claude Desktop](#1-claude-desktop) | Chatting your way to a part | Claude Desktop, Python 3.10+ |
| [Claude Code](#2-claude-code) | Working in a terminal, or changing templates | Claude Code, Python 3.10+ |
| [GitHub Codespaces](#3-github-codespaces-nothing-to-install) | Trying it with nothing installed | A GitHub account |

## Install (for Claude Desktop, Claude Code or the command line)

benchscale needs **Python 3.10 or newer**. The `python3` that ships with macOS is 3.9 and will not
work. These steps use [uv](https://docs.astral.sh/uv/), which installs the right Python for you:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh          # once; or: brew install uv
git clone https://github.com/zhenwei2972/benchscale && cd benchscale
uv venv --python 3.12 && uv pip install -e ".[dev]"
.venv/bin/benchscale fetch                                # downloads the linked labware data, about 10 s
.venv/bin/benchscale templates                            # should list four templates
```

## 1. Claude Desktop

1. Do the install above, then print the full path of the `benchscale` command:
   `echo "$PWD/.venv/bin/benchscale"`
2. In Claude Desktop open **Settings → Developer → Edit Config**. Add this to `claude_desktop_config.json`,
   using your path, and save:
   ```json
   {"mcpServers": {"benchscale": {"command": "/full/path/to/benchscale/.venv/bin/benchscale", "args": ["mcp"]}}}
   ```
3. Quit and reopen Claude Desktop. "benchscale" should appear among the connectors.
4. Check it works: ask *"List the benchscale templates."* Then ask for a part, for example *"Our bulk
   Axygen 200 µL tips take ages to rack. Make me something that loads them."*
5. To see each design in 3D, run `.venv/bin/benchscale serve` and open http://localhost:8742. It refreshes
   on every new design.

## 2. Claude Code

1. Do the install above, then start Claude Code inside the folder with the environment active:
   ```bash
   source .venv/bin/activate && claude
   ```
2. The repository's `.mcp.json` registers the benchscale server. Approve it when Claude Code asks. If it
   doesn't ask, add it yourself: `claude mcp add benchscale -- "$PWD/.venv/bin/benchscale" mcp`
3. Check it works: ask *"List the benchscale templates."* Steps 4 and 5 of Claude Desktop apply here too.

## 3. GitHub Codespaces (nothing to install)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/zhenwei2972/benchscale?quickstart=1)

The button opens benchscale in your own cloud workspace on GitHub, ready to use. The first start takes a
few minutes while it installs; later starts are quicker. Claude Code and the 3D viewer are both set up.

1. Click the button, then **Create codespace**.
2. When it opens, the viewer starts on port 8742. Open it from the **Ports** tab if it does not appear.
3. Choose how to chat:
   - **Claude Code, no API key.** Type `claude` in the terminal and sign in with your Claude account. The
     benchscale tools are already connected.
   - **Built-in chat in the viewer, with your own API key.** Add a Codespaces secret named
     `ANTHROPIC_API_KEY` at [github.com/settings/codespaces](https://github.com/settings/codespaces)
     (**New secret**, choose this repository), then restart the codespace. GitHub may also offer it as a
     recommended secret when you create the codespace.

How your key is kept safe:
- **It stays in your GitHub account.** GitHub stores Codespaces secrets encrypted and passes them only to
  your own codespaces, as an environment variable.
- **We never see it.** benchscale has no server of its own, and the key goes only from your codespace to
  Anthropic.
- **Usage is billed to your Anthropic account**, at standard API rates.
- **The codespace is yours.** Stop or delete it when you are done. GitHub's free monthly allowance for
  personal accounts covers light use.

## Command line only

```bash
.venv/bin/benchscale refs falcon 50                       # search the reference library
.venv/bin/benchscale template shake_fill_rack             # parameters, units and limits
.venv/bin/benchscale design shake_fill_rack -p rows=3 -p cols=4 -p hole_step=0.3
.venv/bin/benchscale serve                                # http://localhost:8742
```

## Troubleshooting

- **"requires a different Python" or "editable mode requires setuptools"**: your Python is too old. Use the
  uv steps above.
- **Claude can't start benchscale**: use the full path to `.venv/bin/benchscale` in the config. Claude
  Desktop does not see your shell's PATH.
- **No network**: set `BENCHSCALE_OFFLINE=1`. The library then holds only the cited standards and your
  own measurements.
- **`benchscale bases` can't render**: rendering the Prompt to Bench base models needs
  [OpenSCAD](https://openscad.org). Listing them does not.

