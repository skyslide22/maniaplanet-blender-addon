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
from .MP_Items_Import   import *



class MP_OT_Items_Export_ExportAndOrConvert(Operator):
    """export and or convert an item"""
    bl_idname = "view3d.exportfbx"
    bl_description = "Execute Order 66"
    bl_icon = 'MATERIAL'
    bl_label = "Export or/and Convert"
        
    def execute(self, context):
        pro__print("CALL EXPORT FUNCTION")
        exportAndConvertMainFunction()
        return {"FINISHED"}
    
    
class MP_OT_Items_Export_OpenConvertReport(Operator):
    """open convert report"""
    bl_idname = "view3d.openconvreport"
    bl_description = "Execute Order 66"
    bl_icon = 'MATERIAL'
    bl_label = "Export or/and Convert"
        
    def execute(self, context):
        openHelp("convertreport")
        return {"FINISHED"}



class MP_PT_Items_Export(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_category = 'ManiaPlanetAddon'
    bl_label = "Export & Convert FBX"
    bl_idname = "MP_PT_Items_Export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    # endregion
    def draw(self, context):

        layout = self.layout
        mp_props        = context.scene.mp_props
        
        if not isIniValid():
            row = layout.row().label(text=errorMsgNadeoIni, icon="ERROR")
            return
        
        actionIsExport          = mp_props.LI_fbx_expType == "EXPORT"
        actionIsConvert         = mp_props.LI_fbx_expType == "CONVERT"
        actionIsExportConvert   = mp_props.LI_fbx_expType == "EXPORT_CONVERT"
        convertRunning          = mp_props.CB_fbx_showConvStatus
        
        
        if actionIsExport or actionIsExportConvert and not convertRunning:            
            row = layout.row().prop(mp_props, "LI_fbx_expType",)
            row = layout.row().prop(mp_props, "LI_fbx_validObjTypes",)
            row = layout.row().prop(mp_props, "CB_fbx_onlySelObjs")
            row = layout.row().prop(mp_props, "CB_fbx_genIcon")
            
            row = layout.row()
            row.enabled = True
            row.scale_y = 1.5
            row.operator("view3d.exportfbx", text=mp_props.LI_fbx_expType, icon="EXPORT")
        
        
        if actionIsConvert and not convertRunning:
            row = layout.row().prop(mp_props, "LI_fbx_expType",)
            row = layout.row(align=True)
            row.prop(mp_props, "ST_fbx_importDirPath", text="Folder")
            row.prop(mp_props, "CB_fbx_importSubFolders", text="", icon="FOLDER_REDIRECT")
            
            if not "Work/Items" in fixSlash(mp_props.ST_fbx_importDirPath):
                row = layout.row().label(text="Choose a Folder in /Work/Items/ !")
                return
            
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
            row.enabled = True
            row.scale_y = 1.5
            row.operator("view3d.exportfbx", text=mp_props.LI_fbx_expType, icon="EXPORT")
        
            

        
        if mp_props.CB_fbx_showConvStatus:
            
            stopConvert = mp_props.CB_fbx_stopConvert
            convertDone = mp_props.NU_fbx_toConvert == mp_props.NU_fbx_convertedRaw
            
            row = layout.row()
            row.enabled = True if any([stopConvert, convertDone]) else False
            row.prop(mp_props, "CB_fbx_showConvStatus", toggle=True, text="OK")
            
            row = layout.row(align=True)
            row.operator("view3d.openconvreport", text="Open failreports")
            row.prop(mp_props, "CB_fbx_stopConvert",    toggle=True)
            row = layout.row()
            
            row.prop(mp_props, "NU_fbx_converted")
            row.enabled = False
            
            atleastOneFail  = mp_props.NU_fbx_convertsFail > 0
            converted       = mp_props.NU_fbx_convertedRaw
            toConvert       = mp_props.NU_fbx_toConvert
            convertDone     = converted == toConvert
            iconRunning     = "COLORSET_13_VEC"
            iconFail        = "COLORSET_01_VEC"
            iconSuccess     = "COLORSET_03_VEC"
            
            convertstatus = iconFail if atleastOneFail else iconRunning if not convertDone else iconSuccess
            
            row = layout.row()
            row.label(text="Done: " + str(mp_props.NU_fbx_convertedRaw) + " / " + str(mp_props.NU_fbx_toConvert)) #
            row.label(text="Fail: " + str(mp_props.NU_fbx_convertsFail), icon=convertstatus)

            
 
        
def exportAndConvertMainFunction() -> None:
    """export&convert fbx main function, call all other functions on conditions set in UI"""
    mp_props = bpy.context.scene.mp_props
    colsToExport    = []
    validObjTypes   = mp_props.LI_fbx_validObjTypes
    useSelectedOnly = mp_props.CB_fbx_onlySelObjs
    invalidColNames = ["master collection", "collection", "scene"]
    allObjs         = bpy.context.scene.objects
    cols            = bpy.context.scene.collection.children
    action          = mp_props.LI_fbx_expType
    exportedFBXs    = []
    
    fixAllColNames()
    
    if action == "EXPORT" or action == "EXPORT_CONVERT":
        
        mp_props.CB_fbx_showConvStatus  = False if action == "EXPORT" else True
        mp_props.CB_fbx_stopConvert     = False
        
        #generate list of collections to export
        for obj in allObjs:
            
            name = obj.name.lower()
            if name.startswith("cp") or name.startswith("checkpoint"):    obj.name = "_socket_CHECKPOINT"
            if name.startswith("multilap"):     obj.name = "_socket_MULTILAP"
            if name.startswith("finish"):       obj.name = "_socket_FINISH"
            if name.startswith("start"):        obj.name = "_socket_START"
            if name.startswith("trigger"):      obj.name = "_trigger_"
            
            for col in obj.users_collection:
                if col.name.lower() not in invalidColNames:
                    if col.name not in colsToExport:    
                        if useSelectedOnly:
                            if obj.select_get() is True:
                                colsToExport.append(col.name)
                        else:
                            colsToExport.append(col.name)

        #remove doubles
        colsToExport = set(colsToExport)
        
        #generate icon by condition
        if mp_props.CB_fbx_genIcon is True:
            createIcons(colnames=colsToExport)

        #export each collection ...
        for col in colsToExport:
            cols = bpy.data.collections
            origin = setColObjsParentToOrigin(colname=col)
            oriObj = allObjs[origin]
            oriOldPos   = tuple(oriObj.location) #old pos of origin
            oriNewPos   = oriObj.location = (0,0,0) #center of world
            deleteOri  = True if "delete" in oriObj.name else False 
            
            #unparent all objects, convert relative transforms to parent to absolute to world
            for obj in cols[col].all_objects:
                if not obj.name.lower().startswith("origin"):
                    deselectAll()
                    obj.select_set(True)
                    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            
            selectAllObjectsInACollection(colname=col)
            
            fbxFilePath = fixSlash( getDocPathWorkItems() + "/".join( getCollectionHierachy(colname=col, hierachystart=[col]) ) + ".fbx" )
            exportFBX(fbxfilepath=fbxFilePath)
            exportedFBXs.append(fbxFilePath)
            
            #reset origin position from center to old location                
            setColObjsParentToOrigin(colname=col)
            oriObj.location = oriOldPos
            
            #unparent all objects, convert relative transforms to parent to absolute to world
            for obj in cols[col].all_objects:
                if not obj.name.lower().startswith("origin"):
                    deselectAll()
                    obj.select_set(True)
                    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            
            #delete created origin object, didn't exist before so: dont't keep it.
            if deleteOri:
                deselectAll()
                oriObj.select_set(True)
                bpy.ops.object.delete(use_global=False)
            
            unsetActiveObj()
            
            for fbx in exportedFBXs:
                pro__print("EXPORTED: ", fbx.split("/Work/")[-1])
            
            #generate item and meshxml
            if mp_props.CB_xml_genItemXML is True:
                colObjs = cols[col].all_objects
                wptypes = ["Start", "StartFinish", "Multilap", "Finish", "Checkpoint"]
                
                def getWaypoint() -> str("None or str"):
                    for obj in cols[col].all_objects:
                        for wptype in wptypes:
                            if obj.name.lower().startswith("_socket_" + wptype.lower()):
                                if wptype.lower() == "multilap":
                                    return "StartFinish"
                                return wptype
                
                waypointtype = getWaypoint()
                waypoint = bool(waypointtype)
                
                gennerateItemXML(fbxfilepath=fbxFilePath, waypoint=waypoint, waypointtype=waypointtype)
                
            if mp_props.CB_xml_genMeshXML is True: 
                gennerateMeshXML(fbxfilepath=fbxFilePath, colname=col)
                


        #convert each exported fbx file
        if action == "EXPORT_CONVERT":
            
            mp_props.NU_fbx_toConvert       = len(exportedFBXs)
            mp_props.NU_fbx_converted       = 0
            mp_props.NU_fbx_convertedRaw    = 0
            mp_props.NU_fbx_convertsFail    = 0
            mp_props.NU_fbx_convertsSuccess = 0
                        
            #run convert on second thread to avoid blender to freeze
            convert = Thread(target=startBatchConvert, args=[exportedFBXs]) 
            convert.start()
            

    
    if action == "CONVERT":
        mp_props.CB_fbx_showConvStatus  = True
        mp_props.CB_fbx_stopConvert     = False

        impPath         = mp_props.ST_fbx_importDirPath
        filesInSubDirs  = mp_props.CB_fbx_importSubFolders
        patternType     = mp_props.LI_fbx_importPatternType
        filesToConvert  = []

        for root, dirs, files in os.walk(impPath):    
            for file in files:
                if file.lower().endswith(".fbx"):
                    fileChecked = checkFileByPattern(file, patternType)
                    
                    if filesInSubDirs:
                        if fileChecked is not None:
                            filesToConvert.append(  fixSlash(root + "/" + file) )
                    
                    if not filesInSubDirs:
                        if fileChecked is not None:
                            filesToConvert.append(  fixSlash(impPath + "/" + file) )

        filesToConvert.sort()        
        mp_props.NU_fbx_toConvert       = len(filesToConvert)
        mp_props.NU_fbx_converted       = 0
        mp_props.NU_fbx_convertedRaw    = 0
        mp_props.NU_fbx_convertsFail    = 0
        mp_props.NU_fbx_convertsSuccess = 0
                        
        #run convert on second thread to avoid blender to freeze
        convert = Thread(target=startBatchConvert, args=[filesToConvert]) 
        convert.start()

    #end exportmainfunc



def setColObjsParentToOrigin(colname: str) -> str:
    """sets all object in a collection as child of obj named 'origin',
        create if necessary and return name of the empty called 'origin' (.001..)"""
    cols    = bpy.data.collections
    col     = cols[colname]
    oriObj  = None
    allObjs = bpy.data.objects
    
    for obj in col.all_objects:
        if obj.name.lower().startswith("origin"):
            oriObj = obj.name
    
    #create origin object if none exists, location at first object in collection.all_objects
    if oriObj is None:
        meshObjs = [obj for obj in col.all_objects if obj.type == "MESH"]
        createAt = meshObjs[0].location
        bpy.ops.object.empty_add(type='ARROWS', align='WORLD', location=createAt)
        newOri = bpy.context.active_object
        newOri.name = "origin_delete_" + generateUID()
        oriObj = newOri.name
        if oriObj not in col.objects:
            col.objects.link(allObjs[oriObj])
    
    #set parent of every object in the collection to the origin object
    #convert absolute transforms to relative transforms(parent)
    for obj in col.all_objects:
        if obj.name != oriObj:
            deselectAll()
            allObjs[oriObj  ].select_set(True)
            allObjs[obj.name].select_set(True)
            setActiveObj(oriObj)
            try:    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
            except: pass #RuntimeError: Error: Loop in parents
            
    return oriObj


def exportFBX(fbxfilepath) -> None:
    """exports fbx, creates filepath if it does not exist"""
    mp_props = bpy.context.scene.mp_props
    objTypes = mp_props.LI_fbx_validObjTypes.split("_") #MESH_LIGHT_EMPTY
    objTypes = {ot for ot in objTypes}
    
    createFolderIfNecessary(fbxfilepath[:fbxfilepath.rfind("/")]) #deltes all after last slash

    bpy.ops.export_scene.fbx(
        filepath              = fbxfilepath,
        object_types          = objTypes,
        use_selection         = True,
        use_custom_props      = True, #*not working for mats
        apply_unit_scale      = False,
        apply_scale_options   = "FBX_SCALE_UNITS"
    )


















        
        
        
        