# backend/main.py
from fastapi import FastAPI, UploadFile, BackgroundTasks
from pydantic import BaseModel
import uuid, os, json
'''from dsp.stems import separate_demucs
from dsp.features import extract_all
from dsp.compare import compare_all
from dsp.plotters import plot_loudness_curve, plot_freq_bars'''
# dsp is not a library but the audio input - digital signal processing code

app = FastAPI()

JOBS = {}  # {job_id: {"status": "queued|running|done|error", "result_path": "..."}}
TMP = "tmp"; os.makedirs(TMP, exist_ok=True)

class AnalyzeResponse(BaseModel):
    job_id: str

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(user_file: UploadFile, ref_file: UploadFile, bg: BackgroundTasks):
    job_id = str(uuid.uuid4()); path_user=f"{TMP}/{job_id}_user.{user_file.filename.split('.')[-1]}"
    path_ref  = f"{TMP}/{job_id}_ref.{ref_file .filename.split('.')[-1]}"
    with open(path_user,"wb") as f: f.write(await user_file.read())
    with open(path_ref ,"wb") as f: f.write(await ref_file.read())
    JOBS[job_id] = {"status":"queued"}
    bg.add_task(run_job, job_id, path_user, path_ref)
    return AnalyzeResponse(job_id=job_id)

@app.get("/status/{job_id}")
def status(job_id: str): return JOBS.get(job_id, {"status":"unknown"})

@app.get("/result/{job_id}")
def result(job_id: str):
    meta = JOBS.get(job_id)
    if not meta or "result_path" not in meta: return {"error":"not ready"}
    with open(meta["result_path"]) as f: return json.load(f)

def run_job(job_id, path_user, path_ref):
    try:
        JOBS[job_id]["status"]="running"
        u_stems = separate_demucs(path_user, f"{TMP}/{job_id}/user")
        r_stems = separate_demucs(path_ref , f"{TMP}/{job_id}/ref")
        # features: mix + 4 stems
        def pack(stems):
            out = {"mix": extract_all(stems.get("mix", path_user))}
            for k in ["vocals","drums","bass","other"]:
                if stems.get(k): out[k] = extract_all(stems[k])
            return out
        user_feats, ref_feats = pack(u_stems), pack(r_stems)
        recs = compare_all(user_feats, ref_feats)
        # plots
        plot_loudness_curve(u_stems.get("mix", path_user), f"{TMP}/{job_id}_loud_user.png")
        plot_loudness_curve(r_stems.get("mix", path_ref),  f"{TMP}/{job_id}_loud_ref.png")
        plot_freq_bars(user_feats["mix"]["freqbal"], ref_feats["mix"]["freqbal"], f"{TMP}/{job_id}_freqbars.png")
        # save JSON
        result = {"recs":recs, "user":user_feats, "ref":ref_feats,
                  "plots":{"loud_user":f"{TMP}/{job_id}_loud_user.png",
                           "loud_ref": f"{TMP}/{job_id}_loud_ref.png",
                           "freqbars": f"{TMP}/{job_id}_freqbars.png"}}
        outp = f"{TMP}/{job_id}.json"; open(outp,"w").write(json.dumps(result, indent=2))
        JOBS[job_id].update({"status":"done","result_path":outp})
    except Exception as e:
        JOBS[job_id] = {"status":"error","message":str(e)}
