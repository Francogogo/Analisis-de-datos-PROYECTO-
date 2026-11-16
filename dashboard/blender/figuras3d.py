# Figuras 3D por pestaña. Cada cantidad sale de datos3d.json (cifras.json, base o modelo M3).
# Uso: blender -b --factory-startup -P figuras3d.py -- datos3d.json salida/ <escena> [animar]
import bpy, json, math, random, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
D = json.load(open(argv[0])); OUT = argv[1]; ESC = argv[2]; ANIMAR = len(argv) > 3
W, H = (1120, 760) if ESC == "sala" else (1600, 900)

scn = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
scn.render.engine = "CYCLES"; scn.cycles.device = "CPU"; scn.cycles.samples = 64; scn.cycles.use_denoising = True
scn.render.resolution_x, scn.render.resolution_y = W, H
scn.render.film_transparent = True
scn.view_settings.view_transform = "Standard"
scn.render.image_settings.file_format = "PNG"; scn.render.image_settings.color_mode = "RGBA"


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


_mats = {}
def mat(hexa, rough=.38, vidrio=False):
    k = (hexa, rough, vidrio)
    if k in _mats: return _mats[k]
    m = bpy.data.materials.new(hexa); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(hexa), 1); b.inputs["Roughness"].default_value = rough
    if vidrio:
        b.inputs["Transmission Weight"].default_value = .92; b.inputs["IOR"].default_value = 1.2
        b.inputs["Roughness"].default_value = .12
    _mats[k] = m; return m


def caja(x, y, z0, sx, sy, alto, color, bisel=.04, **kw):
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z0 + alto / 2)); o = bpy.context.object
    o.scale = (sx / 2, sy / 2, max(alto, 1e-4) / 2)
    o.data.materials.append(color if isinstance(color, bpy.types.Material) else mat(color, **kw))
    if bisel:
        bpy.ops.object.transform_apply(scale=True)
        b = o.modifiers.new("b", "BEVEL"); b.width = min(bisel, sx / 3, sy / 3, max(alto, 1e-4) / 3); b.segments = 3
    return o


def cilindro(x, y, z0, r, alto, color, **kw):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=r, depth=max(alto, 1e-4), location=(x, y, z0 + alto / 2))
    o = bpy.context.object; o.data.materials.append(mat(color, **kw)); bpy.ops.object.shade_smooth()
    return o


def piso():
    bpy.ops.mesh.primitive_plane_add(size=200); p = bpy.context.object
    p.is_shadow_catcher = True; return p


def camara(foco, escala, elev=34, azim=-42, dist=40):
    a, e = math.radians(azim), math.radians(elev)
    pos = Vector(foco) + Vector((math.sin(-a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    bpy.ops.object.camera_add(location=pos); cam = bpy.context.object
    cam.data.type = "ORTHO"; cam.data.ortho_scale = escala; cam.data.clip_end = 500
    bpy.ops.object.empty_add(location=foco); t = bpy.context.object
    c = cam.constraints.new("TRACK_TO"); c.target = t; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    scn.camera = cam


def luces():
    bpy.ops.object.light_add(type="AREA", location=(-12, -14, 22)); k = bpy.context.object
    k.data.energy = 9000; k.data.size = 14; k.rotation_euler = (math.radians(35), 0, math.radians(-40))
    bpy.ops.object.light_add(type="AREA", location=(16, 6, 10)); f = bpy.context.object
    f.data.energy = 2500; f.data.size = 18; f.rotation_euler = (math.radians(60), 0, math.radians(110))
    w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (*lin("#eef2f6"), 1); bg.inputs["Strength"].default_value = .55


COBALTO, ROJO, TURQ, GRIS, TINTA = "#1d4ed8", "#bf4a2a", "#0d7f8c", "#8a979b", "#1d2326"
CARGA = ["#c9a25c", "#d9762c", "#bf4a2a", "#8f2327", "#5b1120"]
piso(); luces()

if ESC == "sala":  # Contexto: 100 camas, una ficha por día; las 9 de estadía prolongada en rojo
    dias = D["dias"]; random.seed(7); pos = [(i, j) for i in range(10) for j in range(10)]; random.shuffle(pos)
    ALTO = .034; maxd = max(dias)
    for k, (i, j) in enumerate(pos):
        x, y = (i - 4.5) * 1.25, (j - 4.5) * 1.25
        caja(x, y, 0, .82, 1.06, .07, "#ffffff", bisel=.02, rough=.6)
        caja(x, y + .42, .07, .74, .16, .05, "#dbe3ee", bisel=.02)
        n = max(1, round(dias[k])); color = mat(CARGA[3] if k >= 91 else COBALTO)
        bpy.ops.mesh.primitive_cube_add(location=(x, y, .07 + ALTO * .31)); o = bpy.context.object
        o.scale = (.31, .31, ALTO * .31); o.data.materials.append(color)
        arr = o.modifiers.new("dias", "ARRAY"); arr.relative_offset_displace = (0, 0, 1 / .62); arr.count = n
        if ANIMAR:
            t = lambda d: 10 + 92 * (d / maxd) ** .6
            o.scale.z = 1e-4; o.keyframe_insert("scale", index=2, frame=t(1) - 3)
            o.scale.z = ALTO * .31; o.keyframe_insert("scale", index=2, frame=t(1))
            for d in range(1, n + 1):
                arr.count = d; arr.keyframe_insert("count", frame=round(t(d)))
    camara((0, 0, 1.0), 19.5, elev=36, azim=-45)

elif ESC == "exploracion":  # 100 grupos de 1 % ordenados en espiral: la cola larga sube al final
    dias = sorted(D["dias"]);
    for k, d in enumerate(dias):
        ang = k / 100 * 1.75 * math.pi; r = 3.2 + k * .05
        x, y = r * math.cos(ang), r * math.sin(ang)
        caja(x, y, 0, .42, .42, .12 + d * .048, CARGA[3] if k >= 91 else COBALTO, bisel=.05)
    camara((0, 0, 1.4), 23.5, elev=30, azim=-30)

elif ESC == "relaciones":  # 16 regiones de norte a sur: alto = % de estadías prolongadas, color = macrozona
    regs = D["regiones"]
    for k, (nombre, zona, pct) in enumerate(regs):
        y = 9 - k * 1.2; x = math.sin(k / 15 * math.pi) * .6
        caja(x, y, 0, .95, 1.0, pct * .42, D["zonas"][zona], bisel=.06)
        caja(x, y, 0, 1.25, 1.15, .06, "#ffffff", bisel=.02, rough=.6)
    camara((0, 0, 2.0), 22, elev=26, azim=-62)

elif ESC == "diagnosticos":  # desviación estándar del residuo por cuartil: la dispersión crece
    sd = list(D["sd"].values())
    for k, s in enumerate(sd):
        x = (k - 1.5) * 3.3
        cilindro(x, 0, 0, s * 1.35, .18, "#ffffff", rough=.5)
        cilindro(x, 0, .18, s * 1.25, s * 4.2, COBALTO, vidrio=True)
        cilindro(x, 0, .18, .09, s * 4.2 + .2, TINTA)
    camara((0, 0, 1.8), 15.5, elev=24, azim=-24)

elif ESC == "modelos":  # η² parcial por factor y el umbral práctico 0,01 como lámina de vidrio
    eta = sorted(D["eta"].items(), key=lambda kv: -kv[1])
    for k, (f, v) in enumerate(eta):
        x = (k - 3) * 1.6
        caja(x, 0, 0, 1.05, 1.05, .06 + v * 75, COBALTO if v >= .01 else GRIS, bisel=.08)
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, .06 + .01 * 75)); g = bpy.context.object
    g.scale = (6.3, 1.4, .025); g.data.materials.append(mat("#bfd3ff", vidrio=True))
    camara((0, 0, 2.7), 17.5, elev=22, azim=-28)

elif ESC == "whatif":  # días estimados por edad (perfil de referencia) con su IC 95 %: una cinta
    pts = D["edad"]
    for k, (e, dd, inf, sup) in enumerate(pts):
        x = (e - 46) * .16
        caja(x, 0, 0, .09, .55, dd * 2.2, COBALTO, bisel=.02)
        caja(x, 0, inf * 2.2, .15, 1.15, max((sup - inf) * 2.2, .03), "#bfd3ff", bisel=0, vidrio=True)
    camara((0, 0, 3.0), 18, elev=24, azim=-62)

elif ESC == "conclusiones":  # %Δ por capítulo frente al digestivo: rojo alarga, turquesa acorta
    caps = sorted(D["capitulos"].items(), key=lambda kv: kv[1])
    for k, (cap, p) in enumerate(caps):
        x = (k - len(caps) / 2) * .8; h = abs(p) * .022
        caja(x, 0, 0 if p >= 0 else -h, .58, .58, h, ROJO if p > 0 else TURQ, bisel=.05)
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0)); g = bpy.context.object
    g.scale = (len(caps) * .43, .7, .015); g.data.materials.append(mat("#ffffff", rough=.5))
    for o in bpy.data.objects:
        if o.type == "MESH" and o.is_shadow_catcher: o.location.z = -3.4
    camara((0, 0, 1.0), 18, elev=18, azim=-24)

if ANIMAR:
    scn.frame_start, scn.frame_end = 1, 120; scn.render.fps = 30
    scn.render.filepath = f"{OUT}/{ESC}_"; bpy.ops.render.render(animation=True)
else:
    scn.render.filepath = f"{OUT}/{ESC}.png"; bpy.ops.render.render(write_still=True)
