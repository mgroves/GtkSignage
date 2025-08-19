Things I still want to do:

* API so that a server can access/update content from 'peers'
  * Auto-discover on the same LAN would be cool
* Design
  * Improve CSS/layout
  * Make sure mobile works well
* Organization
  * Nav/hamburger menu
  * CEC management into its own page
* Status page
  * Stats about server, temperature, CPU load, free RAM, etc
  * Stats about software, uptime, etc
* Testing/hardening
  * Unit tests
  * Integration tests
* Name/logo
  * Use a better name, logo, website
* Docs
  * Create a real set of docs/website
* Flask message: "WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead."
  * Figure out if this is necessary
  * Figure out what to do about it
* Caching improvements
  * There's a window where a cached copy could expire after internet goes out
  * I would like to fallback on older version if possible
  * But seems like there will always be a window? Need to think about this more.
* Play music / sound option
  * A separate process kicked off by main
  * Uses uploaded MP3s? Or maybe some kind of streaming/playlist?
  * Plays sound over HDMI
  * Control volume? Via CEC? (probably not)