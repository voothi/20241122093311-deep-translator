20260209093752

# Update deep-translator for DeepL API Changes

## Request
The user reported an `AuthorizationException` when using the DeepL translator script. This is caused by recent breaking changes in the DeepL API (March 2025) which deprecated GET requests and the `auth_key` parameter in favor of header-based authentication.

The goal is to update the `deep-translator` utility to a version that supports the new DeepL API standards.

## Analytics
The error trace confirms the issue originates in `deep_translator.deepl` raising an `AuthorizationException`.
The linked GitHub issue (deep-translator#299) confirms that `deep-translator` versions prior to the fix use the deprecated method.
DeepL API documentation confirms the deprecation of GET requests for translation.

## Decisions
1.  Update `deep-translator` package in the virtual environment to the latest version.
2.  Verify the update fixes the issue (by checking the version or running a test if possible/safe).
3.  Update documentation to reflect the change.

## Implementation Details
1.  Attempted to upgrade `deep-translator` using pip. Verified that 1.11.4 is the latest version on PyPI (released 2023), which does not contain the fix for 2025 breaking changes.
2.  Manually patched `venv\Lib\site-packages\deep_translator\deepl.py` to:
    -   Use `requests.post` instead of `requests.get`.
    -   Pass parameters in `data` (form-data) instead of query params.
    -   Pass API key in `Authorization` header (`DeepL-Auth-Key <key>`) instead of query/body param.

    **Code Change:**
    ```python
    # deep_translator/deepl.py

    # ... inside translate method ...
            # Create the request parameters.
            translate_endpoint = "translate"
            headers = {
                "Authorization": f"DeepL-Auth-Key {self.api_key}"
            }
            data = {
                "source_lang": self._source,
                "target_lang": self._target,
                "text": text,
            }
            # Do the request and check the connection.
            try:
                response = requests.post(
                    self._base_url + translate_endpoint, data=data, headers=headers
                )
    # ...
    ```


5.  Added developer testing support:
    -   Created `config.json` with `local_deep_translator_fork_path` settings options.
    -   Updated scripts `translate_deepl.py`, `translate_google.py`, `translate_mymemory.py` to accept a `--use-local-fork` flag.
    -   Using the flag allows loading the library from a local path specified in config, facilitating testing of the manual fork without affecting default package usage.
