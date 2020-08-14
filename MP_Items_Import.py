from os import name
import bpy
import os.path
import re
import subprocess
import shutil
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from bpy.props import (
    StringProperty,
    BoolProperty,
    PointerProperty,
    CollectionProperty
)
from bpy.types import (
    Panel,
    Operator,
    AddonPreferences,
    PropertyGroup
)
from .MP_Functions      import *
from .MP_Items_Convert  import *
from .MP_Items_XML      import *
from .MP_Icon_Create    import *
from .MP_Help           import *

itemsToConvert = []





class MP_OT_Items_Import(Operator):
    """import items (fbx)"""
    bl_idname = "view3d.importfbx"
    bl_description = "Execute Order 66"
    bl_icon = 'MATERIAL'
    bl_label = "Batch  FBX import "
        
    def execute(self, context):
        pro__print("CALL IMPORT FUNCTION")
        batchImportFBXMain()
        return {"FINISHED"}


class MP_OT_Items_Regex(Operator):
    """import items (fbx)"""
    bl_idname = "view3d.checkregex"
    bl_description = "Execute Order 66"
    bl_icon = 'MATERIAL'
    bl_label = "Check regex"
        
    def execute(self, context):
        pro__print("CALL IMPORT FUNCTION")
        openHelp("checkregex")
        return {"FINISHED"}
    

class MP_PT_Items_Import(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_category = 'ManiaPlanetAddon'
    bl_label = "Import FBX"
    bl_idname = "MP_PT_Items_Import"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    # endregion
    def draw(self, context):

        layout = self.layout
        mp_props        = context.scene.mp_props
        mp_props_pivots = context.scene.mp_props_pivots
        
        if not isIniValid():
            row = layout.row().label(text=errorMsgNadeoIni, icon="ERROR")
            return
        
        row = layout.row().prop(mp_props, "LI_fbx_importType")
        impType     = mp_props.LI_fbx_importType
        impFilePath = mp_props.ST_fbx_importFilePath
        impDirPath  = mp_props.ST_fbx_importDirPath
        
    
        if impType == "FOLDER_ITEMS":
            row = layout.row().prop(mp_props, "CB_fbx_importSubFolders")
            
            row = layout.row()
            row.scale_y = 1.5
            # row.alert = True
            row.operator("view3d.importfbx", text="Import from Root", icon="IMPORT")
        
        
        if impType == "FILE":
            row = layout.row().prop(mp_props, "ST_fbx_importFilePath")
            row = layout.row()
            row.scale_y = 1.5
            row.enabled = True if impFilePath.lower().endswith(".fbx") else False
            row.operator("view3d.importfbx", text="Import file", icon="FILE")
            
            
        if impType == "FOLDER":
            row = layout.row(align=True)
            row.prop(mp_props, "ST_fbx_importDirPath")
            row.prop(mp_props, "CB_fbx_importSubFolders", text="", icon="FOLDER_REDIRECT", toggle=True)
            row = layout.row().prop(mp_props, "LI_fbx_importPatternType")
            
            patternType = mp_props.LI_fbx_importPatternType
            
            if patternType == "SIMPLE":
                row = layout.row().label(text="Seperate by comma, empty to disable", icon="INFO")
                row = layout.row().prop(mp_props, "ST_fbx_importPrefix")
                row = layout.row().prop(mp_props, "ST_fbx_importSuffix")
                row = layout.row().prop(mp_props, "ST_fbx_importInfix")
                
            if patternType == "REGEX":
                row = layout.row(align=True)
                row.prop(mp_props, "ST_fbx_importRegex")
                row.prop(mp_props, "CB_fbx_importRegex_I", text="", toggle=True, icon="EVENT_I")
                row = layout.row().operator("view3d.checkregex", icon="URL")               
                
            
            row = layout.row()
            row.scale_y = 1.5
            row.enabled = True if "/" in fixSlash(impDirPath) else False
            row.operator("view3d.importfbx", text="Import from folder", icon="IMPORT")
            
        
        
        
def batchImportFBXMain() -> None:
    """main function which calls all other functions"""    
    # filesList       = getFilesToImport()
    # filesToImport   = filesList[0]
    
    # if len(filesToImport[0]) > 0:
    #     batchImportFBX(file=filesToImport, subdirs=fbxDirPathSubDirs)
        


def batchImportFBX(file: str, subdirs: bool) -> None:
    pass

       
        
def getFilesToImport() -> None:
    """(batch) import fbx from folder/file choosen in ui"""
    #set active collection to master collection collection
    #so new generated collections are child of master collection
    viewLayerMcol = bpy.context.view_layer.layer_collection
    bpy.context.view_layer.active_layer_collection = viewLayerMcol
    
    mp_props    = bpy.context.scene.mp_props
    cols        = bpy.data.collections
    sceneCols   = bpy.context.scene.collection.children
    
    fbxImpType         = mp_props.LI_fbx_importType
    fbxFilePath        = mp_props.ST_fbx_importFilePath
    fbxFilePatternPath = mp_props.ST_fbx_importDirPath #same for the moment
    fbxDirPath         = mp_props.ST_fbx_importDirPath
    fbxDirPathSubDirs  = mp_props.CB_fbx_importSubFolders
    
    fbxFilePrefix      = mp_props.ST_fbx_importPrefix.replace(" ", "").split(",")
    fbxFileSuffix      = mp_props.ST_fbx_importSuffix.replace(" ", "").split(",")
    fbxFileInfix       = mp_props.ST_fbx_importInfix.replace(" ",  "").split(",")
    
    fbxFilePatternType      = mp_props.LI_fbx_importPatternType
    fbxFilePatternRegex     = mp_props.ST_fbx_importRegex
    fbxFilePatternRegex_I   = mp_props.CB_fbx_importRegex_I

    
    
    if fbxImpType == "FILE":
        fbxname = re.sub(r"\.fbx", "", fileNameOfPath(path=fbxFilePath), flags=re.I) 
        col = cols.new(fbxname)
        sceneCols.link(col)
        setActiveCollection(colname=col.name)
        importFBXFile(fbxFilePath)
        fixImportedItemMats(colname=col.name)
    
    
    if fbxImpType == "FOLDER" or fbxImpType == "FOLDER_ITEMS":
        filesToImport = []
        
        if fbxImpType == "FOLDER_ITEMS":
            fbxDirPath = getDocPathWorkItems()
            
        if fbxDirPathSubDirs:
            for root, dirs, files in os.walk(fbxDirPath):
                                    
                for file in files:
                    if file.lower().endswith(".fbx"):
                        file = re.sub(r"\.fbx", "", file, flags=re.I)
                        
                        if fbxFilePatternType == "SIMPLE":
                            appendFile =  checkFileByPattern(filename=file, type="SIMPLE")
                            if appendFile is not None:
                                filesToImport.append( fixSlash(f"{root}/{file}") )
                                continue
     
                        if fbxFilePatternType == "REGEX":
                            appendFile =  checkFileByPattern(filename=file, type="REGEX")
                            if appendFile is not None:
                                filesToImport.append( fixSlash(f"{root}/{file}") )
                                continue
                                       
                        if fbxFilePatternType == "NONE":
                            filesToImport.append( fixSlash(f"{root}/{file}") )
        
        
        if not fbxDirPathSubDirs:
            fbxfiles = [file for file in os.listdir(fbxDirPath) if os.path.isfile(fbxDirPath + "/" + file)]
            for file in fbxfiles:
                
                if fbxFilePatternType == "SIMPLE":
                    appendFile =  checkFileByPattern(filename=file, type="SIMPLE")
                    if appendFile is not None:
                        filesToImport.append( fixSlash(f"{fbxDirPath}/{file}") )
                        continue

                if fbxFilePatternType == "REGEX":
                    appendFile =  checkFileByPattern(filename=file, type="REGEX")
                    if appendFile is not None:
                        filesToImport.append( fixSlash(f"{fbxDirPath}/{file}") )
                        continue
                                
                if fbxFilePatternType == "NONE":
                    filesToImport.append( fixSlash(f"{fbxDirPath}/{file}") )
        

        #remove doubles
        filesToImport = set(filesToImport)
        return filesToImport, fbxDirPathSubDirs
        
         

def checkFileByPattern(filename: str, type: str) -> str:
    """checks filename by pre/suf/infix or regex, return filename if true, else none. type="SIMPLE" or "REGEX" """
    mp_props = bpy.context.scene.mp_props
    fbxFilePrefix      = mp_props.ST_fbx_importPrefix.replace(" ", "").split(",")
    fbxFileSuffix      = mp_props.ST_fbx_importSuffix.replace(" ", "").split(",")
    fbxFileInfix       = mp_props.ST_fbx_importInfix.replace(" ",  "").split(",")
    fbxFilePatternType      = mp_props.LI_fbx_importPatternType
    fbxFilePatternRegex     = mp_props.ST_fbx_importRegex
    fbxFilePatternRegex_I   = mp_props.CB_fbx_importRegex_I
    
    if type == "SIMPLE":

        for prefix in fbxFilePrefix:
            if filename.lower().startswith(prefix.lower()):
                return filename
    
        for suffix in fbxFileSuffix:
            if filename.lower().endswith(suffix.lower()):
                return filename
    
        for infix in fbxFileInfix:
            if infix.lower() in filename.lower():
                return filename

    if type == "REGEX":
        useCaseInsensitive = re.I if fbxFilePatternRegex_I is True else 0
        if re.search(fbxFilePatternRegex, filename, flags=re.I) is not None:
            return filename
    
    return None



def importFBXFile(file):
    bpy.ops.import_scene.fbx(
        filepath=file,
        use_custom_props=True #!not working for mats
        )

        
        
def fixImportedItemMats(colname):
    mp_props = bpy.context.scene.mp_props    
    cols = bpy.data.collections
    mats = bpy.data.materials
    matRegex = r"\.\d{0,5}$" #finds the .001 in blaMaterialname.005
    
    for obj in cols[colname].all_objects:
        objmats = obj.material_slots
        if obj.type == "MESH":
            #enumerate takes 0 positional arguments, but 1 was given?!... use i.
            for i in range(0, len(objmats)):
                objmat = objmats[i]
                if re.search(matRegex, objmat.name):
                    existingMat = re.sub(matRegex, "", objmat.name) #remove .001
                    if existingMat in mats: 
                        obj.material_slots[i].material = mats[existingMat]















        
        
        
        