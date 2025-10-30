## Steps from plugin
6) (Optional) Plugin mechanism for 3rd-party steps

Expose a setuptools “entry point” group so plugins can auto-register steps on import:
	•	Define a tiny loader that imports entry points (e.g., ragfine.steps_plugins).
	•	Plugins declare entry points in their own pyproject.toml.
	•	On import, your loader imports those modules → they call register_step(...).

This way, users pip install ragfine-foo-plugin and get new steps without touching your core.