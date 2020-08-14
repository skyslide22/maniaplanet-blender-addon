import bpy
import os
import re
import math
import configparser # -> use json
import json
import uuid
from sys import platform
import webbrowser
from inspect import currentframe, getframeinfo
import bpy.utils.previews
from bpy.types import UIList 





"""ADDON SETTINGS, read addon settings from settings.json, convert to dict"""
addonSettingsFile   = open("settings.json", "r", encoding="utf-8")
addonSettings       = json.load(addonSettingsFile)
addonSettingsFile.close()

# -------

errorMsgAbsolutePath = addonSettings["errorMsgAbsolutePath"]
errorMsgNadeoIni     = addonSettings["errorMsgNadeoIni"]
spacerFac            = addonSettings["UISpacerFactor"]

website_documentation   = addonSettings["website_documentation"]
website_bugreports      = addonSettings["website_bugreports"]
website_github          = addonSettings["website_github"]
website_regex           = addonSettings["website_regex"]
desktopPath             = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') + "/"
website_convertreport   = desktopPath + "convert_report.html"

maniaplanetTextureZipFiles = addonSettings["maniaplanetTextureZipFiles"]
missingPhysicsInLib = addonSettings["missingPhysicsInLib"]
favPhysicIds = addonSettings["favPhysicIds"]

notAllowedColnames = addonSettings["notAllowedColnames"]
# -----

"""NADEO.INI DATA"""
nadeoIniSettings = {}


def getNadeoIniFilePath() -> str:
    return bpy.context.scene.mp_props.FI_nadeoIni.replace("\\", "/")



def getNadeoIniData(setting: str) -> str:
    """return setting, if setting is not in dict nadeoIniSettings, read nadeo.ini and add it"""
    wantedSetting = setting
    possibleSettings = ["WindowTitle", "Distro", "Language", "UserDir", "CommonDir"]
    
    try:
        return nadeoIniSettings[setting]
    
    except KeyError:
        iniData = configparser.ConfigParser()
        iniData.read(getNadeoIniFilePath())
        
        for setting in possibleSettings:
            if setting not in nadeoIniSettings.keys():
                nadeoIniSettings[setting] = iniData.get("ManiaPlanet", setting)
        
        for key, value in nadeoIniSettings.items():
            if value.startswith("{exe}"):
                nadeoIniSettings[key] = value.replace(
                    "{exe}", 
                    getNadeoIniFilePath().replace("Nadeo.ini", "")
                ) + "/"
                # print(nadeoIniSettings[key])
            
        return nadeoIniSettings[wantedSetting]   



def getManiPlanetMainPath() -> str:
    return getNadeoIniFilePath().replace("/Nadeo.ini", "/")



def createFolderIfNecessary(path) -> None:
    """create given folder if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)



def doesFileExist(filepath) -> bool:
    return os.path.isfile(filepath)



def isIniValid() -> bool:
    """return bool, if Nadeo.ini file is selected.."""
    return bpy.context.scene.mp_props.FI_nadeoIni.endswith("Nadeo.ini")



def chooseNadeoIniPathFirstMessage(row) -> object:
    return row.label(text="Select Nadeo.ini file first.", icon="ERROR")



def getAddonPath() -> str:
    return os.path.dirname(__file__) + "/"



def getDocPath() -> str:
    """return absolute path of maniaplanet documents folder"""
    return getNadeoIniData(setting="UserDir")



def getDocPathItems() -> str:
    """return absolute path of ../Items/"""
    return getDocPath() + "/Items/"



def getDocPathWorkItems() -> str:
    """return absolute path of ../Work/Items/"""
    return getDocPath() + "/Work/Items/"



def getDocPathItemsAssets() -> str:
    """return absolute path of ../_BlenderAssets/"""
    return str(getDocPathItems() + "/_BlenderAssets/").replace("\\","/")



def getNadeoImporterPath() -> str:
    """return full file path of /xx/NadeoImporter.exe"""
    return getManiPlanetMainPath() + "/NadeoImporter.exe"



def getNadeoImporterLIBPath() -> str:
    """return full file path of /xx/NadeoImporterMaterialLib.txt"""
    return getManiPlanetMainPath() + "/NadeoImporterMaterialLib.txt"



def r(v) -> float:
    """return math.radians, example: some_blender_object.rotation_euler=(radian, radian, radian)"""
    return math.radians(v)



def getListOfFoldersInX(folderpath: str, prefix="") -> list:
    """return (only) names of folders which are in the folder given as argument"""
    folders = []
    for folder in os.listdir(folderpath):
        if os.path.isdir(folderpath + "/" + folder):
            if prefix != "":
                if folder.startswith(prefix):
                    folders.append(folder)
            else:
                folders.append(folder)
    
    return folders



def deselectAll() -> None:
    """deselects all objects in the scene, works only for visible ones"""
    for obj in bpy.context.scene.objects:
        obj.select_set(False)
        
def selectAll() -> None:
    """selects all objects in the scene, works only for visible ones"""
    for obj in bpy.context.scene.objects:
        try:    obj.select_set(True)
        except: pass
        
def hideAll() -> None:
    """hide all objects in scene (obj.hide_viewport, obj.hide_render)"""
    allObjs = bpy.context.scene.objects
    for obj in allObjs:
        obj.hide_render     = True
        obj.hide_viewport   = True

def unhideSelected(objs: list) -> None:
    """unhide objs in list, expect [ {"name":str, "render":bool, "viewport": bool} ]"""
    allObjs = bpy.context.scene.objects
    for obj in objs:
        allObjs[obj["name"]].hide_render    = obj["render"] 
        allObjs[obj["name"]].hide_viewport  = obj["viewport"]


def setActiveObj(objname: str) -> None:
    """set active object"""
    bpy.context.view_layer.objects.active = bpy.data.objects[objname]
    bpy.context.scene.objects[objname].select_set(True)
    
def unsetActiveObj() -> None:
    """unset active object, deselect all"""
    bpy.context.view_layer.objects.active = None
    deselectAll()


def setActiveCollection(colname: str) -> None:
    """set active scene collection by name, used by item import"""
    layer_collection = bpy.context.view_layer.layer_collection.children[colname]
    bpy.context.view_layer.active_layer_collection = layer_collection
    


def selectAllObjectsInACollection(colname: str) -> None:
    """select all objects in a collection, you may use deselectAll() before"""
    objs = bpy.data.collections[colname].all_objects
    for obj in objs: 
        obj.select_set(True)
            
          
            
def getCollectionNamesFromVisibleObjs() -> list:
    """returns list of collection names of all visible objects in the scene"""
    objs = bpy.context.scene.objects
    return [col.name for col in (obj.users_collection for obj in objs)]



def getCollectionHierachyOfObj(objname: str, hierachystart: bool=False) -> list:
    """returns list of parent collection of the given object name"""
    cols    = bpy.context.scene.objects[objname].users_collection
    colname = cols[0].name
    
    if hierachystart is True:
        hierachystart = [colname]
    else:
        hierachystart = []
        
    return getCollectionHierachy(colname=cols[0].name, objname=objname, hierachystart=hierachystart)
    
    

def getCollectionHierachy(colname: str="", objname: str="No_Name", hierachystart: list=[]) -> list:
    """returns list of parent collection names from given collection name,"""
    hierachy = hierachystart
    sceneCols = bpy.data.collections
    
    def scanHierachy(colname):
        for currentCol in sceneCols:
            for childCol in currentCol.children:
                if childCol.name == colname:
                    hierachy.append(currentCol.name)
                    scanHierachy(colname=currentCol.name)
    
    scanHierachy(colname=colname)
    hierachy.reverse()
    return hierachy



def checkMatValidity(matname: str) -> str("missing prop as str or True"):
    """check material for properties, retrurn True if all props are set, else return False"""
    
    mat = bpy.data.materials[matname]
    matprops = mat.keys()

    if "BaseTexture"  not in matprops: return False #"BaseTexture"  
    if "PhysicsId"    not in matprops: return False #"PhysicsId" 
    if "Model"        not in matprops: return False #"Model" 
    if "IsNadeoMat"   not in matprops: return False #"IsNadeoMat" 
    return True



nadeoLibMaterials = {}
def nadeoLibParser() -> dict:
    """read NadeoImporterMaterialLib.txt and return list of all materials as dict"""
    global nadeoLibMaterials #create global variable to read and parse liffile only once
    
    if nadeoLibMaterials != {}:
        return nadeoLibMaterials
    
    nadeolibfile = getNadeoImporterLIBPath()
    
    libs = []
    mp_props = bpy.context.scene.mp_props
    envi = mp_props.LI_mat_envi
    lib = {}
    currentLib = ""
    currentMat = ""
    regex_DLibrary      = r"DLibrary\t*\((\w+)\)"           # group 1
    regex_DMaterial     = r"DMaterial\t*\((\w+)\)"          # group 1
    regex_DSurfaceId    = r"DSurfaceId(\t*|\s*)\((\w+)\)"   # group 2
    regex_DTexture      = r"DTexture(\t*|\s*)\((\t*|\s*)([0-9a-zA-Z_\.]+)\)"   # group 3

    with open(nadeolibfile, "r") as f:
        for line in f:
            
            if "DLibrary" in line:
                currentLib = re.search(regex_DLibrary, line).group(1) #livname (stadium, canyon, ...)
            
            if currentLib not in lib:
                lib[currentLib] = {} #first loop
                
            if "DMaterial" in line:
                currentMat = re.search(regex_DMaterial, line).group(1) #matname
                lib[currentLib][currentMat] = {
                        "MatName":currentMat,
                        "PhysicsId":"Concrete" #changed below, fallback if not
                    }
                    
            if "DSurfaceId" in line:
                currentPhy = re.search(regex_DSurfaceId, line).group(2) #pyhsicid
                lib[currentLib][currentMat]["PhysicsId"] = currentPhy
                
            if "DTexture" in line:
                mat      = lib[currentLib][currentMat]
                nadeoTex = re.search(regex_DTexture, line)
                nadeoTex = "" if nadeoTex is None else nadeoTex.group(3) #texture
                mat["NadeoTexD"] = "" if "NadeoTexD" not in mat.keys() else mat["NadeoTexD"]
                mat["NadeoTexS"] = "" if "NadeoTexS" not in mat.keys() else mat["NadeoTexS"]
                mat["NadeoTexN"] = "" if "NadeoTexN" not in mat.keys() else mat["NadeoTexN"]
                mat["NadeoTexI"] = "" if "NadeoTexI" not in mat.keys() else mat["NadeoTexI"]
                
                if mat["NadeoTexD"] == "":  mat["NadeoTexD"] = nadeoTex if nadeoTex.lower().endswith("d.dds")  else ""  
                if mat["NadeoTexS"] == "":  mat["NadeoTexS"] = nadeoTex if nadeoTex.lower().endswith("s.dds")  else ""  
                if mat["NadeoTexN"] == "":  mat["NadeoTexN"] = nadeoTex if nadeoTex.lower().endswith("n.dds")  else ""  
                if mat["NadeoTexI"] == "":  mat["NadeoTexI"] = nadeoTex if nadeoTex.lower().endswith("i.dds")  else ""  
            
            if currentLib != "":
                if currentMat !="":
                    if currentMat in lib[currentLib].keys():
                        lib[currentLib][currentMat]["Model"] = "TDSN" #can't read model from lib
                        lib[currentLib][currentMat]["Envi"]  = currentLib 
                    

    
    nadeoLibMaterials = lib
    return nadeoLibMaterials
    
    
    
def fixName(name: str) -> str:
    """return modified name\n
    replace chars which are not allowed with _ or #, fix ligatures: ä, ü, ö, ß, é. \n  
    allowed chars: abcdefghijklmnopqrstuvwxyz0123456789_-#"""

    allowedNameChars = list("abcdefghijklmnopqrstuvwxyz0123456789_-#")
    fixedName = str(name)
    
    for char in name:
        charOriginal = str(char)
        char = str(char).lower()
        if char not in allowedNameChars:
            fixedChar = "_"
            if char == "ä": fixedChar = "ae"
            if char == "ö": fixedChar = "oe"
            if char == "ü": fixedChar = "ue"
            if char == "é": fixedChar = "e"
            if char == "ß": fixedChar = "ss"
            fixedName = fixedName.replace(charOriginal, fixedChar)
            
    return fixedName



def fixAllMatNames() -> None:
    """fixes not allowed chars for every material's name"""
    mats = bpy.data.materials
    for mat in mats:
        mat.name = fixName(name=mat.name)



def fixSlash(filepath) -> str:
    filepath = re.sub(r"\\+", "/", filepath)
    filepath = re.sub(r"\/+", "/", filepath)
    return filepath



def fixAllColNames() -> None:
    """fixes name for every collection in blender"""
    cols = bpy.data.collections
    for col in cols:
        try:    col.name = fixName(col.name)
        except: pass #mastercollection etc is readonly
    



def rgbToHEX(r,g,b, hashtag: str="") -> str:
    """return rgb (0 to 1.0) to hex as str"""
    if type(r) == float:    r = int(r*255)
    if type(g) == float:    g = int(g*255)
    if type(b) == float:    b = int(b*255)
        
    r = max(0, min(r, 255))
    g = max(0, min(g, 255))
    b = max(0, min(b, 255))
    
    hex = f"{hashtag}{r:02x}{g:02x}{b:02x}"
    return hex




def refreshPanels() -> None:
    """refresh panel in ui, they are not updating sometimes"""
    for region in bpy.context.area.regions:
        if region.type == "UI":
            region.tag_redraw()   
      
            

def fileNameOfPath(path: str) -> str:
    """return <tex.dds> of C:/someFolder/anotherOne/tex.dds, path can contain \\ and /"""
    return fixSlash(filepath=path).split("/")[-1]


def pro__print(*args) -> None:
    """better printer, adds line and filename as prefix"""
    frameinfo = getframeinfo(currentframe().f_back)
    line = str(frameinfo.lineno)
    name = str(frameinfo.filename).split("\\")[-1]
    
    line = line if int(line) > 10       else line + " " 
    line = line if int(line) > 100      else line + " " 
    line = line if int(line) > 1000     else line + " " 
    line = line if int(line) > 10000    else line + " " 
    # line = line if int(line) > 100000   else line + " " 
    
    print(f"{line}, {name} --", end="")
    for arg in args:
        print(", " + str(arg), end="")
    print()

           
           
           
           
           
preview_collections = {}

iconsDir = os.path.join(os.path.dirname(__file__), "icons")
pcoll = bpy.utils.previews.new()


def getIcon(icon: str) -> object:
    """return icon for layout (row, col) parameter: 
        icon_value=getIcon('CAM_FRONT') / icon='ERROR'"""
    if icon not in pcoll.keys():
        pcoll.load(icon, os.path.join(iconsDir, icon + ".png"), "IMAGE")
    return pcoll[icon].icon_id
           
                
                
def generateUID() -> str:
    """generate unique id and return as string"""               
    return str(uuid.uuid4())
                
                
                
def func() -> None:
    """development stuff, can not access bpy.data stuff while reload script, so add delay of 1s"""
    pass

# timer = bpy.app.timers.register(func, first_interval=1)
















def makeReportPopup(title= str("some error occured"), infos=[], icon='INFO', fileName="maniaplanet_report"):
    if platform == "darwin": return

    def draw(self, context):
        self.layout.label(text=f"This report is saved at: {desktopPath} as {fileName}.txt", icon="FILE_TEXT")
        for info in infos:
            self.layout.label(text=info)       
              
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
    
    with open(desktopPath + fileName + ".txt", "w", encoding="utf-8") as reportFile:
        if len(infos) > 0:
            for info in infos:
                # print("info: ", info)
                reportFile.write(info + "\n")
        else:
            reportFile.write("No relevant infos...")



