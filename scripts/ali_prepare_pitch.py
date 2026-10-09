"""Build Ali's seven-slide PNG/PDF/PPTX pitch from verified existing evidence.

No inference, external services or additional dependencies. PPTX slides contain
the rendered page images; editable source is this script and the evidence data.
"""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

from matplotlib.patches import FancyBboxPatch
from reportlab.pdfgen import canvas as pdf_canvas

from ali_prepare_slides import (ACCENT, BG, FG, MUTED, ROOT, WARNING,
                                c2_metrics, canvas, comparison, failure,
                                image_panel, perception, text, plt)


def card(fig, box, label, body, *, color=ACCENT):
    x, y, w, h = box
    fig.add_artist(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012",
                                facecolor="#172437", edgecolor="#425671",
                                transform=fig.transFigure, zorder=0))
    text(fig, x + 0.018, y + h - 0.025, label, size=20, color=color)
    text(fig, x + 0.018, y + h - 0.095, body, size=16)


def save(fig, out, name):
    fig.savefig(out / name, facecolor=BG)
    plt.close(fig)


def problem(out):
    fig = canvas("Screenshot-dan qayda və vizual sübuta",
                 "AI Gaming · Rule-Aware Visual Regression · Ali + Celal · NeuroBridge.SI")
    text(fig, 0.05, 0.8, "Hər fərq bug deyil.\nİtən obyekt isə diqqət tələb edir.", size=29)
    image_panel(fig, [0.05, 0.25, 0.52, 0.42],
                ROOT / "docs/ali/a1_evidence/vr_4b921c5d_R1_vlm_input.png")
    card(fig, [0.62, 0.32, 0.31, 0.4], "QA-nın qərarı üçün", "01   Nə dəyişib?\n\n02   Hansı qayda tətbiq olunur?\n\n03   Sübut haradadır?")
    text(fig, 0.05, 0.18,
         "İstifadəçi screenshot pair + allow/deny rules verir.\n"
         "Prototype region crop, qərar səbəbi və paylaşılacaq evidence ZIP yaradır.", size=19, color=ACCENT)
    text(fig, 0.05, 0.075,
         "Real benchmark crop · VideoGameQA-Bench, CC BY 4.0 · PRERECORDED evidence\n"
         "Vaxt qənaəti və QA workload azalması hələ ölçülməyib.", size=12, color=MUTED)
    save(fig, out, "01_problem.png")


def flow(out):
    fig = canvas("Model müşahidə edir. Kod qərar verir.",
                 "Frozen DINOv2 + pixel proposals → two-stage VLM → whole-scene audit → deterministic policy")
    cards = [
        ("01 / INPUT", "Reference + candidate\n\nAllow / deny rules\n\nValidation + alignment"),
        ("02 / LOCALIZE", "Frozen DINOv2 ViT-S/14\n\nPixel diff ilə regionlar\n\nEyni koordinatda crops"),
        ("03 / OBSERVE", "VLM dəyişikliyi təsvir edir\n\nSonra rules ilə verdict\n\nWhole-scene audit"),
        ("04 / DECIDE", "PASS / FAIL / REVIEW\n\nReason + rule ID + crop\n\nZIP + reference history"),
    ]
    for i, (label, body) in enumerate(cards):
        x = 0.05 + i * 0.235
        card(fig, [x, 0.41, 0.205, 0.37], label, body)
        if i < 3:
            text(fig, x + 0.215, 0.6, "→", size=23, color=ACCENT)
    text(fig, 0.05, 0.31,
         "Reliable forbidden evidence → FAIL\n"
         "Uncertainty, error və incomplete coverage → REVIEW", size=23, color=ACCENT)
    text(fig, 0.05, 0.14,
         "Inference only: training / fine-tuning yoxdur. Labels inference input-a daxil edilmir.\n"
         "PASS bütün mümkün bug-ların yoxluğuna zəmanət vermir.\n"
         "Final source SHA 79a0ef7 · OpenRouter / google/gemini-3.5-flash · low · prompt v9",
         size=14, color=MUTED)
    save(fig, out, "02_flow.png")


def barrel(out, data):
    run_id = data["arms"]["C"]["run_ids"]["vr_4b921c5d"]
    fig = canvas("Real bug: barrel yox olub → FAIL",
                 "C2 saved result · vr_4b921c5d · reliable forbidden region R1 + scene audit · D1")
    image_panel(fig, [0.05, 0.28, 0.5, 0.52],
                ROOT / "docs/ali/a1_evidence/vr_4b921c5d_R1_vlm_input.png")
    card(fig, [0.61, 0.57, 0.32, 0.21], "Gemini / FAIL", "Missing barrel · R1 / D1\nValidated visual evidence", color="#ff928f")
    card(fig, [0.61, 0.31, 0.32, 0.2], "Qwen baseline / REVIEW", "Eyni pair: “texture / lighting”\nRegion verdict uncertain", color=WARNING)
    text(fig, 0.05, 0.225,
         f"C2 run {run_id} · config {data['c_config_hash']}\n"
         "4 fresh calls · orchestration wall 31.520 s · pipeline 30.2167 s", size=17, color=ACCENT)
    text(fig, 0.05, 0.125,
         "Bu kadr actual model-input crop-dur; UI screenshot deyil. Nəticə committed raw row-dan göstərilir.\n"
         "Bir seçilmiş dev demo accuracy sübutu deyil; replay live inference kimi göstərilmir.\n"
         "Mənbə: docs/c2_openrouter/C_predictions.jsonl @79a0ef7; a1_evidence/; C2_RECOMPUTED.json.",
         size=13, color=MUTED)
    save(fig, out, "03_barrel.png")


def evidence(out, data):
    fig = canvas("Qərardan paylaşılacaq evidence paketinə",
                 "Evidence JSON + Markdown report + input hashes + paired crops + exact runtime identity")
    card(fig, [0.05, 0.28, 0.38, 0.48], "REPORT ZIP", "report.md\nanalysis.json\nevidence.json\nrules.yaml\nimages/\ncrops/\ndiagnostics/")
    card(fig, [0.5, 0.51, 0.43, 0.25], "Təkrarlana bilən evidence", "Run ID + rule ID + model / prompt\nInput və crop SHA-256\nAssessed / NOT assessed scope")
    card(fig, [0.5, 0.24, 0.43, 0.2], "Explicit reference approval", "İnsan təsdiqi + versioned history\nFAIL / REVIEW override guard")
    text(fig, 0.05, 0.17,
         f'{data["tests"]["passed"]} tests passed / {data["tests"]["skipped"]} skipped at source SHA 79a0ef7 · offline verification\n'
         "3 local Qwen ZIP yoxlanıb; 12 C2 ZIP üçün Celalın verification records-u var.\n"
         "C2 ZIP bytes transfer-i və final browser download check hələ gözlənir.", size=16, color=ACCENT)
    text(fig, 0.05, 0.065,
         "Native cache field unknown (replay possible); C2 freshness ayrıca 80 call/stage record ilə yoxlanıb.\n"
         "Bu səhifə evidence schema təqdimatıdır; final UI recording deyil.", size=12, color=MUTED)
    save(fig, out, "06_evidence.png")


def next_step(out, data):
    fig = canvas("Növbəti pilot: perception və yoxlama scope-u",
                 "İşləyən prototype + ölçülmüş development evidence + görünən failure")
    cards = [
        ("MODEL", "Daha güclü VLM ilə\nbarrel və booth FAIL alıb.\n\nPedestal hələ yanlış PASS.\nClean PASS: 0/7."),
        ("EVIDENCE", "B+C: 80 fresh calls\n0 retries\n\nProvider-reported total:\n$0.2871945\nEyni 12 pair, iki arm"),
        ("NEXT", "Fresh pre-labelled scenes\nAyrı label raters\n\nDINO ablation\nQA evidence-review vaxtı"),
    ]
    for i, (label, body) in enumerate(cards):
        card(fig, [0.05 + i * 0.31, 0.37, 0.275, 0.4], label, body)
    text(fig, 0.05, 0.28,
         "QA üçün qayda, crop və traceable qərar.\n"
         "Unknown halları human review-a verən screenshot comparison prototype.", size=23, color=ACCENT)
    text(fig, 0.05, 0.145,
         "Dev12 held-out deyil. Labels A1 başlayandan sonra dondurulub; 4/5 bug label assistant təklifi + Ali təsdiqidir.\n"
         "Source / class imbalance var. DINOv2 advantage və QA workload reduction ölçülməyib.\n"
         f'Frozen runtime: {data["model"]} / {data["reasoning_effort"]} / {data["prompt_version"]} / {data["c_config_hash"]}\n'
         "VideoGameQA-Bench · CC BY 4.0 · revision 2afbfdcc… · Ali + Celal",
         size=13, color=MUTED)
    save(fig, out, "07_next.png")


def write_pdf(images, path):
    pdf = pdf_canvas.Canvas(str(path), pagesize=(960, 540))
    pdf.setTitle("AI Gaming — Rule-Aware Visual Regression")
    pdf.setAuthor("Ali + Celal")
    for image in images:
        pdf.drawImage(str(image), 0, 0, width=960, height=540)
        pdf.showPage()
    pdf.save()


def write_pptx(images, path):
    """Package rendered slides as a portable Open XML deck without new installs."""
    a = "http://schemas.openxmlformats.org/drawingml/2006/main"
    p = "http://schemas.openxmlformats.org/presentationml/2006/main"
    r = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    def rels(items):
        return f'<Relationships xmlns="{rel_ns}">' + "".join(
            f'<Relationship Id="{rid}" Type="{r}/{kind}" Target="{target}"/>'
            for rid, kind, target in items) + "</Relationships>"
    group = '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>'
    files = {}
    types = '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'
    for part, suffix in [("presentation.xml", "presentation"), ("slideMasters/slideMaster1.xml", "slideMaster"), ("slideLayouts/slideLayout1.xml", "slideLayout"), ("theme/theme1.xml", "theme")]:
        types += f'<Override PartName="/ppt/{part}" ContentType="application/vnd.openxmlformats-officedocument.{"theme+xml" if suffix == "theme" else "presentationml." + suffix + "+xml"}"/>'
    for i in range(1, len(images) + 1):
        types += f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
    files["[Content_Types].xml"] = types + "</Types>"
    files["_rels/.rels"] = rels([("rId1", "officeDocument", "ppt/presentation.xml")])
    ids = "".join(f'<p:sldId id="{255+i}" r:id="rId{i+1}"/>' for i in range(1, len(images)+1))
    files["ppt/presentation.xml"] = f'<p:presentation xmlns:a="{a}" xmlns:r="{r}" xmlns:p="{p}"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:sldIdLst>{ids}</p:sldIdLst><p:sldSz cx="12192000" cy="6858000" type="screen16x9"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>'
    files["ppt/_rels/presentation.xml.rels"] = rels([("rId1", "slideMaster", "slideMasters/slideMaster1.xml")] + [(f"rId{i+1}", "slide", f"slides/slide{i}.xml") for i in range(1,len(images)+1)])
    cmap = 'accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" bg1="lt1" bg2="lt2" folHlink="folHlink" hlink="hlink" tx1="dk1" tx2="dk2"'
    files["ppt/slideMasters/slideMaster1.xml"] = f'<p:sldMaster xmlns:a="{a}" xmlns:r="{r}" xmlns:p="{p}"><p:cSld><p:spTree>{group}</p:spTree></p:cSld><p:clrMap {cmap}/><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>'
    files["ppt/slideMasters/_rels/slideMaster1.xml.rels"] = rels([("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml"), ("rId2", "theme", "../theme/theme1.xml")])
    files["ppt/slideLayouts/slideLayout1.xml"] = f'<p:sldLayout xmlns:a="{a}" xmlns:r="{r}" xmlns:p="{p}" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree>{group}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>'
    files["ppt/slideLayouts/_rels/slideLayout1.xml.rels"] = rels([("rId1", "slideMaster", "../slideMasters/slideMaster1.xml")])
    colors = {"dk1":"101826", "lt1":"FFFFFF", "dk2":"172437", "lt2":"F2F5FA", "accent1":"6EE7CF", "accent2":"FFC978", "accent3":"FF928F", "accent4":"B3C1D3", "accent5":"425671", "accent6":"23334A", "hlink":"6EE7CF", "folHlink":"FFC978"}
    color_xml = "".join(f'<a:{key}><a:srgbClr val="{value}"/></a:{key}>' for key,value in colors.items())
    fill = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    line = f'<a:ln w="9525">{fill}<a:prstDash val="solid"/></a:ln>'
    files["ppt/theme/theme1.xml"] = f'<a:theme xmlns:a="{a}" name="GameQA"><a:themeElements><a:clrScheme name="GameQA">{color_xml}</a:clrScheme><a:fontScheme name="GameQA"><a:majorFont><a:latin typeface="DejaVu Sans"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont><a:minorFont><a:latin typeface="DejaVu Sans"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme><a:fmtScheme name="GameQA"><a:fillStyleLst>{fill*3}</a:fillStyleLst><a:lnStyleLst>{line*3}</a:lnStyleLst><a:effectStyleLst>{"<a:effectStyle><a:effectLst/></a:effectStyle>"*3}</a:effectStyleLst><a:bgFillStyleLst>{fill*3}</a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, value in files.items():
            archive.writestr(name, '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + value)
        for i, image in enumerate(images, 1):
            pic = '<p:pic><p:nvPicPr><p:cNvPr id="2" name="Evidence slide"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="rId2"/><a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="12192000" cy="6858000"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>'
            archive.writestr(f"ppt/slides/slide{i}.xml", f'<p:sld xmlns:a="{a}" xmlns:r="{r}" xmlns:p="{p}"><p:cSld><p:spTree>{group}{pic}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')
            archive.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", rels([("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml"), ("rId2", "image", f"../media/slide{i}.png")]))
            archive.write(image, f"ppt/media/slide{i}.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=ROOT / "docs/ali/pitch")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    data = c2_metrics()
    science = ROOT / "docs/ali/slides"
    science.mkdir(parents=True, exist_ok=True)
    comparison(science)
    perception(science)
    failure(science)
    problem(args.out)
    flow(args.out)
    barrel(args.out, data)
    shutil.copyfile(science / "01_comparison.png", args.out / "04_results.png")
    shutil.copyfile(science / "03_pedestal_failure.png", args.out / "05_failure.png")
    evidence(args.out, data)
    next_step(args.out, data)
    images = [args.out / name for name in ["01_problem.png", "02_flow.png", "03_barrel.png", "04_results.png", "05_failure.png", "06_evidence.png", "07_next.png"]]
    write_pdf(images, args.out / "AI_Gaming_Pitch.pdf")
    write_pptx(images, args.out / "AI_Gaming_Pitch.pptx")
    print(f"7 slides + PDF + image-based PPTX at {args.out}; source SHA {data['source_integration_sha']}")


if __name__ == "__main__":
    main()
