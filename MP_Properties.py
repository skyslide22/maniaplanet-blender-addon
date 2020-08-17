from typing import ItemsView
import bpy
import glob
import os
import re
import bpy.utils.previews
import webbrowser
from bpy.props import (
    StringProperty,
    BoolProperty,
    PointerProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    BoolVectorProperty,
)
from bpy.types import (
    Context, Panel,
    Operator,
    AddonPreferences,
    PropertyGroup
)
from .MP_Functions import * 
from .MP_Icon_Create import *


errorEnumProps = [("ERROR", "ERROR", "ERROR", "ERROR", 0)]


def getIconDimensions():
    return  [
        ("256",   "256px",   "px of icon"),
        ("128",  "128px",    "px of icon"),
        ("64",   "64px",     "px of icon"),
        ("32",    "32px",    "px of icon"),
    ]



def getIconCamPos():
    return  [
        ("FRONT",   "FRONT",    "FRONT",    getIcon("CAM_FRONT"),   0),
        ("LEFT",    "LEFT",     "LEFT",     getIcon("CAM_LEFT"),    1),
        ("RIGHT",   "RIGHT",    "RIGHT",    getIcon("CAM_RIGHT"),   2),
        ("TOP",     "TOP",      "TOP",      getIcon("CAM_TOP"),     3),
        ("CLASSIC", "CLASSIC",  "3D ICON",  getIcon("CAM_CLASSIC"), 4),
    ]
    
    
    
def getMatModels():
    return  [
        ("TDSN",        "TDSN",         "Default Model: _Diffuse, _Specular, _Normalmap",       getIcon("MODEL_TDSN"),          0),
        ("TDOSN",       "TDOSN",        "Same as TDSN, supports 1bit alpha",                    getIcon("MODEL_TDOSN"),         1),
        ("TDOBSN",      "TDOBSN",       "Same as TDSN, supports 256bit alpha",                  getIcon("MODEL_TDOBSN"),        2),
        ("TDSNI",       "TDSNI",        "Same as TDSN, additionally use _Illum",                getIcon("MODEL_TDSNI"),         3),
        ("TDSNI_Night", "TDSNI_Night",  "Same as TDSN, additionally use _Illum at sunset/night",getIcon("MODEL_TDSNI_NIGHT"),   4),
        ("TIAdd",       "TIAdd",        "Use _Illum only, 256 bit alpha, black=transparent",    getIcon("MODEL_TIADD"),         5)
    ]
    
    
    
def getMatType():
    return  [
        ("NadeoLib", "NadeoLib", "Material linked to NadeoLib"),
        ("Custom",   "Custom",   "Material uses custom Textures (ex: /Items/MyTexture, no _D.dds!)")
    ]
    
    
    
def getMatCreateType():
    return  [
        ("CREATE",  "Create",   "Create non existing Material"),
        ("UPDATE",  "Update",   "Update an existing Material"),
    ]
    
    
    
def getExistingMats(self, context) -> list:
    mats = bpy.data.materials
    return [(mat.name, mat.name, "Material to update..") for mat in mats]



matsFromLib = errorEnumProps
def getNadeoMatsFromLIB(self, context) -> list:
    """return list(tuples) of nadeolib materials"""
    mp_props = context.scene.mp_props
    global matsFromLib
    
    if len(matsFromLib) > 1:
        return matsFromLib
    
    try:    lib = nadeoLibParser()
    except AttributeError:
        return matsFromLib
    
    mats = []
    for envi in lib:
        if envi == mp_props.LI_mat_envi:
            for mat in lib[envi]:
                mats.append(    (mat, mat, mat)     )
    
    matsFromLib = mats
    return matsFromLib



def updateNadeoMatEnviList(self, context) -> None:
    global matsFromLib
    matsFromLib = errorEnumProps
    getNadeoMatsFromLIB(self=self, context=context)



def updateMatType(self, context, origin) -> None:
    mp_props = context.scene.mp_props
    newMatBTex = mp_props.FI_mat_newBTex
    isCustomBTex = newMatBTex.startswith("/Items")
    
    mp_props.LI_mat_type = "Custom" if isCustomBTex else "NadeoLib"
    
    fixCustomTexSrcPath(self, context, origin)
    setMatTypeBasedOnBTex(self, context, origin, isCustomBTex)
        
        
        
def setMatTypeBasedOnBTex(self, context, origin, isCustomBTex) -> None:
    mp_props = context.scene.mp_props

    if not isCustomBTex: mp_props.LI_mat_type = "NadeoLib"
    if     isCustomBTex: mp_props.LI_mat_type = "Custom"



def setMatModelToTDSN(self, context) -> None:
    mp_props = context.scene.mp_props
    mp_props.LI_mat_model = "TDSN"



    
def setPropsOFMatToChange(self, context) -> None:
    """set props to update mat, called from mp_props.LI_mat_matList when changed"""
    mp_props = context.scene.mp_props
    matName  =   mp_props.LI_mat_matList
    mats = bpy.data.materials
    mat  = mats[matName]
    physics = [phy[0] for phy in getMatPhysics(self, context)]
    
    matProps = mat.keys()
    
    if "BaseTexture" not in matProps:   mat["BaseTexture"]  = ""
    if "Model"       not in matProps:   mat["Model"]        = "TDSN" 
    if "PhysicsId"   not in matProps:   mat["PhysicsId"]    = "Concrete" 
    if "IsNadeoMat"  not in matProps:   mat["IsNadeoMat"]   = "True" 
    
    matBTex      =   mat["BaseTexture"]
    matModel     =   mat["Model"]
    matPhysicsId =   mat["PhysicsId"] if mat["PhysicsId"] in physics else "Concrete"
    matType      =   mat["IsNadeoMat"]
    
    context.scene.mp_props.ST_mat_newName       = matName
    context.scene.mp_props.FI_mat_newBTex       = matBTex
    context.scene.mp_props.ST_mat_newModel      = matModel
    context.scene.mp_props.LI_mat_newPhysic     = matPhysicsId
    context.scene.mp_props.ST_mat_newType       = matType


texFolders = errorEnumProps
def getMatTextureSourceFolders(self, context):
    """get folders in assetfolder which starts with TEX_"""
    folders = []
    global texFolders
    
    if len(texFolders) > 1:
        return texFolders
    
    #try excpet necessary, look getMatPhysics() below for more infos
    try:
        folders = getListOfFoldersInX(folderpath=getDocPathItemsAssets(), prefix="TEX_")
        folders = [folder.replace("TEX_", "") for folder in folders]
        folders = [(f, f, f) for f in folders]
        
    except AttributeError:
        return texFolders
    
    texFolders = folders
    return texFolders
    


def fixCustomTexSrcPath(self, context, origin) -> None:
    """called from a update function in a proptery, fixes texture path"""
    texSrc = eval("self." + origin)
    pattern = r"_*\w{1}\.dds"
    
    if "\\" or "/" in texSrc:
        texSrc = texSrc.replace("\\", "/")
        texSrc = texSrc.split("Items/")
        texSrc = "/Items/" + texSrc[-1]
        texSrc = re.sub(pattern=pattern, repl="", string=texSrc) #remove _*.dds

        mp_props = bpy.context.scene.mp_props
        exec("self[\"" + origin + "\"] = texSrc")
        # [] = x style avoids infinite recursion, loop will happen here: mp_props.sth = x
    


def getMatEnvies() -> list:
    envies = ["Stadium", "Canyon", "Valley", "Lagoon", "Storm"]
    return [(e,e,e) for e in envies]



matPhysics = errorEnumProps
def getMatPhysics(self, context) -> list:
    """get physics from nadeoLibParser() and return als list(tuples)"""
    global matPhysics #create global variable to read libfile only once
    
    if len(matPhysics) > 1:
        return matPhysics
    
    #calling getNadeoImporterLIBPath while addon is registering not allowed:
    #AttributeError: "_RestrictedContext" object has no attribute "scene"
    #return tuple "ERROR" the first few milliseconds to fix it
    #then assign list of physics to matPhysics, to read file only once
    try:    libfile =  getNadeoImporterLIBPath()
    except  AttributeError:
        return matPhysics
    
    if not libfile.endswith("Lib.txt"):
        return matPhysics
    
    libmats = nadeoLibParser()
    physics = []
    
    for envi in libmats:
        for mat in libmats[envi]:
            mat = libmats[envi][mat]
            phy = mat["PhysicsId"]
            if phy not in physics:
                physics.append(phy)
    
    #some physics are not used by nadeo but exist.
    for mphy in missingPhysicsInLib: 
        if mphy not in physics:
            physics.append(mphy)
    
    physics.sort()
    physicsWithIcons = []
    
    for i, phy in enumerate(physics):
        icon = "FUND" if phy in favPhysicIds else "AUTO"
        physicsWithIcons.append(    (phy, phy, phy, icon, i)  )

    matPhysics = physicsWithIcons
    return matPhysics



def getExportObjTypes(self, context) -> list:
    return [
        (   'MESH_LIGHT_EMPTY', "Mesh, Light, Empty",   "Normal meshes, lights and empties",                "SCENE_DATA",   0),
        (   'MESH_LIGHT',       "Mesh, Light",          "Normal meshes, lights, no empties",                "LIGHT_SUN",    1),
        (   'MESH_EMPTY',       "Mesh, Empty",          "Normal meshes, empties(_socket_START), no lights", "EMPTY_ARROWS", 2),
    ]


def getExportTypes(self, context) -> list:
    return [
        (   'EXPORT',           "Export",               "Export collections",                   "EXPORT",           0),
        (   'EXPORT_CONVERT',   "Export & Convert",     "Export collections and convert",       "CON_FOLLOWPATH",   1),
        (   'CONVERT',          "Convert Folder",       "Convert all fbx in selected folder",   "FILE_REFRESH",     2),
    ]



def getWayPointVariations() -> list:
    return [
        ("Start",       "Start",        "Use this waypoint type as fallback", getIcon("WP_START"),          0),
        ("Finish",      "Finish",       "Use this waypoint type as fallback", getIcon("WP_FINISH"),         1),
        ("StartFinish", "StartFinish",  "Use this waypoint type as fallback", getIcon("WP_STARTFINISH"),    2),
        ("Checkpoint",  "Checkpoint",   "Use this waypoint type as fallback", getIcon("WP_CHECKPOINT"),     3),
    ]
    
    

def getItemXMLCollections() -> list:
    return [
        ("Stadium", "Stadium",  "", getIcon("ENVI_STADIUM"),    1),
        ("Canyon",  "Canyon",   "", getIcon("ENVI_CANYON"),     2),
        ("Valley",  "Valley",   "", getIcon("ENVI_VALLEY"),     3),
        ("Lagoon",  "Lagoon",   "", getIcon("ENVI_LAGOON"),     4),
        ("Storm",   "Storm",    "", getIcon("ENVI_STORM"),      5),
        ("Common",  "Common",   "", getIcon("ENVI_COMMON"),     6),
        ("SMCommon","SMCommon", "", getIcon("ENVI_COMMON"),     7),
    ]



def getItemXMLType() -> list:
    return [    
        ("StaticObject","StaticObject","StaticObject",  "KEYFRAME",     0), 
        ("DynaObject",  "DynaObject",   "DynaObject",   "KEYFRAME_HLT", 1) 
    ]

def getMeshXMLType() -> list:
    return [    
        ("Static",  "Static",   "Static",   "KEYFRAME",     0), 
        ("Dynamic", "Dynamic",  "Dynamic",  "KEYFRAME_HLT", 1) 
    ]

def updateGridAndLevi(self, context) -> None:
    mp_props = bpy.context.scene.mp_props
    syncX = mp_props.NU_xml_gridAndLeviX
    syncY = mp_props.NU_xml_gridAndLeviY
    mp_props.NU_xml_gridX = syncX
    mp_props.NU_xml_gridY = syncY
    mp_props.NU_xml_leviX = syncX
    mp_props.NU_xml_leviY = syncY
    
    

def updateConvertProgressBar(self, context):
    mp_props = bpy.context.scene.mp_props
    
    converted = mp_props.NU_fbx_convertedRaw
    toConvert = mp_props.NU_fbx_toConvert
    mp_props.NU_fbx_converted = int(converted / toConvert * 100) if converted > 0 else 0
    redrawPanel(self, context)



def getFBXImportType() -> list:
    return [
        ("FOLDER",      "From Folder XYZ",      "Multiple",             "DOCUMENTS",        0),
        ("FOLDER_ITEMS","From /Work/Items/",    "All in /Work/Items/",  "FILE_FOLDER",      1),
        ("FILE",        "Single FBX",           "Single FBX",           "FILE",             2),
    ]
    
def getImportPatternType() -> list:
    return [
        ("REGEX",       "Regex",        "Select files by regex, like ^start.*(_#9)$",   "SORTBYEXT",    0),
        ("SIMPLE",      "Simple",       "Select files by Prefix, Suffix or Infix",      "SORTALPHA",    1),
        ("NONE",        "None",         "Select all FBX files",                         "DOCUMENTS",    2),
    ]



def redrawPanel(self, context):
    try:    context.area.tag_redraw()
    except  AttributeError: pass #works fine but spams console full of errors... yes
    

#region acronyms
#? CB = CheckBox
#? LI = List
#? FI = File
#? FO = Folder
#? NU = Number
#? ST = String
#endregion acronyms

class MP_Properties_for_Panels(bpy.types.PropertyGroup):
    """general maniaplanet properties"""
    # general
    FI_nadeoIni         : StringProperty(subtype="FILE_PATH")
    FO_MPdocPath        : StringProperty(subtype="DIR_PATH")
    FI_importMatXMLPath : StringProperty(subtype="FILE_PATH")
    CB_selectedItemsOnly: BoolProperty( name="Selected items only",  default=False)
    
    
    #help
    CB_copy_assets          : BoolProperty(name="Copy assets",  default=True)
    CB_copy_textures        : BoolProperty(name="Copy textures",  default=True)
    CB_copy_overwriteAssets : BoolProperty(name="Overwrite existing files",  default=False)
    CB_copy_onlyDiffuseTex  : BoolProperty(name="Copy only *D.dds)",  default=True)
    CB_copy_texStadium      : BoolProperty(name="Stadium",  default=True)
    CB_copy_texCanyon       : BoolProperty(name="Canyon",   default=True)
    CB_copy_texValley       : BoolProperty(name="Valley",   default=True)
    CB_copy_texLagoon       : BoolProperty(name="Lagoon",   default=True)
    CB_copy_texShootmania   : BoolProperty(name="ShootMania",default=True)
    
    
    #materials
    LI_mat_createUpdate:EnumProperty(   name="Cre/Update",  items=getMatCreateType())
    ST_mat_name:        StringProperty( name="Name",        default="IcePlatform")
    LI_mat_model:       EnumProperty(   name="Model",       items=getMatModels())
    LI_mat_envi:        EnumProperty(   name="Envi",        items=getMatEnvies(), description="Envi of material", update=updateNadeoMatEnviList)
    LI_mat_texFolders:  EnumProperty(   name="Envi",        items=getMatTextureSourceFolders, description="Folders with prefix TEX_ and NADEO TEXTURES in /Items/_BlenderAssets/")
    LI_mat_physic:      EnumProperty(   name="Physic",      items=getMatPhysics)
    FI_mat_btex:        StringProperty( name="TexName",     description="Select custom _D/S/N/I dds texture in /Items/", subtype="FILE_PATH", update=lambda s,c: fixCustomTexSrcPath(s,c,"FI_mat_btex"))
    LI_mat_btex:        EnumProperty(   name="TexName",     items=getNadeoMatsFromLIB)
    LI_mat_type:        EnumProperty(   name="Type",        items=getMatType(), update=setMatModelToTDSN)
    
    LI_mat_matList:     EnumProperty(   name="Mats",        items=getExistingMats, update=setPropsOFMatToChange)
    ST_mat_newName:     StringProperty( name="Name", )
    LI_mat_newModel:    EnumProperty(   name="Model",       items=getMatModels())
    FI_mat_newBTex:     StringProperty( name="TexName",     default="StadiumPlatform", description="Texture name/path or nadeolib material name", update= lambda s, c: updateMatType(s, c, "FI_mat_newBTex") , subtype="FILE_PATH")
    LI_mat_newPhysic:   EnumProperty(   name="Physic",      items=getMatPhysics)
    
    
    #make icon 
    NU_icon_margin      : IntProperty(name="Icon space usage", default=85, min=25, max=100, subtype="PERCENTAGE")
    NU_icon_camPosScale : FloatProperty(name="Cam position & scale", default=64.0, min=0,  max=256, step=100, update=setIconCamByChange)
    LI_icon_camPos      : EnumProperty(items=getIconCamPos(), name="Camera position/angle", update=setIconCamByChange)
    LI_icon_resInPX     : EnumProperty(items=getIconDimensions(), name="Icon dimension in pixels", update=setRenderRes)
    CB_icon_onlySelObjs : BoolProperty( name="Selected objects only",  default=False)


    #export fbx
    CB_fbx_showConvStatus   : BoolProperty( name="Generate Icons",          default=False)
    CB_fbx_genIcon          : BoolProperty( name="Generate Icons",          default=False)
    CB_fbx_convertLOCK      : BoolProperty( name="lock write",              default=False)
    CB_fbx_onlySelObjs      : BoolProperty( name="Selected objects only",   default=False)
    CB_fbx_stopConvert      : BoolProperty( name="Stop convert",            default=False)
    LI_fbx_validObjTypes    : EnumProperty( name="Objtype to export",   items=getExportObjTypes)
    LI_fbx_expType          : EnumProperty( name="Action",              items=getExportTypes)
    NU_fbx_toConvert        : IntProperty(  name="Items to convert",    min=0,  max=100000, step=1, update=redrawPanel)
    NU_fbx_converted        : IntProperty(  name="Converted items",     min=0,  max=100,    step=1, update=redrawPanel, subtype="PERCENTAGE")
    NU_fbx_convertedRaw     : IntProperty(  name="Converted items",     min=0,  max=100000, step=1, update=updateConvertProgressBar,)
    NU_fbx_convertsFail     : IntProperty(  name="Failed converts",     min=0,  max=100000, step=1, update=redrawPanel,)
    NU_fbx_convertsSuccess  : IntProperty(  name="Suceed converts",     min=0,  max=100000, step=1, update=redrawPanel,)
    
    
    #export xml
    CB_xml_syncGridLevi : BoolProperty(name="Sync Grid & Levi steps",   default=True)
    CB_xml_itemXMLNew   : BoolProperty(name="Use Custom",               default=True)
    CB_xml_genItemXML   : BoolProperty(name="Generate Item XML",        default=True)
    CB_xml_genMeshXML   : BoolProperty(name="Generate Mesh XML",        default=True)
    
    LI_xml_meshtype         : EnumProperty( name="Type",    items=getMeshXMLType())
    LI_xml_scale            : FloatProperty(name="Objscales", default=1.0, min=0, max=256, step=100)
    LI_xml_powerOfLights    : FloatProperty(name="Lightpowers",  default=1.0, min=0, max=256, step=1)
    CO_xml_lightglobcolor   : FloatVectorProperty(name='Color',  subtype='COLOR', min=0, max=1, step=1000, default=(0.0,0.319,0.855))
    CB_xml_lightglobcolor   : BoolProperty(name="Global Lightcolor", default=False)
    
    LI_xml_itemtype     : EnumProperty( name="Type",    items=getItemXMLType())
    LI_xml_waypointtype : EnumProperty( name="Waypoint",items=getWayPointVariations())
    LI_xml_enviType     : EnumProperty( name="Envi",    items=getItemXMLCollections())
    ST_xml_author       : StringProperty(name="Author", default="skyslide")
    NU_xml_gridAndLeviX : FloatProperty(name="Sync X",          default=32.0, min=0, max=256, step=100, update=updateGridAndLevi)
    NU_xml_gridAndLeviY : FloatProperty(name="Synx Y",          default=32.0, min=0, max=256, step=100, update=updateGridAndLevi)
    NU_xml_gridX        : FloatProperty(name="X Grid",          default=32.0, min=0, max=256, step=100)
    NU_xml_gridXoffset  : FloatProperty(name="X Offset",        default=0.0,  min=0, max=256, step=100)
    NU_xml_gridY        : FloatProperty(name="Y Grid",          default=8.0,  min=0, max=256, step=100)
    NU_xml_gridYoffset  : FloatProperty(name="Y Offset",        default=0.0,  min=0, max=256, step=100)
    NU_xml_leviX        : FloatProperty(name="X Levitation",    default=0.0,  min=0, max=256, step=100)
    NU_xml_leviXoffset  : FloatProperty(name="X Offset",        default=0.0,  min=0, max=256, step=100)
    NU_xml_leviY        : FloatProperty(name="Y Levitation",    default=0.0,  min=0, max=256, step=100)
    NU_xml_leviYoffset  : FloatProperty(name="Y Offset",        default=0.0,  min=0, max=256, step=100)
    CB_xml_ghostMode    : BoolProperty(name="Ghostmode",        default=True)
    CB_xml_autoRot      : BoolProperty(name="Autorot",          default=False)
    CB_xml_oneAxisRot   : BoolProperty(name="OneAxisRot",       default=False)
    CB_xml_notOnItem    : BoolProperty(name="Not on Item",      default=False)
    CB_xml_pivots       : BoolProperty(name="Pivots",           default=False)
    CB_xml_pivotSwitch  : BoolProperty(name="Pivot switch",     default=False)
    NU_xml_pivotSnapDis : FloatProperty(name="Pivot snap distance", default=8.0,  min=0, max=256, step=100)


    #fbx import
    LI_fbx_importType       : EnumProperty(name="Import",       items=getFBXImportType())
    ST_fbx_importDirPath    : StringProperty(name="Folder",     subtype="DIR_PATH", description="Select a Folder to import")
    ST_fbx_importFilePath   : StringProperty(name="File",       subtype="FILE_PATH",description="Select a File to import")
    CB_fbx_importSubFolders : BoolProperty(name="Include Subfolders", default=True)
    LI_fbx_importPatternType: EnumProperty(name="Pattern",       items=getImportPatternType())
    ST_fbx_importRegex      : StringProperty(name="Regex",      default="^start.*(_#[6-9])$",   description="Regex syntax, learn at regex101.com")
    CB_fbx_importRegex_I    : BoolProperty(name="Case insensitive", default=True)
    ST_fbx_importPrefix     : StringProperty(name="Prefix", default="_Start",   description="Prefix like 'Start_' in 'Start_Platform32x8_#9'")
    ST_fbx_importSuffix     : StringProperty(name="Suffix", default="_#9",      description="Su like '_#9' in 'Start_Platform32x8_#9'")
    ST_fbx_importInfix      : StringProperty(name="Infix",  default="Platform", description="Infix like 'Platform' in 'Start_Platform32x8_#9'")



class MP_Properties_Generated(PropertyGroup):
    """maniaplanet properties generated"""
    ST_matPhysicsId :  StringProperty(name="PhysicsId",         default="Concrete")
    ST_matName :       StringProperty(name="Mat Name",          default="")
    ST_matModel:       StringProperty(name="Mat Model",         default="TDSN")
    ST_matBTex :       StringProperty(name="Mat BaseTexture",   default="StadiumPlatform")
    CB_matBool :       BoolProperty(name="mat name not set yet",default=False)
    

class MP_Properties_Pivots(PropertyGroup):
    """maniaplanet properties generated for pivots (item xml)"""
    NU_pivotX   : FloatProperty(name="X", default=0.0, min=-1024, max=1024, soft_min=-8, soft_max=8, step=10)
    NU_pivotY   : FloatProperty(name="Y", default=0.0, min=-1024, max=1024, soft_min=-8, soft_max=8, step=10)
    NU_pivotZ   : FloatProperty(name="Z", default=0.0, min=-1024, max=1024, soft_min=-8, soft_max=8, step=10)
    
    
class MP_ItemConvertStatus(PropertyGroup):
    """maniaplanet properties for the convert progress, status"""
    ST_fbx_toConvert        : StringProperty(name="fbxname", default="")
    CB_fbx_convertFailed    : BoolProperty(name="status",   default=False)
    CB_fbx_convertDone      : BoolProperty(name="status",   default=False)
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    