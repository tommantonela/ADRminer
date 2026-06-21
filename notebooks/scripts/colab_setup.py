#!/usr/bin/env python3
"""
Prepare ADRMiner for execution in Google Colab.

The script performs the following tasks:

1. Reuses the current Python 3.11 runtime when available; otherwise installs it.
2. Registers Python 3.11 as the default only when the current runtime is not already 3.11.
3. Reuses the existing pip under Python 3.11, or installs it only when Python setup is required.
4. Clones or reuses the ADRMiner repository.
5. Checks out a requested branch, tag, or commit.
6. Optionally removes NumPy/pandas, then installs requirements.txt with Python 3.11.
7. Configures no LLM provider, OpenAI, or Ollama.
8. For Ollama: installs zstd and Ollama, starts the server, waits for readiness,
   pulls a model, and writes the OpenAI-compatible endpoint to .env.
9. Streams command output live to the Colab console.
10. Changes the current process to the repository's notebooks/ directory.

Important Colab note
--------------------
A running Jupyter kernel cannot replace its own Python interpreter. If the current
runtime is not already using Python 3.11, this script installs and configures Python
3.11 and installs the project dependencies for it, but you must restart the Colab
runtime once before executing the ADRMiner notebooks.

Recommended Colab usage:

    %run /content/colab_setup_py311.py \
        --provider ollama \
        --ollama-model qwen3:8b

By default, the script checks out the latest commit from the repository's
default branch. Use --repo-ref only when a specific branch, tag, or commit
is intentionally required.
"""

from __future__ import print_function

import argparse
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union


DEFAULT_REPOSITORY_URL = "https://github.com/tommantonela/ADRminer.git"
DEFAULT_REPOSITORY_DIR = Path("/content/ADRminer")

PYTHON_VERSION = "3.11"
PYTHON_EXECUTABLE = Path("/usr/bin/python3.11")
GET_PIP_PATH = Path("/tmp/get-pip.py")

DEFAULT_OLLAMA_HOST = "127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "qwen3:8b"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_OLLAMA_LOG = Path("/tmp/ollama-server.log")


CommandPart = Union[str, Path]


def run(
    command: Iterable[CommandPart],
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    """
    Run a command and stream its combined stdout/stderr to the notebook console.

    This keeps long-running commands such as pip, apt, git, and ollama visible
    while they execute.
    """
    command_list = [str(part) for part in command]
    print("$", " ".join(command_list), flush=True)

    process_env = os.environ.copy()
    if env:
        process_env.update(env)

    process_env.setdefault("PYTHONUNBUFFERED", "1")
    process_env.setdefault("PIP_PROGRESS_BAR", "on")

    process = subprocess.Popen(
        command_list,
        cwd=str(cwd) if cwd else None,
        env=process_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    output_lines: List[str] = []

    if process.stdout is not None:
        for line in process.stdout:
            print(line, end="", flush=True)
            output_lines.append(line)

    return_code = process.wait()
    stdout = "".join(output_lines)

    completed = subprocess.CompletedProcess(
        args=command_list,
        returncode=return_code,
        stdout=stdout,
        stderr=None,
    )

    if return_code != 0:
        raise subprocess.CalledProcessError(
            returncode=return_code,
            cmd=command_list,
            output=stdout,
        )

    return completed


def command_succeeds(command: Iterable[CommandPart]) -> bool:
    """Return True when a command exits successfully."""
    completed = subprocess.run(
        [str(part) for part in command],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        text=True,
    )
    return completed.returncode == 0


def install_python311(skip_python_setup: bool) -> Path:
    """
    Return a usable Python 3.11 interpreter, installing/configuring it only when needed.

    If the current notebook kernel already runs Python 3.11, the function reuses
    `sys.executable` and skips:

    - apt-based Python installation;
    - update-alternatives changes;
    - pip bootstrapping; and
    - pip/setuptools/wheel upgrades.

    All later package operations then use the tools already associated with the
    current Python 3.11 interpreter.
    """
    current_python = Path(sys.executable).resolve()
    current_is_python311 = (
        sys.version_info.major == 3
        and sys.version_info.minor == 11
    )

    if current_is_python311:
        print(
            "The current kernel already uses Python 3.11; "
            "reusing the existing interpreter and pip."
        )
        print("Current interpreter:", current_python)

        if not command_succeeds(
            [current_python, "-m", "pip", "--version"]
        ):
            raise RuntimeError(
                "The current kernel uses Python 3.11, but pip is not available "
                f"for {current_python}. Install pip manually or rerun in a "
                "runtime that includes pip."
            )

        pip_version = subprocess.check_output(
            [str(current_python), "-m", "pip", "--version"],
            text=True,
        ).strip()
        print("Existing pip:", pip_version)

        return current_python

    if skip_python_setup:
        if not PYTHON_EXECUTABLE.is_file():
            raise FileNotFoundError(
                "--skip-python-setup was used, but Python 3.11 was not found at "
                f"{PYTHON_EXECUTABLE}."
            )
        print("Skipping Python 3.11 installation and configuration.")
        return PYTHON_EXECUTABLE

    if not PYTHON_EXECUTABLE.is_file():
        print("Installing Python 3.11...")
        run(["apt-get", "update"])
        run(
            [
                "apt-get",
                "install",
                "-y",
                "python3.11",
                "python3.11-dev",
                "python3.11-venv",
                "curl",
                "zstd",
            ]
        )
    else:
        print(f"Python 3.11 is already installed at {PYTHON_EXECUTABLE}.")

    # Register Python 3.11 as the default command for /usr/bin/python3 and
    # /usr/bin/python. The running notebook kernel is unaffected until restart.
    print("Registering Python 3.11 as the system default...")
    run(
        [
            "update-alternatives",
            "--install",
            "/usr/bin/python3",
            "python3",
            PYTHON_EXECUTABLE,
            "311",
        ]
    )
    run(
        [
            "update-alternatives",
            "--set",
            "python3",
            PYTHON_EXECUTABLE,
        ]
    )
    run(
        [
            "update-alternatives",
            "--install",
            "/usr/bin/python",
            "python",
            PYTHON_EXECUTABLE,
            "311",
        ]
    )
    run(
        [
            "update-alternatives",
            "--set",
            "python",
            PYTHON_EXECUTABLE,
        ]
    )

    # Bootstrap pip specifically for Python 3.11. The Ubuntu python3-pip package
    # may target another interpreter, so get-pip.py is used as a reliable fallback.
    if not command_succeeds([PYTHON_EXECUTABLE, "-m", "pip", "--version"]):
        print("Installing pip for Python 3.11...")
        run(
            [
                "curl",
                "-fsSL",
                "https://bootstrap.pypa.io/get-pip.py",
                "-o",
                GET_PIP_PATH,
            ]
        )
        run([PYTHON_EXECUTABLE, GET_PIP_PATH])

    run(
        [
            PYTHON_EXECUTABLE,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
            "setuptools",
            "wheel",
        ]
    )

    version = subprocess.check_output(
        [str(PYTHON_EXECUTABLE), "--version"],
        text=True,
    ).strip()
    pip_version = subprocess.check_output(
        [str(PYTHON_EXECUTABLE), "-m", "pip", "--version"],
        text=True,
    ).strip()

    print("Configured interpreter:", version)
    print("Configured pip:", pip_version)

    return PYTHON_EXECUTABLE


def current_kernel_uses_python311() -> bool:
    """Return True when the running notebook kernel already uses Python 3.11."""
    return sys.version_info.major == 3 and sys.version_info.minor == 11


def get_remote_default_branch(repository_dir: Path) -> str:
    """Return the default branch advertised by origin."""
    run(
        ["git", "remote", "set-head", "origin", "--auto"],
        cwd=repository_dir,
    )

    result = subprocess.run(
        [
            "git",
            "symbolic-ref",
            "--short",
            "refs/remotes/origin/HEAD",
        ],
        cwd=str(repository_dir),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(
            "Could not determine the repository's default branch."
        )

    # Example output: origin/main
    return result.stdout.strip().split("/", 1)[1]


def clone_or_checkout_repository(
    repository_url: str,
    repository_dir: Path,
    repository_ref: str,
    update_existing: bool,
) -> None:
    """
    Clone ADRMiner or check out the requested revision.

    The special value ``latest`` selects the newest commit from the remote
    repository's default branch. Existing Colab clones are fetched and updated
    automatically in this mode.
    """
    use_latest = repository_ref.lower() == "latest"

    if not repository_dir.exists():
        repository_dir.parent.mkdir(parents=True, exist_ok=True)

        if use_latest:
            # Cloning without --branch follows the repository's default branch
            # and retrieves its latest commit.
            run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    repository_url,
                    repository_dir,
                ]
            )
        else:
            run(
                [
                    "git",
                    "clone",
                    "--branch",
                    repository_ref,
                    "--single-branch",
                    repository_url,
                    repository_dir,
                ]
            )
        return

    if not (repository_dir / ".git").exists():
        raise RuntimeError(
            f"{repository_dir} exists but is not a Git repository."
        )

    print(f"Reusing existing repository: {repository_dir}")

    if use_latest:
        # Always refresh an existing clone when "latest" was requested.
        run(["git", "fetch", "origin"], cwd=repository_dir)
        default_branch = get_remote_default_branch(repository_dir)

        run(["git", "checkout", default_branch], cwd=repository_dir)
        run(
            ["git", "pull", "--ff-only", "origin", default_branch],
            cwd=repository_dir,
        )

        current_commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repository_dir),
            text=True,
        ).strip()
        print(
            f"Using latest commit {current_commit} "
            f"from the default branch {default_branch!r}."
        )
        return

    if update_existing:
        run(["git", "fetch", "--all", "--tags"], cwd=repository_dir)

    checkout = subprocess.run(
        ["git", "checkout", repository_ref],
        cwd=str(repository_dir),
        text=True,
        capture_output=True,
        check=False,
    )
    if checkout.returncode != 0:
        raise RuntimeError(
            f"Could not check out {repository_ref!r}. "
            "Use --update-existing to fetch remote branches and tags.\n"
            + checkout.stderr.strip()
        )

    if update_existing:
        branch = subprocess.run(
            ["git", "symbolic-ref", "--short", "-q", "HEAD"],
            cwd=str(repository_dir),
            text=True,
            capture_output=True,
            check=False,
        )
        if branch.returncode == 0 and branch.stdout.strip():
            run(["git", "pull", "--ff-only"], cwd=repository_dir)


def install_requirements(
    repository_dir: Path,
    python_executable: Path,
    skip_requirements: bool,
    force_reinstall: bool,
    ignore_installed: bool,
    uninstall_numpy_pandas: bool,
) -> None:
    """
    Install the repository dependencies with Python 3.11 pip.

    `force_reinstall` is useful in Colab because the runtime includes many
    preinstalled packages. `ignore_installed` is stronger and should only be
    used when pip still refuses to replace an incompatible preinstalled package.
    """
    if skip_requirements:
        print("Skipping requirements installation.")
        return

    requirements = repository_dir / "requirements.txt"
    if not requirements.is_file():
        raise FileNotFoundError(
            f"requirements.txt was not found at {requirements}"
        )

    if uninstall_numpy_pandas:
        print(
            "Removing existing NumPy and pandas installations from "
            "the Python 3.11 environment..."
        )
        run(
            [
                python_executable,
                "-m",
                "pip",
                "uninstall",
                "-y",
                "numpy",
                "pandas",
            ]
        )

        # Confirm that neither package remains importable from this interpreter.
        check_code = (
            "import importlib.util; "
            "names=['numpy','pandas']; "
            "remaining=[name for name in names "
            "if importlib.util.find_spec(name) is not None]; "
            "print('Packages still discoverable after uninstall:', remaining)"
        )
        run([python_executable, "-c", check_code])

    install_command = [
        python_executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--no-cache-dir",
    ]

    if force_reinstall:
        install_command.append("--force-reinstall")

    if ignore_installed:
        install_command.append("--ignore-installed")

    install_command.extend(["-r", requirements])
    run(install_command)

    kernel_command = [
        python_executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        "--no-cache-dir",
    ]
    if force_reinstall:
        kernel_command.append("--force-reinstall")
    kernel_command.append("ipykernel")
    run(kernel_command)

    run(
        [
            python_executable,
            "-m",
            "ipykernel",
            "install",
            "--user",
            "--name",
            "adrminer-py311",
            "--display-name",
            "Python 3.11 (ADRMiner)",
        ]
    )

    verification_code = (
        "import importlib; "
        "names=['numpy','pandas']; "
        "print('Installed package versions:'); "
        "[print(f'  {name}: {importlib.import_module(name).__version__}') "
        "for name in names]"
    )
    run([python_executable, "-c", verification_code])


def update_env_file(path: Path, values: Dict[str, str]) -> None:
    """Update selected keys while preserving unrelated .env entries."""
    existing_lines = (
        path.read_text(encoding="utf-8").splitlines()
        if path.is_file()
        else []
    )

    managed_keys = set(values)
    retained_lines: List[str] = []

    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            retained_lines.append(line)
            continue

        key = stripped.split("=", 1)[0].strip()
        if key not in managed_keys:
            retained_lines.append(line)

    if retained_lines and retained_lines[-1].strip():
        retained_lines.append("")

    retained_lines.append("# Generated or updated by scripts/colab_setup.py")
    for key, value in values.items():
        if value:
            retained_lines.append(f"{key}={value}")

    path.write_text(
        "\n".join(retained_lines).rstrip() + "\n",
        encoding="utf-8",
    )
    print(f"Updated environment configuration: {path}")


def read_colab_secret(name: str) -> Optional[str]:
    """Read a value from the Colab Secrets panel when available."""
    try:
        from google.colab import userdata  # type: ignore

        value = userdata.get(name)
        return value if value else None
    except Exception:
        return None


def configure_openai(repository_dir: Path, model_name: str) -> None:
    """Configure OpenAI from the environment or Colab Secrets."""
    api_key = os.getenv("OPENAI_API_KEY") or read_colab_secret(
        "OPENAI_API_KEY"
    )
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY was not found. Add it to Colab Secrets "
            "or define it in the environment."
        )

    os.environ["LLM_PROVIDER"] = "openai"
    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_MODEL_NAME"] = model_name

    update_env_file(
        repository_dir / ".env",
        {
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": api_key,
            "OPENAI_MODEL_NAME": model_name,
        },
    )

    print(f"Configured OpenAI model: {model_name}")


def ollama_is_ready(api_url: str) -> bool:
    """Return True when the local Ollama API responds."""
    try:
        with urllib.request.urlopen(
            f"{api_url}/api/version",
            timeout=3,
        ) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def ensure_system_packages(packages: List[str]) -> None:
    """Install missing Debian/Ubuntu system packages."""
    missing = [
        package
        for package in packages
        if shutil.which(package) is None
    ]

    if not missing:
        print(
            "Required system packages are already available: "
            + ", ".join(packages)
        )
        return

    print("Installing required system packages:", ", ".join(missing))
    run(["apt-get", "update"])
    run(["apt-get", "install", "-y", *missing])


def install_ollama(skip_install: bool) -> None:
    """Install Ollama through its Linux installation script."""
    if shutil.which("ollama"):
        print("Ollama is already installed.")
        return

    if skip_install:
        raise RuntimeError(
            "Ollama is not installed and --skip-ollama-install was used."
        )

    # The Ollama installer requires zstd to extract its distribution archive.
    # This check is also performed when Python setup was skipped.
    ensure_system_packages(["curl", "zstd"])

    print("Installing Ollama...")
    run(
        [
            "bash",
            "-lc",
            "curl -fsSL https://ollama.com/install.sh | sh",
        ]
    )

    if not shutil.which("ollama"):
        raise RuntimeError(
            "The installer completed but 'ollama' is not on PATH."
        )


def start_ollama_server(
    host: str,
    log_path: Path,
    startup_timeout: int,
) -> Optional[subprocess.Popen]:
    """Start Ollama in the background unless it is already running."""
    api_url = f"http://{host}"

    if ollama_is_ready(api_url):
        print(f"Ollama is already responding at {api_url}.")
        return None

    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_path.open("w", encoding="utf-8")

    server_env = os.environ.copy()
    server_env["OLLAMA_HOST"] = host
    server_env.setdefault("OLLAMA_NUM_PARALLEL", "1")

    print(f"Starting Ollama; logs: {log_path}")
    process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        env=server_env,
        start_new_session=True,
        text=True,
    )

    deadline = time.time() + startup_timeout
    while time.time() < deadline:
        if ollama_is_ready(api_url):
            print(f"Ollama is ready at {api_url}.")
            return process

        if process.poll() is not None:
            log_handle.flush()
            raise RuntimeError(
                f"Ollama stopped during startup. Inspect {log_path}."
            )

        time.sleep(2)

    raise TimeoutError(
        f"Ollama did not become ready within {startup_timeout} seconds. "
        f"Inspect {log_path}."
    )


def configure_ollama(
    repository_dir: Path,
    model_name: str,
    host: str,
    log_path: Path,
    startup_timeout: int,
    skip_install: bool,
    skip_pull: bool,
) -> None:
    """Install, start, and configure Ollama for ADRMiner."""
    install_ollama(skip_install=skip_install)
    start_ollama_server(
        host=host,
        log_path=log_path,
        startup_timeout=startup_timeout,
    )

    if skip_pull:
        print(f"Skipping model pull: {model_name}")
    else:
        run(["ollama", "pull", model_name])

    base_url = f"http://{host}/v1"

    os.environ["LLM_PROVIDER"] = "ollama"
    os.environ["OLLAMA_MODEL_NAME"] = model_name
    os.environ["OLLAMA_BASE_URL"] = base_url
    os.environ["OLLAMA_API_KEY"] = "ollama"
    os.environ.setdefault("PARALLEL_CLASSIFICATION", "false")

    update_env_file(
        repository_dir / ".env",
        {
            "LLM_PROVIDER": "ollama",
            "OLLAMA_MODEL_NAME": model_name,
            "OLLAMA_BASE_URL": base_url,
            "OLLAMA_API_KEY": "ollama",
            "PARALLEL_CLASSIFICATION": "false",
        },
    )

    print(f"Configured Ollama model: {model_name}")
    print(f"OpenAI-compatible endpoint: {base_url}")


def configure_no_provider(repository_dir: Path) -> None:
    """Configure workflows that do not require an LLM provider."""
    os.environ["LLM_PROVIDER"] = "none"
    update_env_file(
        repository_dir / ".env",
        {"LLM_PROVIDER": "none"},
    )
    print("No LLM provider configured.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare ADRMiner for Google Colab with Python 3.11."
    )

    parser.add_argument(
        "--repo-url",
        default=DEFAULT_REPOSITORY_URL,
    )
    parser.add_argument(
        "--repo-dir",
        type=Path,
        default=DEFAULT_REPOSITORY_DIR,
    )
    parser.add_argument(
        "--repo-ref",
        default="latest",
        help=(
            "Revision to use. The default value 'latest' selects the newest "
            "commit from the repository's default branch. A branch, tag, or "
            "commit hash can also be provided explicitly."
        ),
    )
    parser.add_argument(
        "--update-existing",
        action="store_true",
    )
    parser.add_argument(
        "--skip-python-setup",
        action="store_true",
        help=(
            "Do not install or configure Python 3.11. This is usually unnecessary "
            "when the current kernel already runs Python 3.11, because setup is "
            "skipped automatically in that case."
        ),
    )
    parser.add_argument(
        "--skip-requirements",
        action="store_true",
    )
    parser.add_argument(
        "--force-reinstall-requirements",
        action="store_true",
        help=(
            "Reinstall every package from requirements.txt even when pip "
            "considers it already installed."
        ),
    )
    parser.add_argument(
        "--ignore-installed",
        action="store_true",
        help=(
            "Ignore all currently installed packages when resolving requirements. "
            "Use only when --force-reinstall-requirements is insufficient."
        ),
    )
    parser.add_argument(
        "--uninstall-numpy-pandas",
        action="store_true",
        help=(
            "Uninstall NumPy and pandas from the Python 3.11 environment "
            "before installing requirements.txt."
        ),
    )
    parser.add_argument(
        "--provider",
        choices=("none", "openai", "ollama"),
        default="none",
    )
    parser.add_argument(
        "--openai-model",
        default=DEFAULT_OPENAI_MODEL,
    )
    parser.add_argument(
        "--ollama-model",
        default=DEFAULT_OLLAMA_MODEL,
    )
    parser.add_argument(
        "--ollama-host",
        default=DEFAULT_OLLAMA_HOST,
    )
    parser.add_argument(
        "--ollama-log",
        type=Path,
        default=DEFAULT_OLLAMA_LOG,
    )
    parser.add_argument(
        "--ollama-startup-timeout",
        type=int,
        default=120,
    )
    parser.add_argument(
        "--skip-ollama-install",
        action="store_true",
    )
    parser.add_argument(
        "--skip-ollama-pull",
        action="store_true",
    )
    parser.add_argument(
        "--no-chdir",
        action="store_true",
    )

    return parser.parse_args()


def fix_colab():
    run(
        [
            PYTHON_EXECUTABLE,
            "-m",
            "pip",
            "install",
            "ipykernel==6.17.1",
            "ipython==7.34.0",
            "requests==2.32.3",
            "tornado==6.4.2",
        ]
    )
    
    run(
        [
            PYTHON_EXECUTABLE,
            "-m",
            "pip",
            "uninstall",
            "-y",
            "torch",
            "torchvision",
            "torchaudio",
        ]
    )
    
    run(
        [
            PYTHON_EXECUTABLE,
            "-m",
            "pip",
            "install",
            "torch==2.6.0+cu124",
            "torchvision==0.21.0+cu124",
            "torchaudio==2.6.0+cu124",
            "--index-url",
            "https://download.pytorch.org/whl/cu124"
        ]
    )

    pass

def main() -> None:
    args = parse_args()
    repository_dir = args.repo_dir.expanduser().resolve()

    print("=== ADRMiner Colab setup ===")
    print("Current kernel:", sys.version.replace("\n", " "))
    print("Repository:", args.repo_url)
    print("Requested revision:", args.repo_ref)
    print("Destination:", repository_dir)
    print("Provider:", args.provider)

    python_executable = install_python311(
        skip_python_setup=args.skip_python_setup
    )

    clone_or_checkout_repository(
        repository_url=args.repo_url,
        repository_dir=repository_dir,
        repository_ref=args.repo_ref,
        update_existing=args.update_existing,
    )

    install_requirements(
        repository_dir=repository_dir,
        python_executable=python_executable,
        skip_requirements=args.skip_requirements,
        force_reinstall=args.force_reinstall_requirements,
        ignore_installed=args.ignore_installed,
        uninstall_numpy_pandas=args.uninstall_numpy_pandas,
    )

    if args.provider == "openai":
        configure_openai(
            repository_dir=repository_dir,
            model_name=args.openai_model,
        )
    elif args.provider == "ollama":
        configure_ollama(
            repository_dir=repository_dir,
            model_name=args.ollama_model,
            host=args.ollama_host,
            log_path=args.ollama_log,
            startup_timeout=args.ollama_startup_timeout,
            skip_install=args.skip_ollama_install,
            skip_pull=args.skip_ollama_pull,
        )
    else:
        configure_no_provider(repository_dir)

    notebooks_dir = repository_dir / "notebooks"
    if not notebooks_dir.is_dir():
        raise FileNotFoundError(
            f"Notebook directory not found: {notebooks_dir}"
        )

    if not args.no_chdir:
        os.chdir(notebooks_dir)
        print("Working directory:", Path.cwd())

    if not args.skip_python_setup:
        fix_colab()
    print("\nSetup completed.")

    if current_kernel_uses_python311():
        print("The current notebook kernel is already using Python 3.11.")
    else:
        print(
            "\nACTION REQUIRED: the current notebook kernel is not Python 3.11.\n"
            "Restart the Colab runtime once, then rerun this setup script with:\n"
            "    --skip-python-setup --skip-requirements\n"
            "After the restart, verify the interpreter with:\n"
            "    import sys; print(sys.version)\n"
        )


if __name__ == "__main__":
    main()
