# GIMP 3.x Batch Mode on macOS

Hard-won knowledge from getting GIMP 3.0.8 Python-Fu batch mode working on macOS (Apple Silicon).

## The Problem

Running `gimp -n -i --batch-interpreter=python-fu-eval -b '...'` hangs indefinitely on macOS. GIMP launches, begins initializing plugins, and never reaches the batch command.

### Root Cause

The `file-rawtherapee` plugin (at `/Applications/GIMP.app/Contents/Resources/lib/gimp/3.0/plug-ins/file-rawtherapee/file-rawtherapee`) hangs during initialization. This blocks the entire GIMP startup sequence.

You cannot simply remove or rename the plugin because the macOS app bundle is code-signed — any modification triggers "Operation not permitted".

## The Solution

Three changes are required:

### 1. Use `gimp-console` instead of `gimp`

```bash
/Applications/GIMP.app/Contents/MacOS/gimp-console
```

The regular `gimp` binary tries to initialize as a macOS GUI application (even with `-i`), which causes additional macOS app lifecycle issues. `gimp-console` is specifically designed for non-GUI batch operations.

### 2. Create a filtered plugin directory

Create `~/Library/Application Support/GIMP/3.0/batch-plug-ins/` containing symlinks to all system plugins EXCEPT `file-rawtherapee`:

```bash
BATCH_PLUGINS="$HOME/Library/Application Support/GIMP/3.0/batch-plug-ins"
mkdir -p "$BATCH_PLUGINS"

SYS_PLUGINS="/Applications/GIMP.app/Contents/Resources/lib/gimp/3.0/plug-ins"

# Only link the plugins you need for batch processing
NEEDED_PLUGINS=(
    file-png file-jpeg file-tiff file-bmp file-webp
    file-gif-load file-gif-export
    python-console python-eval script-fu
)

for name in "${NEEDED_PLUGINS[@]}"; do
    [ -d "$SYS_PLUGINS/$name" ] && ln -sf "$SYS_PLUGINS/$name" "$BATCH_PLUGINS/$name"
done
```

**Tip**: Only link what you need. The full system has 122 plugins — loading all of them (even via symlinks) is slower and risks hitting other problematic plugins. The minimal set above covers JPEG/PNG/TIFF/BMP/WebP/GIF loading and Python-Fu/Script-Fu execution.

### 3. Create a batch-mode gimprc

Create `~/Library/Application Support/GIMP/3.0/batch-gimprc`:

```
# Minimal gimprc for batch mode — uses filtered plugin directory
(plug-in-path "${gimp_dir}/plug-ins:${gimp_dir}/batch-plug-ins")
```

This tells GIMP to load plugins from the user's `batch-plug-ins/` directory (with its filtered symlinks) instead of the system plugin directory.

## Working Command

```bash
LSBackgroundOnly=1 /Applications/GIMP.app/Contents/MacOS/gimp-console \
  -n -i --no-data --quit \
  --gimprc="$HOME/Library/Application Support/GIMP/3.0/batch-gimprc" \
  --batch-interpreter=python-fu-eval \
  -b "exec(open('/path/to/script.py').read())"
```

This exits cleanly with code 0. No `timeout` wrapper needed.

Flags explained:
- `LSBackgroundOnly=1` — macOS env var that suppresses the dock icon (prevents bouncing)
- `/Applications/GIMP.app/Contents/MacOS/gimp-console` — console binary, no GUI
- `-n` — new instance
- `-i` — headless (no user interface)
- `--no-data` — skip loading brushes, gradients, patterns (faster startup)
- `--quit` — exit cleanly after all batch commands complete
- `--gimprc=...` — use our filtered config (skips problematic plugins)
- `--batch-interpreter=python-fu-eval` — Python-Fu instead of Script-Fu
- `-b "exec(open('...').read())"` — execute external script file

**Important**: Do NOT call `Gimp.quit()` in your script — the `--quit` flag handles clean exit. Calling `Gimp.quit()` causes a race condition where GIMP terminates before the batch wrapper can collect the return value.

## GIMP 3.x Python API Differences

The GIMP 3.x (GObject Introspection) API differs significantly from GIMP 2.x:

| Operation | GIMP 2.x | GIMP 3.x |
|-----------|----------|----------|
| Get drawable | `image.get_active_drawable()` | `image.get_layers()[0]` |
| Get selected drawables | N/A | `image.get_selected_drawables()` |
| Get pixel | `drawable.get_pixel(x, y)` → `(num_channels, pixel)` | `drawable.get_pixel(x, y)` → `Gegl.Color` |
| Pixel RGBA | Manual unpacking | `color.get_rgba()` → named tuple with `.red`, `.green`, `.blue`, `.alpha` |
| Hue/saturation | `gimp_drawable_hue_saturation(drawable, range, ...)` | `drawable.hue_saturation(range, hue, light, sat, overlap)` |
| File load | `pdb.gimp_file_load(path, path)` | `Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, Gio.File.new_for_path(path))` |
| File save | `pdb.gimp_file_overwrite(...)` | `Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image, Gio.File.new_for_path(path))` |
| Desaturate | `pdb.gimp_desaturate_full(drawable, mode)` | `drawable.desaturate(Gimp.DesaturateMode.LUMINANCE)` |
| Curves spline | `pdb.gimp_curves_spline(drawable, ch, n, pts)` | `drawable.curves_spline(channel, [pts])` (no num_points arg) |
| Quit | `gimp.quit(0)` | Don't call — use `--quit` CLI flag instead |
| Python version | Python 2 + `execfile()` | Python 3 + `exec(open(...).read())` |

### Imports for GIMP 3.x scripts

```python
import gi
gi.require_version("Gimp", "3.0")
gi.require_version("Gegl", "0.4")
from gi.repository import Gimp, Gegl, GLib, Gio
```

## Performance Notes

- `drawable.get_pixel(x, y)` is slow when called in a tight Python loop. For dominant hue detection, sample ~1000 random pixels rather than scanning the full image grid.
- `--no-data` significantly reduces startup time by skipping brush/gradient/pattern loading.
- The minimal plugin set (10 plugins) loads much faster than all 122 system plugins.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| GIMP hangs on startup | Plugin initialization hang | Use `gimp-console` + `--no-data` + filtered `--gimprc` |
| "Operation not permitted" modifying app bundle | macOS code signing | Don't modify the app bundle; use symlinks in user config |
| GIMP icon bounces in dock | `gimp-console` registers with window server | Set `LSBackgroundOnly=1` env var before the command |
| GIMP launches in taskbar and crashes | GUI initialization on macOS | Use `gimp-console` instead of `gimp` |
| `get_active_drawable` AttributeError | GIMP 3.x API change | Use `image.get_layers()[0]` |
| Script runs but GIMP stays alive (EXIT 124) | GIMP runs as background daemon after batch | Use `--quit` flag — exits cleanly with code 0 |
| `Gimp.quit()` error: takes 0 arguments | GIMP 3.x API change | Don't call `Gimp.quit()` at all — use `--quit` flag instead |
| "Procedure 'python-fu-eval' returned no return values" | `Gimp.quit()` exits before batch wrapper can collect result | Don't call `Gimp.quit()` — use `--quit` flag |
| `DesaturateMode.LUMINOSITY` not found | GIMP 3.x enum rename | Use `DesaturateMode.LUMINANCE` |
| `curves_spline()` wrong arg count | GIMP 3.x removed num_points arg | Use `drawable.curves_spline(channel, [pts])` (2 args, not 3) |

## Linux

On Linux, standard GIMP batch mode works without these workarounds:

```bash
gimp -n -i --batch-interpreter=python-fu-eval \
  -b "exec(open('/path/to/script.py').read())" \
  -b '(gimp-quit 0)'
```

The second `-b '(gimp-quit 0)'` uses Script-Fu syntax to quit GIMP. This works on Linux because the `file-rawtherapee` plugin doesn't hang there.
