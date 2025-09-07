# backend/dsp/plotters.py
import matplotlib.pyplot as plt, numpy as np, librosa, pyloudnorm as pl

def plot_loudness_curve(path, out_png):
    y, sr = librosa.load(path, sr=None, mono=True)
    meter = pl.Meter(sr)
    win = int(sr*1.0); hop = win//2
    times, st = [], []
    for i in range(0, len(y)-win, hop):
        st.append(meter.integrated_loudness(y[i:i+win]))
        times.append(i/sr)
    plt.figure()
    plt.plot(times, st); plt.xlabel("Time (s)"); plt.ylabel("Short-term LUFS")
    plt.title("Loudness over time"); plt.tight_layout(); plt.savefig(out_png); plt.close()

def plot_freq_bars(user_props, ref_props, out_png, labels=("Low","Mid","High")):
    ind = np.arange(3); w=0.35
    plt.figure()
    plt.bar(ind, [user_props["low"],user_props["mid"],user_props["high"]], width=w, label="User")
    plt.bar(ind+w, [ref_props["low"],ref_props["mid"],ref_props["high"]], width=w, label="Reference")
    plt.xticks(ind+w/2, labels); plt.ylabel("Energy proportion")
    plt.legend(); plt.title("Frequency balance"); plt.tight_layout(); plt.savefig(out_png); plt.close()
