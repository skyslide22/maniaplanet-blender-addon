from sys import path
import bpy
import os.path
import re
import subprocess
import shutil
from time import sleep
from threading import Thread
import xml.etree.ElementTree as ET
from xml.dom import minidom
from .MP_Functions import *
from random import randint


class CONVERT_ITEM(Thread):
    
    def __init__(self, fbxfilepath: str) -> None:
        super(CONVERT_ITEM, self).__init__() #need to call init from Thread, otherwise error
        self.fbxfilepath    = fixSlash( fbxfilepath ) 
        self.fbxfilepathREL = "Items/" + fbxfilepath.split("/Work/Items/")[-1] 
        self.convertIsDone  = False
        self.convertFailed  = False
        self.meshInfos = None #error or succes msg of mesh/shape.gbx
        self.itemInfos = None #error or succes msg of item.gbx
        self.itemRcode = 0 #0 good, 1 and above bad
        self.meshRcode = 0 #0 good, 1 and above bad
        self.name      = self.fbxfilepath.split("/")[-1]
        self.progress  = []
        
        self.meshparamsXMLFilepath  = self.fbxfilepath.replace(".fbx", ".MeshParams.xml")
        self.itemXMLFilepath        = self.fbxfilepath.replace(".fbx", ".Item.xml")
        self.itemXMLFilepathREL     = self.fbxfilepathREL.replace(".fbx", ".Item.xml")
        
        self.gbxfilepath         = self.fbxfilepath.replace("/Work/Items/", "/Items/")
        self.meshGBXFilepath     = self.gbxfilepath.replace(".fbx", ".Mesh.gbx")
        self.itemGBXFilepath     = self.gbxfilepath.replace(".fbx", ".Item.gbx")
        self.shapeGBXFilepath    = self.gbxfilepath.replace(".fbx", ".Shape.gbx")
        self.shapeGBXFilepathOLD = self.gbxfilepath.replace(".fbx", ".Shape.gbx.old")
        
        
    
    def run(self) -> None:
        """method called when method start() is called on an instance of this class"""        
        #first run
        if not self.convertFailed:    self.convertMeshAndShapeGBX()
        if not self.convertFailed:    self.hackShapeGBX(action="MAKE_OLD")
        
        #convert again but replace "BaseMaterial" with "Link" in meshparams.xml of each item
        if not self.convertFailed:    self.convertMeshAndShapeGBX()
        if not self.convertFailed:    self.hackShapeGBX(action="USE_OLD")
        
        #convert item.gbx
        if not self.convertFailed:    self.convertItemGBX()
    
        pro__print(f"convert done, succeed: {'Nope' if self.convertFailed else 'True'}, status: mesh={self.meshRcode} item={self.itemRcode}, obj: {self.name}")
        
        mp_props = bpy.context.scene.mp_props
        
        failure = False
        success = False
        
        if not  self.convertFailed: success = True    
        if      self.convertFailed: failure = True
        
        updateConvertStatusNumbers(success=success, failure=failure)
        
        
        # for step in self.progress:
        #     pro__print(step)

    

    def convertMeshAndShapeGBX(self) -> None:
        """convert fbx to shape/mesh.gbx"""
        self.progress.append("Start converting mesh/shape.gbx")
        
        cmd = f"{getNadeoImporterPath()} Mesh {self.fbxfilepathREL}" # ex: NadeoImporter.exe Mesh /Items/myblock.fbx
        convertProcess  = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        mesh_output     = convertProcess.communicate()  # is blocking, => blender not frozen cuz this func runs in a new thread
        mesh_returncode = convertProcess.returncode
        convertProcess.wait()
        
        self.meshInfos = str(mesh_output[0])
        self.meshRcode = mesh_returncode
        self.convertFailed = True if mesh_returncode > 0 else False

    
    
    def convertItemGBX(self) -> None:
        """convert fbx to item.gbx"""
        self.progress.append("Start converting item.gbx")
        
        cmd = f"{getNadeoImporterPath()} Item {self.itemXMLFilepathREL}" # ex: NadeoImporter.exe Mesh /Items/myblock.fbx
        convertProcess  = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        item_output     = convertProcess.communicate()  # is blocking, => blender not frozen cuz this func runs in a new thread
        item_returncode = convertProcess.returncode
        convertProcess.wait()

        self.itemInfos = str(item_output[0])
        self.itemRcode = item_returncode
        self.convertFailed = True if item_returncode > 0 else False
                

    
    
    def hackShapeGBX(self, action: str="MAKE_OLD" or "USE_OLD") -> None:
        """hack the shape.gbx of the given filename, call this function 2 times!
            --- 1st call: action='MAKE_OLD', this will rename the shape.gbx to shape.gbx.old
                and change meshParams.xml.
            --- 2nd call: action='USE_OLD',  replace shape.gbx with shape.gbx.old
        """
        validActions = ["MAKE_OLD", "USE_OLD"]
        if action not in validActions:
            raise ValueError("action value not in ", validActions)
        
        #create shape.gbx.old file, should be used in first call
        if action == "MAKE_OLD":
            
            self.progress.append("Start rename shape.gbx to shape.gbx.old")
            
            if doesFileExist(self.shapeGBXFilepathOLD):
                os.remove(self.shapeGBXFilepathOLD)
            
            try:
                os.rename(
                self.shapeGBXFilepath,
                self.shapeGBXFilepathOLD
                )
            except FileNotFoundError:
                pass
            
            
            self.progress.append("Start parsing item.xml")
            tree = ET.parse(self.meshparamsXMLFilepath)
            root = tree.getroot()
            data = root.findall(".Materials/Material")
            for mat in data:
                if mat.get("BaseTexture"):
                    if not "/" in mat.get("BaseTexture"):
                        mat.set("Link", mat.get("BaseTexture"))
                        del mat.attrib["BaseTexture"]
                        del mat.attrib["Model"]
                        del mat.attrib["PhysicsId"]
                        
            self.progress.append("Start writing changed xml to same file")
            tree.write(self.meshparamsXMLFilepath)

        
        #replace shape.gbx with shape.old.gbx
        if action == "USE_OLD":
            
            self.progress.append("Start replacing shape.gbx with shape.old.gbx")
        
            try:    os.remove(self.shapeGBXFilepath)
            except: pass #doesn't wotk sometimes, for some unknown reason..

            try:
                os.rename(
                    self.shapeGBXFilepathOLD,
                    self.shapeGBXFilepath
                )
            except FileNotFoundError:
                pass
        
        
        

def updateConvertStatusNumbers(success: int, failure: int) -> None:
    """updates the numbers for converting which are displaed in the ui panel"""
    mp_props = bpy.context.scene.mp_props
    
    try:
        if success: mp_props.NU_fbx_convertsSuccess += 1
        if failure: mp_props.NU_fbx_convertsFail    += 1
        mp_props.NU_fbx_convertedRaw += 1
    
    except AttributeError: #happens sometime, so try again (access object at the same time twice)
        updateConvertStatusNumbers(success=success, failure=failure)
        
        


def startBatchConvert(fbxfilepaths: list) -> None:
    """convert each fbx one after one, create a new thread for it"""
    mp_props = bpy.context.scene.mp_props
    results = []
    
    for fbx in fbxfilepaths:
        convertTheFBX = CONVERT_ITEM(fbxfilepath=fbx)
        convertTheFBX.start() #start the convert (call internal run())
        convertTheFBX.join()  #waits until the thread terminated (function/convert is done..)
        
        results.append({
            "name":         convertTheFBX.fbxfilepathREL,
            "meshRcode":    convertTheFBX.meshRcode,
            "itemRcode":    convertTheFBX.itemRcode,
            "itemInfos":    convertTheFBX.itemInfos,
            "meshInfos":    convertTheFBX.meshInfos,
        })
        
        pro__print("mesh:", convertTheFBX.meshInfos)
        pro__print("item:", convertTheFBX.itemInfos)
        
        if mp_props.CB_fbx_stopConvert is True:
            pro__print("convert stopped, aborted by user (UI CHECKBOX)")
            break
    
    writeConvertReport(results=results)
    



def writeConvertReport(results: list) -> None:
    """genertate status html file of converted fbx files"""
    errors      = 0
    converted   = len(results)
    
    for res in results:
        if res["meshRcode"] > 0 or res["itemRcode"] > 0:
            errors += 1
    
    with open(website_convertreport, "w", encoding="utf-8") as f:
        f.write(f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Document</title>
                <link rel="stylesheet" href="file://{getAddonPath()}assets/report.css"
            </head>
            <body>
                <header>
                    <div>
                        Failed converts: {errors} of {converted}
                    </div>
                </header>
                <ul id="result-list">
            """)
        
        for res in results:
            f.write(f"""
                <li class="{"error" if res["meshRcode"] > 0 or res["itemRcode"] > 0 else "success"}">
                    <ul class="result-object">
                        <li class="item"><b>Item:</b> {res["name"]}     </li>
                        <li class="mesh-error"><b>Mesh Errors:</b> {beautifyError(res["meshInfos"]) if res["meshRcode"] > 0 else ""} </li>
                        <li class="item-error"><b>Item Errors:</b> {beautifyError(res["itemInfos"]) if res["itemRcode"] > 0 else ""} </li>
                    </ul>    
                </li>
                """)
        
        f.write("""
                </ul>
            </body>
            </html>
            """)
        
        
        
def beautifyError(error: str):
    """proper description from nadeoimporter return string"""
    LMMissing       = "lightmap"
    BMMissing       = "basematerial"
    MatMissing      = "no material"
    noInfos         = ""
    missingUV       = "uvlayers"
    commonNotFound  = "common"
    itemXMLMissing  = "item.xml"       
    
    error = error.replace("(b'", "")
    error = error.replace("\\r",  "<br />")
    error = error.replace("\\n'", "<br />")
    error = error.replace("\\n",  "<br />")
    error = error.replace("\\",   "/")
    error = error.replace(", None)", "")
    
    # "(b'NadeoImporter 2019-10-09_22_51\\r\\nfile not found : skyslide_main1.Trigger.Shape.gbx\\r\\nwhile reading :user:\\\\Work\\\\Items\\\\skyslide_main1.Item.xml\\r\\n', None)(b'NadeoImporter 2019-10-09_22_51\\r\\nCreated :user:\\\\Items\\\\skyslide_main1.Mesh.gbx\\r\\nCreated :user:\\\\Items\\\\skyslide_main1.Shape.gbx\\r\\n', None)"
    
    prettymsg = ""
    if LMMissing        in error.lower(): prettymsg="Lightmap uv layer is missing"
    if BMMissing        in error.lower(): prettymsg="Basematerial uv layer is missing"
    if MatMissing       in error.lower(): prettymsg="No material found, use atleast 1"
    if LMMissing        in error.lower(): prettymsg="Not enough UvLayers, BaseMaterial/Lightmap missing?"
    if missingUV        in error.lower(): prettymsg="Not enough UvLayers, BaseMaterial/Lightmap/Decal missing?"
    if commonNotFound   in error.lower(): prettymsg="Collection COMMON not found, does meshParams.xml exist?"
    if itemXMLMissing   in error.lower(): prettymsg="Item.xml not found, does it exists?"
    if prettymsg == "":                   prettymsg=error 

    return prettymsg

        

    
# bpy.app.register(checkItemsToConvertStatus, first_interval=1)
    
    
    



















        
        
        
        