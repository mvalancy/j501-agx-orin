"""Write one 3MF per printable STL (already in print orientation), centred on a 256 mm P1S plate."""
from pathlib import Path
import json,zipfile,trimesh,numpy as np
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];E=R/'exports'
CT='<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
RELS='<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
def model(m,name):
    v=m.vertices-[*(m.bounds[0][:2]+m.bounds[1][:2])/2,m.bounds[0][2]]+[128,128,0]
    verts=''.join(f'<vertex x="{a:.4f}" y="{b:.4f}" z="{c:.4f}"/>' for a,b,c in v)
    tris=''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in m.faces)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
            f'<metadata name="Title">{name}</metadata><resources><object id="1" name="{name}" type="model"><mesh><vertices>{verts}</vertices>'
            f'<triangles>{tris}</triangles></mesh></object></resources><build><item objectid="1"/></build></model>')
names=list(json.loads((E/'geometry-checks.json').read_text()))
for n in names:
    m=trimesh.load_mesh(E/f'{n}.stl')
    with zipfile.ZipFile(E/f'{n}.3mf','w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',CT);z.writestr('_rels/.rels',RELS);z.writestr('3D/3dmodel.model',model(m,n))
    # Read the package back with a plain XML parser and confirm the mesh survived intact.
    ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    root=ET.fromstring(zipfile.ZipFile(E/f'{n}.3mf').read('3D/3dmodel.model'))
    v=np.array([[float(q.get(k)) for k in 'xyz'] for q in root.iterfind('.//m:vertex',ns)])
    f=np.array([[int(q.get(k)) for k in ('v1','v2','v3')] for q in root.iterfind('.//m:triangle',ns)])
    back=trimesh.Trimesh(v,f,process=False)
    assert len(f)==len(m.faces) and back.is_watertight and abs(back.volume-m.volume)<1e-3*abs(m.volume),n
print(len(names),'3MF files written')
