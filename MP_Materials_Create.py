# region imports
import bpy
import os.path
import re
import xml.etree.ElementTree as ET
from bpy.props import (
    StringProperty,
    BoolProperty,
    PointerProperty,
    CollectionProperty,
    IntProperty
)
from bpy.types import (
    Panel,
    Operator,
    AddonPreferences,
    PropertyGroup
)
from .MP_Functions import *
# endregion imports




class MP_OT_Materials_Create(Operator):
    bl_idname = "view3d.materials_create"
    bl_label = "create materials"
    bl_desciption = "create material"
   
    def execute(self, context):
        mp_props = context.scene.mp_props
        
        matName     = fixName(mp_props.ST_mat_name) 
        matBTex     = mp_props.FI_mat_btex
        matModel    = mp_props.LI_mat_model if mp_props.LI_mat_type == "Custom" else "TDSN"
        matPhysic   = mp_props.LI_mat_physic
        isNadeoMat  = "True" if mp_props.LI_mat_type == "NadeoLib" else "False"
        
        createMaterial(
            matname     = matName, 
            basetex     = matBTex, 
            model       = matModel, 
            physic      = matPhysic, 
            isNadeoMat  = isNadeoMat,
            )
            
        context.region.tag_redraw()
            
        return {"FINISHED"}
    
    
class MP_OT_Materials_Update(Operator):
    bl_idname = "view3d.materials_update"
    bl_label = "update materials"
    bl_desciption = "update material"
   
    def execute(self, context):
        mp_props = context.scene.mp_props
        
        matType     = mp_props.LI_mat_type
        matName     = mp_props.LI_mat_matList 
        matBTex     = mp_props.FI_mat_btex if matType == "Custom" else mp_props.LI_mat_btex
        matModel    = mp_props.LI_mat_model
        matPhysic   = mp_props.LI_mat_physic
        isNadeoMat  = True if mp_props.LI_mat_type == "NadeoLib" else False
        
        updateMaterial(
            matname     = matName, 
            newbtex     = matBTex, 
            newmodel    = matModel, 
            newphysic   = matPhysic,
            newtype     = matType,
            isNadeoMat  = isNadeoMat
            )
            
        context.region.tag_redraw()
            
        return {"FINISHED"}
    
   
class MP_PT_Materials_Create(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_category = 'ManiaPlanetAddon'
    bl_label = "Material Creation/Update"
    bl_idname = "OBJECT_PT_MP_CreateMaterials"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    # endregion
    
    def draw(self, context):

        mp_props = context.scene.mp_props
        mats = bpy.data.materials
         
        layout = self.layout

        if not isIniValid():
            row = layout.row().label(text=errorMsgNadeoIni, icon="ERROR")
            return
        
        row = layout.row().prop(mp_props, "LI_mat_createUpdate", text="Create or update", expand=True)
        row = layout.row().prop(mp_props, "LI_mat_type",        text="Type",            expand=True )
        
        
        #? -------------
        
        
        if mp_props.LI_mat_createUpdate == "CREATE":
            row = layout.row().prop(    mp_props, "ST_mat_name",    text="Name")
            
            row = layout.row()
            row.enabled = True if mp_props.LI_mat_type == "Custom" else False
            row.prop(mp_props, "LI_mat_model",   text="Model")
            
            if mp_props.LI_mat_type == "NadeoLib":
                row = layout.row().prop(mp_props, "LI_mat_btex",        text="Texture")
                row = layout.row().prop(mp_props, "LI_mat_envi",        text="Envi",)
                row = layout.row().prop(mp_props, "LI_mat_texFolders",  text="TexPath")
            else:
                row = layout.row().prop(mp_props, "FI_mat_btex",        text="TexPath")
            
            row = layout.row().prop(mp_props, "LI_mat_physic",  text="Physic")
            
            row = layout.row()
            row.scale_y = 1.5
            row.operator("view3d.materials_create", text="Create Material", icon="ADD")

        
        #? ----------
        
        
        if mp_props.LI_mat_createUpdate == "UPDATE":
            row = layout.row().prop(mp_props, "LI_mat_matList", text="Update")
            
            row = layout.row()
            row.enabled = True if mp_props.LI_mat_type == "Custom" else False
            row.prop(mp_props, "LI_mat_model", text="Model")
            
            if mp_props.LI_mat_type == "Custom":
                row = layout.row().prop(mp_props, "FI_mat_btex",        text="TexPath")
            else:
                row = layout.row().prop(mp_props, "LI_mat_btex",        text="Texture")
                row = layout.row().prop(mp_props, "LI_mat_envi",        text="Envi",)
                row = layout.row().prop(mp_props, "LI_mat_texFolders",  text="TexPath")
            
            row = layout.row().prop(mp_props, "LI_mat_physic",  text="Physic")

            row = layout.row()
            row.scale_y = 1.7
            row.enabled = True if mp_props.LI_mat_matList is not None else False
            row.operator("view3d.materials_update", text=f"Update: {mp_props.LI_mat_matList}", icon="FILE_REFRESH")

        
        
        
        
        

def updateMaterial(matname: str, newbtex: str, newmodel: str, newphysic: str, newtype: str, isNadeoMat: str) -> None:
    """update material, overwrite all old settings (del/create all nodes, custom props..)"""
    mp_props = bpy.context.scene.mp_props
    mats = bpy.data.materials
    mat  = mats[matname]
    
    pro__print(newbtex)
    
    mat["BaseTexture"]  = newbtex
    mat["IsNadeoMat"]   = "True" if newtype == "NadeoLib" else "False"
    mat["Model"]        = newmodel
    mat["PhysicsId"]    = newphysic
    
    if createMaterialNodes(matname=matname) is False:
        makeReportPopup(title=f"Material update of <{matname}> failed, custom properties not set/invalid", icon="ERROR")
    else:
        makeReportPopup(title=f"Material updated", icon="ERROR")
        pro__print("material updated: ", matname)
    


def createMaterial(matname: str, basetex: str, model: str, physic: str, isNadeoMat: str) -> None:
    """create material by given name if a material with given materialname doesn't exist yet\n
    also set custom props: basetexture, model, physicsid, isnadeomat"""

    mats = bpy.data.materials
    
    if matname not in mats:
        newmat = mats.new(matname)
        newmat["BaseTexture"]   = basetex 
        newmat["Model"]         = model
        newmat["PhysicsId"]     = physic
        newmat["IsNadeoMat"]    = str(isNadeoMat)
        
        createMaterialNodes(matname=matname)
        
        pro__print("material created: ", matname)
        makeReportPopup(title=f"Material created", icon="ERROR")
    
    else: 
        pro__print(" - material already exists, creation stopped", matname)
        makeReportPopup(title=f"Material with the name <{matname}> already exist!", icon="ERROR")



def deleteMaterialNodes(matname: str) -> None:
    """delete all nodes of material"""
    mat = bpy.data.materials[matname]
    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)



def createMaterialNodes(matname: str) -> None:
    """create nodes for material (TDSN etc, TIAdd), configure them:\n
    load textures if necessary, connect nodes if necessary, """
    mp_props = bpy.context.scene.mp_props
    imgs = bpy.data.images
    mats = bpy.data.materials
    mat  = mats[matname]
    matModel = mat["Model"]

    pro__print("create nodes for: ", mat.name)
    
    if checkMatValidity(matname=matname) is not True:
        return "ERROR"
    
    mat.use_nodes = True
    
    links = mat.node_tree.links
    nodes = mat.node_tree.nodes
    
    deleteMaterialNodes(matname=matname)
    
    #node positions
    xstep = 300
    ystep = 300
    def x(step): return  (xstep * step)
    def y(step): return -(ystep * step)
    
    output = nodes.new(type="ShaderNodeOutputMaterial")
    output.location = x(7), y(2)
    
    tex_frame = nodes.new(type="NodeFrame")
    tex_frame.location = x(.9), y(0)
    tex_frame.label = "Textures, <M> to un/mute"
    tex_frame.name = "tex_frame"
    tex_frame.color = (0.00332224, 0.181666, 0.410938)
    tex_frame.use_custom_color = True
    
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = x(4), y(1)
    
    bsdf_mixShader = nodes.new(type="ShaderNodeMixShader")
    bsdf_mixShader.location = x(5.5), y(2)

    uvmap = nodes.new(type="ShaderNodeUVMap")
    uvmap.location = x(0), y(1)
    uvmap.uv_map = "BaseMaterial"
    
    tex_D = nodes.new(type="ShaderNodeTexImage")
    tex_D.location = x(.9), y(1)
    tex_D.parent  = nodes.get("tex_frame")
    tex_D.label = "Texture Diffuse _D.dds"
    tex_D.name  = "tex_D"
    
    tex_S = nodes.new(type="ShaderNodeTexImage")
    tex_S.location = x(.9), y(2)
    tex_S.parent  = nodes.get("tex_frame")
    tex_S.label = "Texture Specular _S.dds"
    tex_S.name  = "tex_S"
    
    tex_S_converter = nodes.new(type="ShaderNodeSeparateRGB")
    tex_S_converter.location = x(2), y(2)
    
    tex_N = nodes.new(type="ShaderNodeTexImage")
    tex_N.location = x(.9), y(3)
    tex_N.parent  = nodes.get("tex_frame")
    tex_N.label = "Texture NormalMap _N.dds"
    tex_N.name  = "tex_N"
    
    tex_N_converter = nodes.new(type="ShaderNodeNormalMap")
    tex_N_converter.location = x(2), y(3)
    
    tex_I = nodes.new(type="ShaderNodeTexImage")
    tex_I.location = x(.9), y(4)
    tex_I.parent  = nodes.get("tex_frame")
    tex_I.label = "Texture Illum _I.dds"
    tex_I.name  = "tex_I"

    tex_I_BW = nodes.new(type="ShaderNodeRGBToBW")
    tex_I_BW.location = x(2), y(4)

    tex_I_math = nodes.new(type="ShaderNodeMath")
    tex_I_math.location = x(3), y(4)
    tex_I_math.operation = "SUBTRACT"
    tex_I_math.inputs[1].default_value = 0
    
    tex_I_glow = nodes.new(type="ShaderNodeEmission")
    tex_I_glow.location = x(4), y(4)
    tex_I_glow.inputs[1].default_value = 200 if matModel.upper() == "TIADD" else 3

    # -----------------
    
    links.new(uvmap.outputs[0], tex_D.inputs[0])
    links.new(uvmap.outputs[0], tex_S.inputs[0])
    links.new(uvmap.outputs[0], tex_N.inputs[0])
    links.new(uvmap.outputs[0], tex_I.inputs[0])
    
    # ------------------
    

    
    if matModel.upper() in ["TDSN", "TDOSN", "TDOBSN", "TDSNI", "TDSNI_NIGHT"]:
        
        links.new(tex_D.outputs[0], bsdf.inputs[0])
        links.new(tex_D.outputs[1], bsdf.inputs[18])
        
        links.new(tex_S.outputs[0],             tex_S_converter.inputs[0])
        links.new(tex_S_converter.outputs[0],   bsdf.inputs[5])
        links.new(tex_S_converter.outputs[1],   bsdf.inputs[15])
    
        links.new(tex_N.outputs[0],             tex_N_converter.inputs[1])
        links.new(tex_N_converter.outputs[0],   bsdf.inputs[19])
    
        links.new(bsdf.outputs[0], output.inputs[0])
    
    
    if matModel.upper() in ["TDSNI", "TDSNI_NIGHT"]:
        links.new(tex_I.outputs[0],             tex_I_glow.inputs[0])
        links.new(tex_I_glow.outputs[0],        bsdf_mixShader.inputs[2])
        links.new(bsdf.outputs[0],              bsdf_mixShader.inputs[1])
        links.new(bsdf_mixShader.outputs[0],    output.inputs[0])
        
    
    
    #TIAdd needs special stuff, using only _I texture as diffuse, "transparent glow"
    if matModel.upper() == "TIADD":
        
        links.new(tex_I.outputs[0], tex_I_BW.inputs[0])
        links.new(tex_I.outputs[0], tex_I_glow.inputs[0])
        
        links.new(tex_I_math.outputs[0], bsdf.inputs[18])
        links.new(tex_I_BW.outputs[0],   tex_I_math.inputs[0])
        links.new(tex_I_BW.outputs[0],   bsdf_mixShader.inputs[0])
        
        links.new(bsdf.outputs[0],           bsdf_mixShader.inputs[1])
        links.new(tex_I_glow.outputs[0],     bsdf_mixShader.inputs[2])
        links.new(bsdf_mixShader.outputs[0], output.inputs[0])
            
    # ------------------
    
    missingTexs = []
    matBTexSrc  = mp_props.LI_mat_texFolders
    matBTex     = mat["BaseTexture"] if mp_props.LI_mat_type == "Custom" else mp_props.LI_mat_btex
    nadeoMat    = True if mp_props.LI_mat_type == "NadeoLib" else False
    texName     = fileNameOfPath(path=matBTex)
    
    #absolute texture path, based on material prop isNadeoMat 
    if nadeoMat:    
        texPath     = getDocPathItemsAssets() + "/TEX_" + matBTexSrc + "/"
        currentMat  = nadeoLibParser()
        currentMat  = currentMat[mp_props.LI_mat_envi][mp_props.LI_mat_btex]
        currentMatTexD = currentMat["NadeoTexD"]
        currentMatTexS = currentMat["NadeoTexS"]
        currentMatTexN = currentMat["NadeoTexN"]
        currentMatTexI = currentMat["NadeoTexI"]
        currentMatTextures = {
            "d":currentMatTexD, 
            "s":currentMatTexS, 
            "n":currentMatTexN, 
            "i":currentMatTexI 
            }
                
    else:           
        texPath = getDocPath() + matBTex #custom, ex: C:/../ManiaPlanet/Items/RPG_Textures/Glass
        currentMatTextures = []
        
    # load <texname>_D/S/N.dds if it exists, load_<type>Tex = tuple(texname_<type>.dds, bool)
    if matModel.upper() in ["TDSN", "TDOSN", "TDOBSN", "TDSNI", "TDSNI_NIGHT"]:
        load_DTex = loadDDSTextureIntoBlender(texpath=texPath, textype="D", nadeomat=nadeoMat, texlist=currentMatTextures)
        load_STex = loadDDSTextureIntoBlender(texpath=texPath, textype="S", nadeomat=nadeoMat, texlist=currentMatTextures)
        load_NTex = loadDDSTextureIntoBlender(texpath=texPath, textype="N", nadeomat=nadeoMat, texlist=currentMatTextures)
        
        if load_DTex[1] is True: assignTextureToImageNode(texname=load_DTex[0], node=tex_D)
        if load_STex[1] is True: assignTextureToImageNode(texname=load_STex[0], node=tex_S)
        if load_NTex[1] is True: assignTextureToImageNode(texname=load_NTex[0], node=tex_N)
        if load_NTex[1] is True: assignTextureToImageNode(texname=load_NTex[0], node=tex_N)
        
        tdsnTexs    = [load_DTex, load_STex, load_NTex]
        missingTexs = ["Texture missing: " + tex[0] for tex in tdsnTexs if tex[1] is False]

    # load <texname>_I.dds if it exists
    if matModel.upper() in ["TDSNI", "TDSNI_NIGHT", "TIADD"]:
        load_ITex = loadDDSTextureIntoBlender(texpath=texPath, textype="I", nadeomat=nadeoMat, texlist=currentMatTextures)
        if load_ITex[1] is True:    assignTextureToImageNode(texname=load_ITex[0], node=tex_I)
        if load_ITex[1] is False:   missingTexs.append("Texture missing: " + load_ITex[0])
 
    # ----
    
    bm = "OPAQUE"
    if      matModel == "TDSN":          bm = "OPAQUE"
    elif    matModel == "TDSNI":         bm = "OPAQUE"
    elif    matModel == "TDSNI_NIGHT":   bm = "OPAQUE"
    elif    matModel == "TDOSN":         bm = "CLIP"
    elif    matModel == "TDOBSN":        bm = "BLEND"
    elif    matModel == "TIAdd":         bm = "BLEND"
        
    mat.blend_method = bm
    mat.use_backface_culling = True
    
    for node in nodes:
        if node.type == "TEX_IMAGE" and node.image == None:
            node.mute = True
            node.hide = True
    
    if len(missingTexs) > 0:
        makeReportPopup("Missing textures from last material creation", missingTexs, "ERROR")    
    
    #? end createMaterialNodes()   



def assignTextureToImageNode(texname, node) -> bool:
    """assign blender already loaded texture (dds?) to given node of type ImageTexture"""
    imgs = bpy.data.images
    
    if texname in imgs:
        img = imgs[texname]
        node.image = img
        
        if texname.lower().endswith("n.dds"):
            img.colorspace_settings.name = "Non-Color"
        return True
    
    else:
        node.mute = True
        return False



def loadDDSTextureIntoBlender(texpath: str, textype: str, nadeomat: bool, texlist: list=[]) -> tuple:
    """load dds texture into blender, return tuple: (texname, bool(success)),\n
        textype in ["d", "n", "s", "i"]"""
    imgs = bpy.data.images
    
    if nadeomat:
        texpath = texpath + texlist[textype.lower()]
        texpath = texpath.replace(textype + "_.dds", "")
        texpath = texpath.replace(textype + ".dds",  "")
        
    texpath = fixSlash(texpath)
    
    fullTexPath_US = f"{texpath}_{textype}.dds"
    fullTexPath    = f"{texpath}{textype}.dds"
    
    texName     = fileNameOfPath(path=fullTexPath_US)
    tex         = "_" if doesFileExist(fullTexPath_US) else "" if doesFileExist(fullTexPath) else False
    texToLoad   = ""
    
    if tex is False: return (texName, False)
    if tex == "_":   texToLoad = fullTexPath_US
    if tex == "":    texToLoad = fullTexPath
    
    texName = fileNameOfPath(texToLoad)
    
    if texName not in imgs:
        pro__print(texToLoad)
        imgs.load(texToLoad)

    return texName, True







        
        
        
        
        