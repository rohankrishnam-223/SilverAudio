# backend/dsp/stems.py
import subprocess, tempfile, pathlib

def separate_demucs(in_path: str, out_dir: str) -> dict:
    outdir = pathlib.Path(out_dir); outdir.mkdir(parents=True, exist_ok=True)
    # call demucs via CLI for simplicity; for prod use python API
    subprocess.run([
        "demucs", "--two-stems", "vocals",  # for 4 stems: demucs -n mdx_extra_q
        "-o", str(outdir), in_path
    ], check=True)
    # find generated files; normalize names to {'vocals':..., 'drums':..., 'bass':..., 'other':..., 'mix':...}
    return discover_stems(outdir, in_path)
