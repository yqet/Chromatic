from __future__ import annotations
import math
from io import BytesIO
from PIL import Image
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective
from recolor_engine import Chromatic_pil, find_texture, cached_minecraft_skin, detect_pack_version
from adapters import get_adapter

ARM_W, ARM_H = 64.0, 32.0
SKIN_W = 64.0
ARMOR_UV = {
    "head": [(8,8,16,16),(24,8,32,16),(8,0,16,8),(16,0,24,8),(0,8,8,16),(16,8,24,16)],
    "body": [(20,20,28,32),(32,20,40,32),(20,16,28,20),(28,16,36,20),(16,20,20,32),(28,20,32,32)],
    "leg": [(4,20,8,32),(12,20,16,32),(4,16,8,20),(8,16,12,20),(0,20,4,32),(8,20,12,32)],
    "arm": [(44,20,48,32),(52,20,56,32),(44,16,48,20),(48,16,52,20),(40,20,44,32),(48,20,52,32)],
}
SKIN_UV = {
    "head": [(8,8,16,16),(24,8,32,16),(8,0,16,8),(16,0,24,8),(0,8,8,16),(16,8,24,16)],
    "body": [(20,20,28,32),(32,20,40,32),(20,16,28,20),(28,16,36,20),(16,20,20,32),(28,20,32,32)],
    "right_arm": [(44,20,48,32),(52,20,56,32),(44,16,48,20),(48,16,52,20),(40,20,44,32),(48,20,52,32)],
    "left_arm": [(36,52,40,64),(44,52,48,64),(36,48,40,52),(40,48,44,52),(32,52,36,64),(40,52,44,64)],
    "right_leg": [(20,52,24,64),(28,52,32,64),(20,48,24,52),(24,48,28,52),(16,52,20,64),(24,52,28,64)],
    "left_leg": [(4,52,8,64),(12,52,16,64),(4,48,8,52),(8,48,12,52),(0,52,4,64),(8,52,12,64)],
}

class ArmorGL(QOpenGLWidget):
    def __init__(self, source, hue, saturation, value, selected, parent=None):
        super().__init__(parent)
        self.source=source; self.hue=hue; self.saturation=saturation; self.value=value
        self.selected=set(selected); self.rot_x=-8.0; self.rot_y=-18.0; self.zoom=-15.0
        self.last_pos=QPoint(); self.dragging=False; self.tex={}; self.skin_tex=None
        self.skin_model="classic"; self.skin_path=None; self.skin_h=64.0; self.skin_legacy=False
        self.version=detect_pack_version(source); self.adapter=get_adapter(self.version)
        self.walk_phase=0.0; self.walk_speed=0.0
        self.setMinimumSize(560,560); self.setFocusPolicy(Qt.StrongFocus)
        self.anim_timer=None

    def _find_adapter_texture(self, item_key):
        if self.adapter:
            for candidate in self.adapter.TARGETS.get(item_key, ()):
                p=find_texture(self.source,candidate)
                if p: return p
                p=find_texture(self.source,Path(candidate).name)
                if p: return p
        return None

    def _animate_walk(self):
        self.walk_phase += self.walk_speed
        if self.walk_phase > 6.283185307179586: self.walk_phase -= 6.283185307179586
        self.update()

    def initializeGL(self):
        glClearColor(0.055,0.06,0.065,1); glEnable(GL_DEPTH_TEST); glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_ALPHA_TEST); glAlphaFunc(GL_GREATER,0.02)
        # Minecraft-like fixed lighting: directional diffuse + ambient, without changing source textures.
        glEnable(GL_LIGHTING); glEnable(GL_LIGHT0); glEnable(GL_COLOR_MATERIAL)
        glLightfv(GL_LIGHT0, GL_POSITION, (2.5, 4.0, 5.0, 0.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.82, 0.82, 0.82, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.34, 0.34, 0.34, 1.0))
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        self._load_textures(); self._load_skin()

    def _load_textures(self):
        # Only build recolored armor layers when the corresponding armor item is selected.
        needs_l1 = bool(self.selected & {"diamond_helmet", "diamond_chestplate", "diamond_boots"})
        needs_l2 = "diamond_leggings" in self.selected
        if needs_l1:
            p=self._find_adapter_texture("diamond_chestplate")
            if p: self.tex["l1"]=self._upload(self._recolor(p))
        if needs_l2:
            p=self._find_adapter_texture("diamond_leggings")
            if p: self.tex["l2"]=self._upload(self._recolor(p))

    def _load_skin(self):
        self.skin_path,self.skin_model=cached_minecraft_skin("blinkzin")
        if not self.skin_path: return
        try:
            im=Image.open(self.skin_path).convert("RGBA")
            if im.size==(64,32): self.skin_h=32.0; self.skin_legacy=True
            elif im.size!=(64,64): im=im.resize((64,64),Image.Resampling.NEAREST); self.skin_h=64.0
            self.skin_tex=self._upload(im)
        except Exception: self.skin_tex=None

    def _recolor(self,path):
        return Chromatic_pil(Image.open(path).convert("RGBA"),self.hue,self.saturation,self.value)

    def _upload(self,im):
        raw=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes("raw","RGBA")
        tex=glGenTextures(1); glBindTexture(GL_TEXTURE_2D,tex)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST); glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE); glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,im.width,im.height,0,GL_RGBA,GL_UNSIGNED_BYTE,raw); return tex

    def resizeGL(self,w,h):
        glViewport(0,0,max(1,w),max(1,h)); glMatrixMode(GL_PROJECTION); glLoadIdentity(); gluPerspective(32.0,max(1,w)/max(1,h),0.1,100.0); glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT); glLoadIdentity(); glTranslatef(0,-3.8,self.zoom); glRotatef(self.rot_x,1,0,0); glRotatef(self.rot_y,0,1,0)
        slim=self.skin_model=="slim"; arm_half=0.375 if slim else 0.5; arm_center=1.0+arm_half
        # NPC is intentionally static. Keep the body pose stable for a clean texture preview.
        gait=0.0
        gait_op=0.0
        bob=0.0
        torso_sway=0.0
        torso_pitch=0.0
        forward_shift=0.0
        glTranslatef(0.0,0.0,0.0)
        if self.skin_tex:
            self._skin_part("head",0,7.0,0,1,1,1,"head")
            self._skin_part("body",0,4.5,0,1,1.5,.5,"body")
            self._skin_part("right_arm",-arm_center,4.5,0,arm_half,1.5,.5,"right_arm")
            self._skin_part("left_arm",arm_center,4.5,0,arm_half,1.5,.5,"left_arm",self.skin_legacy)
            self._skin_part("right_leg",-.5,1.5,0,.5,1.5,.5,"right_leg")
            self._skin_part("left_leg",.5,1.5,0,.5,1.5,.5,"left_leg",self.skin_legacy)
        else:
            self._solid_cube(0,7,0,1,1,1,(.48,.43,.38)); self._solid_cube(0,4.5,0,1,1.5,.5,(.38,.34,.30))
            self._solid_cube(-arm_center,4.5,0,arm_half,1.5,.5,(.38,.34,.30)); self._solid_cube(arm_center,4.5,0,arm_half,1.5,.5,(.38,.34,.30))
            self._solid_cube(-.5,1.5,0,.5,1.5,.5,(.30,.27,.24)); self._solid_cube(.5,1.5,0,.5,1.5,.5,(.30,.27,.24))
        if "diamond_helmet" in self.selected and "l1" in self.tex: self._part("head",0,7,0,1.08,1.08,1.08,"l1")
        if "diamond_chestplate" in self.selected and "l1" in self.tex:
            self._part("body",0,4.5,0,1.08,1.58,.58,"l1"); self._part("arm",-arm_center,4.5,0,arm_half+.06,1.58,.58,"l1",True); self._part("arm",arm_center,4.5,0,arm_half+.06,1.58,.58,"l1",False)
        if "diamond_leggings" in self.selected and "l2" in self.tex:
            self._part("body",0,3.05,0,1.06,.52,.56,"l2"); self._part("leg",-.5,1.5,0,.56,1.58,.56,"l2",True); self._part("leg",.5,1.5,0,.56,1.58,.56,"l2",False)
        if "diamond_boots" in self.selected and "l1" in self.tex:
            self._part("leg",-.5,.35,0,.58,.35,.60,"l1",True); self._part("leg",.5,.35,0,.58,.35,.60,"l1",False)

    def _skin_part(self,name,x,y,z,sx,sy,sz,uvname,mirror=False):
        glBindTexture(GL_TEXTURE_2D,self.skin_tex); glColor4f(1,1,1,1)
        uv=SKIN_UV[uvname]
        if self.skin_legacy and uvname=="left_arm": uv=SKIN_UV["right_arm"]
        if self.skin_legacy and uvname=="left_leg": uv=SKIN_UV["right_leg"]
        rot = 0.0
        pivot_y = 0.0
        self._cube_geometry(x,y,z,sx,sy,sz,uv,mirror,SKIN_W,self.skin_h,rot,pivot_y=pivot_y)

    def _solid_cube(self,x,y,z,sx,sy,sz,c):
        glDisable(GL_TEXTURE_2D); glColor4f(*c,1); self._cube_geometry(x,y,z,sx,sy,sz,None); glEnable(GL_TEXTURE_2D)

    def _part(self,name,x,y,z,sx,sy,sz,texname,mirror=False):
        glBindTexture(GL_TEXTURE_2D,self.tex[texname]); glColor4f(1,1,1,1)
        rot = 0.0
        pivot_y = 0.0
        self._cube_geometry(x,y,z,sx,sy,sz,ARMOR_UV[name],mirror,ARM_W,ARM_H,rot,pivot_y=pivot_y)

    def _cube_geometry(self,x,y,z,sx,sy,sz,uvs=None,mirror=False,tw=64.0,th=32.0,rot_x=0.0,pivot_y=0.0):
        glPushMatrix(); glTranslatef(x,y,z); glTranslatef(0,-pivot_y,0); glRotatef(rot_x,1,0,0); glTranslatef(0,pivot_y,0); glScalef(sx,sy,sz)
        v=[(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1),(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1)]
        faces=[(0,1,2,3),(5,4,7,6),(3,2,6,7),(4,5,1,0),(1,5,6,2),(4,0,3,7)]
        glBegin(GL_QUADS)
        # The fixed GL light above handles face brightness; keep texture RGB untouched.
        for fi,face in enumerate(faces):
            glColor4f(1.0, 1.0, 1.0, 1.0)
            if uvs:
                x1,y1,x2,y2=uvs[fi]; u1=x1/tw; u2=x2/tw; v1=1-y2/th; v2=1-y1/th; coords=[(u1,v1),(u2,v1),(u2,v2),(u1,v2)]
                if mirror: coords=[(u2,v1),(u1,v1),(u1,v2),(u2,v2)]
            else: coords=[(0,0)]*4
            for i,idx in enumerate(face): glTexCoord2f(*coords[i]); glVertex3f(*v[idx])
        glEnd(); glPopMatrix()

    def mousePressEvent(self,e):
        if e.button()==Qt.LeftButton: self.dragging=True; self.last_pos=e.pos(); self.setCursor(Qt.ClosedHandCursor)
    def mouseReleaseEvent(self,e):
        if e.button()==Qt.LeftButton: self.dragging=False; self.setCursor(Qt.ArrowCursor)
    def mouseMoveEvent(self,e):
        if self.dragging:
            d=e.pos()-self.last_pos; self.rot_y+=d.x()*.7; self.rot_x=max(-55,min(55,self.rot_x+d.y()*.45)); self.last_pos=e.pos(); self.update()
    def wheelEvent(self,e): self.zoom=max(-18,min(-5.5,self.zoom+e.angleDelta().y()/120*.6)); self.update()

class PreviewDialog(QDialog):
    def __init__(self,source,hue,saturation,value,selected,parent=None):
        super().__init__(parent); self.setWindowTitle("Inspect Edits"); self.resize(980,720); self.selected=set(selected)
        self.version=detect_pack_version(source); self.adapter=get_adapter(self.version)
        self.setStyleSheet("QDialog{background:#1e1f22;color:#f0f0f0;} QLabel{color:#f0f0f0;} QFrame{background:#202124;border:1px solid #3a3d42;border-radius:8px;}")
        root=QVBoxLayout(self); title=QLabel("Inspect Edits"); title.setStyleSheet("font-size:18px;font-weight:700;border:0;background:transparent;"); root.addWidget(title)
        hint=QLabel("Final Color Edit Result"); hint.setStyleSheet("border:0;background:transparent;color:#aeb4bf;"); root.addWidget(hint)
        content=QHBoxLayout(); card=QFrame(); al=QVBoxLayout(card); at=QLabel("Diamond Armor"); at.setAlignment(Qt.AlignCenter); at.setStyleSheet("font-weight:700;border:0;background:transparent;"); al.addWidget(at)
        al.addWidget(ArmorGL(source,hue,saturation,value,selected,card),1); content.addWidget(card,1)
        right=QVBoxLayout(); right.addWidget(self._item_card("Diamond Sword",source,hue,saturation,value,"diamond_sword")); right.addWidget(self._item_card("Golden Apple",source,hue,saturation,value,"golden_apple")); right.addStretch(); content.addLayout(right); root.addLayout(content,1)

    def _pixmap(self,im,w,h):
        im=im.copy(); im.thumbnail((w-24,h-24),Image.Resampling.NEAREST)
        scale=3 if im.width <= 32 and im.height <= 32 else 2
        im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
        im.thumbnail((w-24,h-24),Image.Resampling.NEAREST)
        bio=BytesIO(); im.save(bio,"PNG"); pm=QPixmap(); pm.loadFromData(bio.getvalue(),"PNG"); return pm
    def _item_card(self,name,source,hue,sat,val,item_key):
        f=QFrame(); lay=QVBoxLayout(f); l=QLabel(name); l.setAlignment(Qt.AlignCenter); l.setStyleSheet("font-weight:600;border:0;background:transparent;"); lay.addWidget(l)
        try:
            p=None
            if self.adapter:
                for candidate in self.adapter.TARGETS.get(item_key, ()):
                    p=find_texture(source,candidate) or find_texture(source,Path(candidate).name)
                    if p: break
            if p:
                im=Image.open(p).convert("RGBA")
                if item_key in getattr(self, "selected", set()):
                    im=Chromatic_pil(im,hue,sat,val)
                img=QLabel(); img.setAlignment(Qt.AlignCenter); img.setFixedSize(280,240); img.setStyleSheet("border:0;background:transparent;"); img.setPixmap(self._pixmap(im,280,240)); lay.addWidget(img)
            else: lay.addWidget(QLabel("Texture n?o encontrada no pack"))
        except Exception as exc: lay.addWidget(QLabel("Preview failed: "+str(exc)))
        return f


