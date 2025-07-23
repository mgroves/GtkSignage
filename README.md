# GTK Signage

A lightweight digital signage solution that combines a GTK-based display with a web-based management interface. Perfect for information displays, menu boards, and other digital signage needs.

## Features

- **Simple Web-Based Management**: Add, edit, and delete slides through an intuitive web interface
- **Flexible Content Display**: Show web pages, local images, or any content that can be rendered in a browser
- **Scheduling**: Set start and end times for each slide to control when content is displayed
- **Secure Admin Interface**: Password-protected admin console
- **Lightweight**: Minimal dependencies and system requirements
- **Easy Installation**: Simple installation script for Linux systems
- **SSL Support**: Optional HTTPS for secure admin access

## Requirements

### System Requirements
- Linux system with systemd
- Python 3
- GTK 3.0
- WebKit2

### Python Dependencies
- Flask
- Jinja2
- python-dotenv

## Installation

### Automatic Installation (Recommended)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/mgroves/GtkSignage/prod/install.sh)
```

The installation script will:
1. Install required system dependencies
2. Clone the repository to `/opt/gtk-signage`
3. Prompt for admin username and password
4. Configure Flask host and port
5. Optionally enable HTTPS with self-signed certificates
6. Set up a systemd service to run at boot

## Usage

### Accessing the Admin Interface

After installation, the admin interface is available at:
- HTTP: `http://<your-ip>:<port>/admin`
- HTTPS (if enabled): `https://<your-ip>:<port>/admin`

Log in with the username and password you provided during installation.

### Managing Slides

1. **Adding Slides**:
   - Click "Add Slide" in the admin interface
   - Enter a URL or upload a local image
   - Set the duration (in seconds)
   - Optionally set start and end times (leave both blank to always display)
   - Click "Save"

2. **Editing Slides**:
   - Click "Edit" next to the slide you want to modify
   - Update the slide properties
   - Click "Save"

3. **Deleting Slides**:
   - Click "Delete" next to the slide you want to remove
   - Confirm the deletion

### Slide Properties

- **Source**: URL or file path to display
- **Duration**: How long to display the slide (in seconds)
- **Start Time**: When the slide should start being displayed (optional)
- **End Time**: When the slide should stop being displayed (optional)
- **Hide**: Manually hide a slide without deleting it

## Configuration

GTK Signage is configured through environment variables, which can be set in the `.env` file:

- `ADMIN_USERNAME`: Username for the admin interface
- `ADMIN_PASSWORD`: Password for the admin interface
- `FLASK_SECRET_KEY`: Secret key for Flask sessions
- `FLASK_HOST`: Host to bind the Flask server (default: 0.0.0.0)
- `FLASK_PORT`: Port for the Flask server (default: 6969)
- `USE_SSL`: Enable HTTPS (true/false)

## Data Storage

Slides are stored in a JSON file (`slides.json`) in the following format:

```json
[
    {
        "source": "https://example.com/slide1",
        "duration": 10,
        "start": "2023-01-01T00:00:00",
        "end": "2023-12-31T23:59:59",
        "hide": false
    }
]
```

## License

GTK Signage is available under a dual licensing model:

- **Free for small businesses** operating in 1-2 physical locations
- **Commercial license required** for businesses with 3+ locations

For complete license terms and conditions, see [LICENSE.md](LICENSE.md).

## Support

GTK Signage offers different support options depending on your license:

- **Free Support**: Available through [GitHub issues](https://github.com/mgroves/GtkSignage/issues). No Service Level Agreement (SLA) is guaranteed for free support.
- **Commercial Support**: Users with commercial licenses may receive support with an SLA. Contact `info@grovesmanagementllc.com` for details.

### Contributing

Pull requests are welcome! If you'd like to contribute to GTK Signage, please see our [contribution guidelines](CONTRIBUTING.md) for more information.