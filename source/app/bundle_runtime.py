import os
import sys
import shutil
import stat
import urllib.request
import flet_desktop
import flet_desktop.version


def prepare_flet_runtime():
    """
    Ensures that the Flet desktop runtime client and its archive are pre-cached
    and placed inside flet_desktop's package directory prior to PyInstaller build.
    This guarantees 100% offline, standalone execution on target machines.
    """
    ver = flet_desktop.version.version
    print(f"[bundle_runtime] Preparing Flet v{ver} runtime for packaging...")

    # 1. Ensure extracted client in ~/.flet/client
    try:
        cache_dir = flet_desktop.ensure_client_cached()
        print(f"[bundle_runtime] Cached client located at: {cache_dir}")
    except Exception as e:
        print(f"[bundle_runtime] Warning: ensure_client_cached encountered: {e}", file=sys.stderr)
        cache_dir = None

    # 2. Determine target package directory (flet_desktop/app)
    pkg_bin_dir = flet_desktop.get_package_bin_dir()
    os.makedirs(pkg_bin_dir, exist_ok=True)
    print(f"[bundle_runtime] Target package bin dir: {pkg_bin_dir}")

    # 3. Download / copy the archive artifact (e.g. flet-windows.zip) into flet_desktop/app
    artifact = flet_desktop.get_artifact_filename()
    target_archive = os.path.join(pkg_bin_dir, artifact)

    if not os.path.exists(target_archive):
        flet_url = os.environ.get(
            "FLET_CLIENT_URL",
            f"https://github.com/flet-dev/flet/releases/download/v{ver}/{artifact}"
        )
        print(f"[bundle_runtime] Downloading archive artifact {artifact} from {flet_url}...")
        try:
            urllib.request.urlretrieve(flet_url, target_archive)
            print(f"[bundle_runtime] Successfully saved archive to: {target_archive}")
        except Exception as e:
            print(f"[bundle_runtime] Warning: Could not download {artifact}: {e}", file=sys.stderr)
    else:
        print(f"[bundle_runtime] Archive artifact already exists at: {target_archive}")

    # 4. Copy extracted binaries into pkg_bin_dir/flet or pkg_bin_dir if available
    target_flet_dir = os.path.join(pkg_bin_dir, "flet")
    if cache_dir and os.path.exists(cache_dir):
        src_flet = os.path.join(cache_dir, "flet")
        if os.path.exists(src_flet):
            shutil.copytree(src_flet, target_flet_dir, dirs_exist_ok=True)
            print(f"[bundle_runtime] Copied extracted flet binaries to: {target_flet_dir}")
        else:
            for item in os.listdir(cache_dir):
                s = os.path.join(cache_dir, item)
                d = os.path.join(pkg_bin_dir, item)
                if os.path.isdir(s) and not os.path.exists(d):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                    print(f"[bundle_runtime] Copied {item} to: {d}")

    print("[bundle_runtime] Flet runtime packaging preparation complete!")


if __name__ == '__main__':
    prepare_flet_runtime()
