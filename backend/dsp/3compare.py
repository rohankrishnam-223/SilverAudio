# backend/dsp/compare.py
def diff(a,b): 
    return {k: (a[k]-b[k]) if isinstance(a[k], (int,float)) else None for k in a.keys() & b.keys()}

def recs_for_pair(user_mix, ref_mix):
    out = []
    # Loudness
    dl = user_mix["loudness"]["integrated"] - ref_mix["loudness"]["integrated"]
    if abs(dl) >= 2.0:
        if dl < 0: out.append(f"Your mix is ~{abs(dl):.1f} dB quieter than the reference. Raise overall level or reduce dynamic range before limiting.")
        else:      out.append(f"Your mix is ~{dl:.1f} dB louder than the reference. Consider easing limiting to regain dynamics.")
    # Dynamic range
    ddr = user_mix["dynrange"]["dr_mean"] - ref_mix["dynrange"]["dr_mean"]
    if ddr <= -1.5:
        out.append("Your mix is more compressed than the reference (lower crest). Back off bus compression or limiter.")
    # Freq balance
    for band,label in [("low","low end (20–200 Hz)"),("mid","mids (200 Hz–5 kHz)"),("high","highs (5–20 kHz)")]:
        d = user_mix["freqbal"][band] - ref_mix["freqbal"][band]
        if abs(d) >= 0.08:
            action = "reduce" if d>0 else "boost"
            out.append(f"Your {label} is {abs(d)*100:.0f}% {'higher' if d>0 else 'lower'} than the reference. Consider {action} EQ in that band.")
    # Stereo width
    drho = user_mix["width"]["rho_mean"] - ref_mix["width"]["rho_mean"]
    if abs(drho) >= 0.10:
        if drho > 0:
            out.append("Your stereo image is narrower than the reference. Add subtle stereo widening on pads/FX.")
        else:
            out.append("Your stereo image is wider than the reference. Ensure mono compatibility and check phase.")
    if user_mix["width"]["rho_p10"] < -0.05:
        out.append("Potential phase issues detected (negative L/R correlation). Check polarity or mid/side processing.")
    # Tempo drift (optional for songs)
    if user_mix["tempo"]["drift_pct"] is not None and ref_mix["tempo"]["drift_pct"] is not None:
        ddrift = user_mix["tempo"]["drift_pct"] - ref_mix["tempo"]["drift_pct"]
        if ddrift >= 5:
            out.append("Rhythm is less consistent than the reference. Tighten timing or quantize drums/bass.")
    return out[:6]  # keep it concise

def compare_all(user, ref):
    """user/ref are dicts keyed by stems: 'mix','vocals','drums','bass','other' → feature dicts"""
    summary = {"mix": recs_for_pair(user["mix"], ref["mix"])}
    for stem in ["vocals","drums","bass","other"]:
        if stem in user and stem in ref:
            r = recs_for_pair(user[stem], ref[stem])
            # make stem-specific text
            summary[stem] = [s.replace("mix","{stem}").replace("overall level","stem level") for s in r]
    return summary
