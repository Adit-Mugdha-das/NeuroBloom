import pymupdf

doc = pymupdf.open(r"d:\NeuroBloom\Paper_Materials\figure1_clinical_problem_workflow.pdf")
page = doc[0]
mat = pymupdf.Matrix(3, 3)  # 3x zoom ≈ 216 DPI for crisp output
pix = page.get_pixmap(matrix=mat, alpha=False)
out = r"d:\NeuroBloom\Paper_Materials\figure1_clinical_problem_workflow.png"
pix.save(out)
print(f"Saved {out}  ({pix.width} x {pix.height} px)")
