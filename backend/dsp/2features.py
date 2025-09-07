# backend/dsp/features.py
import librosa, numpy as np, pyloudnorm as pl, soundfile as sf
from scipy.stats import iqr

def load_audio(path, sr=48000, mono=False):
    y, sr = librosa.load(path, sr=sr, mono=mono)  # mono=False keeps stereo
    return y, sr

def lufs_values(path):
    y, sr = load_audio(path, mono=True)  # integrated is typically mono
    meter = pl.Meter(sr)
    integrated = meter.integrated_loudness(y)
    # short-term: 3s window; compute rolling
    frame = int(sr*3)
    st_vals = []
    for i in range(0, len(y)-frame, frame//2):
        st_vals.append(meter.integrated_loudness(y[i:i+frame]))
    return {"integrated": float(integrated),
            "short_term_mean": float(np.nanmean(st_vals)),
            "short_term_std": float(np.nanstd(st_vals))}

def dynamic_range(path):
    y, sr = load_audio(path, mono=True)
    win = int(0.4*sr); hop = win//2
    rms = librosa.feature.rms(y=y, frame_length=win, hop_length=hop, center=False)[0]
    peak = np.array([np.max(np.abs(y[i:i+win])) for i in range(0, len(y)-win, hop)])
    # add eps to avoid log(0)
    eps = 1e-9
    rms_db = 20*np.log10(rms+eps)
    peak_db = 20*np.log10(peak+eps)
    dr = peak_db - rms_db
    return {"dr_mean": float(np.mean(dr)), "dr_p25": float(np.percentile(dr,25)),
            "dr_p75": float(np.percentile(dr,75))}

def freq_balance(path):
    y, sr = load_audio(path, mono=True)
    S = np.abs(librosa.stft(y, n_fft=4096, hop_length=1024))**2
    freqs = librosa.fft_frequencies(sr=sr, n_fft=4096)
    bands = [(20,200), (200,5000), (5000,20000)]
    energy = []
    for lo, hi in bands:
        idx = np.where((freqs>=lo)&(freqs<hi))[0]
        energy.append(float(np.mean(S[idx,:])))
    total = sum(energy)+1e-9
    props = [e/total for e in energy]
    return {"low": props[0], "mid": props[1], "high": props[2]}

def stereo_width(path):
    y, sr = load_audio(path, mono=False)
    if y.ndim==1:  # mono file
        return {"rho_mean": 1.0, "rho_p10": 1.0, "rho_p90": 1.0}
    L, R = y[0], y[1]
    win = int(0.5*sr); hop = win//2
    rhos = []
    for i in range(0, len(L)-win, hop):
        segL, segR = L[i:i+win], R[i:i+win]
        if np.std(segL)<1e-6 or np.std(segR)<1e-6: 
            continue
        r = np.corrcoef(segL, segR)[0,1]
        rhos.append(np.clip(r, -1, 1))
    return {"rho_mean": float(np.mean(rhos)), "rho_p10": float(np.percentile(rhos,10)),
            "rho_p90": float(np.percentile(rhos,90))}

def tempo_and_drift(path):
    y, sr = load_audio(path, mono=True)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, units='time')
    if len(beats) < 4:
        return {"bpm": float(tempo), "drift_pct": None}
    intervals = np.diff(beats)
    drift = float(iqr(intervals) / (np.median(intervals)+1e-9) * 100.0)
    return {"bpm": float(tempo), "drift_pct": drift}

def extract_all(path):
    return {
        "loudness": lufs_values(path),
        "dynrange": dynamic_range(path),
        "freqbal":  freq_balance(path),
        "width":    stereo_width(path),
        "tempo":    tempo_and_drift(path)
    }
