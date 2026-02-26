# GTK Signage

A lightweight digital signage system combining a fullscreen GTK display with a Flask-powered admin interface. Designed primarily for Raspberry Pi kiosks, menu boards, and in-store displays, with **local caching**, **offline resilience**, and **simple lifecycle management**.

GTK Signage is distributed as a **Flatpak application** and managed using straightforward install, update, and uninstall scripts.

---

## Features

* **Web Admin Interface**
  Add, edit, and delete slides via a browser

* **Flexible Display**
  Show web pages or uploaded images

* **Scheduling Support**
  Control slide visibility with start/end timestamps

* **Secure Access**
  Password-protected admin login with hashed credentials

* **Local Caching**
  Saves web content (HTML, JS, images, CSS) to survive internet outages

* **Minimal Display Stack**
  Fullscreen GTK WebView using WebKit (no Chromium)

* **Flatpak Distribution**
  Self-contained app with predictable dependencies

* **Auto-Start on Login**
  Uses standard XDG autostart (no systemd or shell hacks)

* **HTTPS Support**
  Optional self-signed SSL certs for the admin UI

* **HDMI-CEC Support**
  Optional scheduled and manual display power control on supported hardware

---

## Installation

### Files Required

You need **two files in the same directory**:

* `install.sh`
* `GtkSignage.flatpak`

Download the Flatpak bundle from:

```
https://github.com/mgroves/GtkSignage/releases
```

---

### Install

```bash
chmod +x install.sh
./install.sh
```

The installer will:

1. Ensure Flatpak is installed
2. Prompt for configuration values
3. Require and confirm an admin password
4. Write `config.ini` to a Flatpak-visible location
5. Install the local Flatpak bundle
6. Configure auto-start on login using XDG autostart
7. Optionally enable auto-login (highly recommended)

---

## Updating

To update GTK Signage using a new Flatpak bundle:

```bash
chmod +x update.sh
./update.sh
```

The update script will:

1. Verify the existing config
2. Back up `config.ini` with a timestamp
3. Apply any future config migrations (if present)
4. Optionally reinstall the Flatpak from a local bundle

Configuration is preserved.

---

## Uninstalling

```bash
chmod +x uninstall.sh
./uninstall.sh
```

The uninstall script will:

* Remove the autostart entry
* Uninstall the Flatpak
* Optionally remove all GTK Signage config and data
* Optionally remove auto-login

---

## Configuration

GTK Signage uses a **single INI config file**, written by `install.sh`.

Location:

```
~/.var/app/com.mgroves.GtkSignage/config/com.mgroves.GtkSignage/config.ini
```

You can find an example in `config.ini.example`

---

## Admin Interface

Once running, the admin UI is available at:

* HTTP: `http://<device-ip>:<port>/admin`
* HTTPS (if enabled): `https://<device-ip>:<port>/admin`

Log in using the credentials provided during installation.

---

## Slide Management

### Slide Properties

* **Source**: URL or uploaded image
* **Duration**: Display time in seconds
* **Start Time**: Optional scheduled start
* **End Time**: Optional scheduled end
* **Hide**: Temporarily disable without deleting

Slides are stored in `slides.json` under the configured data directory.

---

## Licensing

GTK Signage uses a **dual licensing model**:

* **Free** for small businesses with 1–2 physical locations
* **Commercial license required** for 3+ locations

See [LICENSE.md](LICENSE.md) for details.

---

## Support

* **Free support**: GitHub Issues
  [https://github.com/mgroves/GtkSignage/issues](https://github.com/mgroves/GtkSignage/issues). The CLA is "whenever I get around to it".

* **Commercial support**:
  [info@grovesmanagementllc.com](mailto:info@grovesmanagementllc.com). The CLA is negotiable.

---

## FAQ

**Q: Why not Chromium kiosk mode?**
A: Chromium is heavy and fragile for long-running signage. GTK WebView + WebKit is simpler and more predictable.

**Q: Why Python?**
A: GTK bindings made Python the path of least resistance, despite my dislike of Python.

**Q: Is this supported on Windows or macOS?**
A: No. Linux only, Raspberry Pi only.

**Q: Is there a roadmap?**
A: Yes. See [ROADMAP.md](ROADMAP.md).

