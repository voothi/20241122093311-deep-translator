import argparse
import sys
import os
import json

def main():
    parser = argparse.ArgumentParser(description="Translate text using DeepL.")
    parser.add_argument('--text', type=str, required=True, help='Text to translate')
    parser.add_argument('--source', type=str, required=True, help='Source language code (e.g., en, fr)')
    parser.add_argument('--target', type=str, required=True, help='Target language code (e.g., en, fr)')
    parser.add_argument('--deepl-api-key', type=str, required=True, help='Your DeepL API key')
    parser.add_argument('--use-local-fork', action='store_true', help='Use local fork from config.json')

    # Resilience options
    parser.add_argument('--timeout', type=float, help='Timeout in seconds')
    parser.add_argument('--retries', type=int, help='Max number of retries (-1 for endless)')
    parser.add_argument('--retry-backoff', type=float, help='Retry backoff base in seconds')
    parser.add_argument('--max-total-time', type=float, help='Max total wall-clock time in seconds')
    parser.add_argument('--quiet', action='store_true', help='Suppress retry diagnostics on stderr')
    parser.add_argument('--plain', action='store_true', help='Echo one-line error to stdout on failure')

    args = parser.parse_args()

    # Load config.json
    config = {}
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except Exception:
            pass

    # Resolve configuration precedence
    try:
        # netTimeout
        raw_timeout = args.timeout if args.timeout is not None else config.get('netTimeout', 5)
        timeout = float(raw_timeout)
        if timeout <= 0:
            raise ValueError("Timeout must be a positive number.")

        # maxRetries
        raw_retries = args.retries if args.retries is not None else config.get('maxRetries', 2)
        if isinstance(raw_retries, float) and not raw_retries.is_integer():
            raise ValueError("Retries must be an integer.")
        max_retries = int(raw_retries)
        if max_retries < -1:
            raise ValueError("Retries must be >= -1.")

        # retryBackoff
        raw_backoff = args.retry_backoff if args.retry_backoff is not None else config.get('retryBackoff', 1.0)
        retry_backoff = float(raw_backoff)
        if retry_backoff <= 0:
            raise ValueError("Retry backoff must be a positive number.")

        # maxTotalTime
        raw_total_time = args.max_total_time if args.max_total_time is not None else config.get('maxTotalTime', None)
        if raw_total_time is not None:
            max_total_time = float(raw_total_time)
            if max_total_time <= 0:
                raise ValueError("Max total time must be a positive number.")
        else:
            max_total_time = None

        # retryDiagnostics
        retry_diagnostics = False if args.quiet else config.get('retryDiagnostics', True)

        # echoErrorsToStdout
        echo_errors_to_stdout = args.plain if args.plain else config.get('echoErrorsToStdout', False)

    except (ValueError, TypeError) as e:
        sys.stderr.write(f"Configuration Error: {str(e)}\n")
        sys.exit(1)

    if max_retries == -1 and max_total_time is None:
        sys.stderr.write("Warning: Endless retries configured without a max total time deadline. This could lead to infinite hangs.\n")

    # Set up path to local fork if requested
    if args.use_local_fork:
        fork_path = config.get('local_deep_translator_fork_path')
        if fork_path:
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), fork_path)))

    from deep_translator import DeeplTranslator

    # Observability callback
    def on_retry_cb(attempt, delay, reason):
        if retry_diagnostics:
            sys.stderr.write(f"Attempt {attempt} failed: {reason}. Retrying in {delay:.2f}s...\n")

    translator_kwargs = {
        "timeout": timeout,
        "max_retries": max_retries,
        "retry_backoff": retry_backoff,
        "max_total_time": max_total_time,
        "on_retry": on_retry_cb,
    }

    try:
        try:
            translator = DeeplTranslator(api_key=args.deepl_api_key, source=args.source, target=args.target, **translator_kwargs)
        except TypeError:
            translator = DeeplTranslator(api_key=args.deepl_api_key, source=args.source, target=args.target)

        result = translator.translate(args.text)
        print(result)

    except KeyboardInterrupt:
        sys.stderr.write("Translation interrupted by user.\n")
        sys.exit(130)
    except Exception as e:
        err_msg = str(e)
        sys.stderr.write(f"Error: {err_msg}\n")
        if echo_errors_to_stdout:
            sys.stdout.write(f"Error: {err_msg}\n")
        sys.exit(2)

if __name__ == "__main__":
    main()