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
from .MP_Functions import *




    
class MP_OT_Help_CreateAssetFolderContent(Operator):
    bl_idname = "view3d.create_assetfoldercontent"
    bl_label = "help"
   
    def execute(self, context):
        createAssetFolderContent()
        return {"FINISHED"}


class MP_OT_Help_OpenItemsFolder(Operator):
    bl_idname = "view3d.open_itemsfolder"
    bl_label = "help"
   
    def execute(self, context):
        openHelp("itemsfolder")
        return {"FINISHED"}


class MP_OT_Help_OpenWorkItemsFolder(Operator):
    bl_idname = "view3d.open_workitemsfolder"
    bl_label = "help"
   
    def execute(self, context):
        openHelp("workitemsfolder")
        return {"FINISHED"}
    
    
class MP_OT_Help_OpenAssetFolder(Operator):
    bl_idname = "view3d.open_assetfolder"
    bl_label = "help"
   
    def execute(self, context):
        openHelp("assetfolder")
        return {"FINISHED"}
    

class MP_OT_Help_OpenDocumentation(Operator):
    bl_idname = "view3d.open_documentation"
    bl_label = "help"
   
    def execute(self, context):
        openHelp("documentation")
        return {"FINISHED"}


class MP_OT_Help_OpenBugreports(Operator):
    bl_idname = "view3d.open_bugreports"
    bl_label = "help"
   
    def execute(self, context):
        openHelp("bugreport")
        return {"FINISHED"}

   
class MP_PT_Help(Panel):
    # region bl_
    """Creates a Panel in the Object properties window"""
    bl_category = 'ManiaPlanetAddon'
    bl_label = "Help / Documentation"
    bl_idname = "OBJECT_PT_MP_Help"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    # endregion
    def draw(self, context):

        mp_props = context.scene.mp_props
        mats = bpy.data.materials
        
        layout = self.layout
                
        row = layout.row()
        row.scale_y = 1.5
        row.operator("view3d.open_documentation",   text="Open Documentation",  icon="URL")
        
        row = layout.row()
        row.operator("view3d.open_bugreports",      text="Bugreport on Github",  icon="FILE_SCRIPT")
        
        row = layout.row()
        row.separator(factor=spacerFac)
        row = layout.row()
        row.label(text="Select your Nadeo.ini file")

        row = layout.row()
        row.prop(mp_props, "FI_nadeoIni", text="")
        
        if not isIniValid():
            row = layout.row()
            row.label(text=errorMsgNadeoIni, icon="ERROR")
            return
        
        row = layout.row()
        row.separator(factor=spacerFac)
        
        col = layout.column()
        col.scale_y = 1.5
        col.operator("view3d.open_assetfolder",     text="Open Assets folder",  icon="FILE_FOLDER")
        col.operator("view3d.open_itemsfolder",     text="Open /Items/",        icon="FILE_FOLDER")
        col.operator("view3d.open_workitemsfolder", text="Open /Work/Items/",   icon="FILE_FOLDER")
        col = layout.column()
        
        
        row = layout.row()
        row.separator(factor=spacerFac)
        
        box = layout.box()
        
        row = box.row(align=True)
        row.prop(mp_props, "CB_copy_textures",  toggle=True)
        row.prop(mp_props, "CB_copy_assets",    toggle=True)

        row = box.row()
        row.prop(mp_props, "CB_copy_overwriteAssets", toggle=False)
        
        
        if mp_props.CB_copy_textures:

            row = box.row()
            row.separator(factor=spacerFac)

            row = box.row()
            row.label(text="Copy from environment:", icon="TEXTURE")
            
            col = box.column(align=True)
            row = col.row(align=True)
            
            row.prop(mp_props, "CB_copy_texStadium",    toggle=True)
            row.prop(mp_props, "CB_copy_texCanyon",     toggle=True)
            row.prop(mp_props, "CB_copy_texValley",     toggle=True)
            row = col.row(align=True)
            row.prop(mp_props, "CB_copy_texLagoon",     toggle=True)
            row.prop(mp_props, "CB_copy_texShootmania", toggle=True)
            
            row = box.row(align=True)
            row.prop(mp_props, "CB_copy_onlyDiffuseTex", toggle=False)
        
            row = box.row()
            row.separator(factor=spacerFac)
        
        row = box.row()
        row.scale_y = 1.5
        row.enabled = True if mp_props.CB_copy_textures or mp_props.CB_copy_assets else False
        row.operator("view3d.create_assetfoldercontent", text="Create Assetfolder Content",   icon="FILE_REFRESH")
        
        row = layout.row()
        row.separator(factor=spacerFac)



def openHelp(helptype: str) -> None:
    """open exporer or webbrowser by given helptype"""
    cmd = "" #+path
    
    if helptype == "workitemsfolder":   cmd += getDocPathWorkItems()
    if helptype == "itemsfolder":       cmd += getDocPathItems()
    if helptype == "assetfolder":       cmd += getDocPathItemsAssets()
    
    if helptype == "documentation": webbrowser.open(website_documentation)
    if helptype == "bugreport":     webbrowser.open(website_bugreports)
    if helptype == "checkregex":    webbrowser.open(website_regex)
    if helptype == "convertreport": subprocess.Popen(['start', fixSlash(website_convertreport)], shell=True)
    
        
    if cmd != "":
        cmd = f'explorer "{cmd}"'
        cmd = cmd.replace("/", "\\")
        cmd = cmd.replace("\\\\", "\\")
        subprocess.Popen(cmd, stdout=subprocess.PIPE)
        # print("explorercmd is: ", cmd)
    
   
    
def createAssetFolderContent() -> None:
    """copy addon assets to user assets folder, 
    also textures from maniaplanet packscache folder"""
    assetPathUser = getDocPathItemsAssets()
    assetPath = getAddonPath() + "/assets/user_assets/"
    mp_props = bpy.context.scene.mp_props
    
    
    for root, dirs, files in os.walk(assetPath):
        
        for folder in dirs:
            createFolderIfNecessary(assetPathUser + folder)
            
        for file in files:
            filePathRelative = root.replace(assetPath, "")  + "/" + file
            allowOverwriting = mp_props.CB_copy_overwriteAssets
            copy = doesFileExist(assetPathUser + filePathRelative)
            
            oldfile = assetPath + filePathRelative
            newfile = assetPathUser + filePathRelative
            
            if mp_props.CB_copy_overwriteAssets:
                shutil.copyfile(oldfile, newfile)
    
    copyManiaPlanetTexturesToAddonFolder()
    
    

def createAssetFolderTextures() -> None:
    """copy textures from maniaplanet packscache zipfiles to user asset folder"""
    
    
def copyManiaPlanetTexturesToAddonFolder():
    """copies textures which maniaplanet uses to addon folder (dds files)"""
    MPDataPath = getNadeoIniData(setting="CommonDir")
    assetPathUser = getDocPathItemsAssets()
        
    mp_props = bpy.context.scene.mp_props
    onlyDiffuse = mp_props.CB_copy_onlyDiffuseTex
    overwriteExisting = mp_props.CB_copy_overwriteAssets
    
    allowedEnvis = []
    if mp_props.CB_copy_texStadium:     allowedEnvis.append("Stadium")
    if mp_props.CB_copy_texCanyon:      allowedEnvis.append("Canyon")
    if mp_props.CB_copy_texValley:      allowedEnvis.append("Valley")
    if mp_props.CB_copy_texLagoon:      allowedEnvis.append("Lagoon")
    if mp_props.CB_copy_texShootmania:  allowedEnvis.append("Shootmania")
    
    # meme.DrakeFormat("Use a debugger", "print('line 218 reached')")
    
    for relativeZippath in maniaplanetTextureZipFiles:
        env = "Stadium"
        if "stadium"    in relativeZippath.lower():    env = "Stadium"
        if "canyon"     in relativeZippath.lower():    env = "Canyon"
        if "valley"     in relativeZippath.lower():    env = "Valley"
        if "lagoon"     in relativeZippath.lower():    env = "Lagoon"
        if "shootmania" in relativeZippath.lower():    env = "Shootmania"
    
        zippath = MPDataPath + relativeZippath
        
        if os.path.isfile(zippath):
                        
            textureZip      = ZipFile(zippath)
            textureZipFiles = textureZip.namelist()
            
            for ddsFileInZip in textureZipFiles:
                if f"{env}/Media/Texture/Image/" in ddsFileInZip:
                    
                    ddsFileName = ddsFileInZip.split("/")[-1]
                    ddsFilePath = f"{assetPathUser}/TEX_{env}/"
                    ddsFile     = f"{ddsFilePath}/{ddsFileName}"
                    
                    createFolderIfNecessary(path=ddsFilePath)
                        
                    if onlyDiffuse is True and ddsFileName.endswith("D.dds") is False:
                        continue 
                    
                    if env not in allowedEnvis:
                        continue
                    
                    writeNewDDS = True
                    
                    if not overwriteExisting:
                        writeNewDDS = False if os.path.isfile(ddsFile) else True
                    
                    if writeNewDDS:
                        with open(ddsFile, "wb") as newdds:
                            ddscontent = textureZip.read(ddsFileInZip)
                            newdds.write(ddscontent)
                            print(f"create new {env} dds file: {ddsFile}")

    
    
                
        
        